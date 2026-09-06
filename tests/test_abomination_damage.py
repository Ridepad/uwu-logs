"""Regression tests for separate owner and Mutated Abomination report rows.

Run from the repository root with:
    python -m unittest discover -s tests -p test_abomination_damage.py -v

The report fixture starts at normalized logs and accepted encounter metadata.
It uses the real request, parsing, aggregation, duration and table code, without
report files, raw-log encounter detection, spec detection or absorb events.
"""

from copy import deepcopy
import unittest

from logs_check_difficulty import LogsSegment
from logs_dmg_heals import add_pets
from logs_main import QuerySegment, THE_LOGS


OWNER = "0x0000000000000001"
SECOND_OWNER = "0x0000000000000002"
PET = "0xF140000001000001"
ABOM = "0xF13000958D000001"
SECOND_ABOM = "0xF13000958D000002"
OTHER_OWNER_ABOM = "0xF13000958D000003"
BOSS = "0xF130008F46000001"
MARROWGAR = "0xF130008F04000001"
GUIDS = {
    OWNER: {"name": "Player"},
    SECOND_OWNER: {"name": "Second"},
    PET: {"name": "Pet", "master_guid": OWNER},
    ABOM: {"name": "Mutated Abomination", "master_guid": OWNER},
    SECOND_ABOM: {"name": "Mutated Abomination", "master_guid": OWNER},
    OTHER_OWNER_ABOM: {"name": "Mutated Abomination", "master_guid": SECOND_OWNER},
    BOSS: {"name": "Professor Putricide"},
    MARROWGAR: {"name": "Lord Marrowgar"},
}


def event(second, source, target, amount, flag="SPELL_DAMAGE", overheal=0):
    """Produce the normalized CSV shape consumed by parse_both."""
    minute, second = divmod(second, 60)
    return (
        f'9/6 12:{minute:02}:{second:02}.000,{flag},'
        f'{source},"{GUIDS[source]["name"]}",'
        f'{target},"{GUIDS[target]["name"]}",'
        f'1,"Fixture Spell",1,{amount},{overheal},0'
    )


class MemoryReport(THE_LOGS):
    def __init__(self):
        super().__init__("26-09-06_fixture", copy_from_backup=False)
        self._guids_all = deepcopy(GUIDS)
        self._guids_players = {OWNER: "Player", SECOND_OWNER: "Second"}
        self._guids_classes = {}
        self.lines = []
        self.encounters = {}
        self.accepted_segments = {}

        # Two Marrowgar attempts and one Putricide kill, each ten seconds.
        for start, multiplier in ((0, 1), (30, 2)):
            self.add_attempt("Lord Marrowgar", start, [
                event(start, OWNER, MARROWGAR, 1000 * multiplier),
                event(start + 2, PET, MARROWGAR, 100 * multiplier),
                event(start + 4, OWNER, OWNER, 100 * (multiplier + 1),
                      "SPELL_HEAL", 50 * multiplier),
                event(start + 8, MARROWGAR, OWNER, 100 * multiplier),
                event(start + 10, MARROWGAR, PET, 20 * multiplier),
            ], "wipe" if multiplier == 1 else "kill")
            if multiplier == 1:
                # Not part of either boss attempt; All Bosses must exclude it.
                self.lines.append(event(20, OWNER, BOSS, 50000))

        self.add_attempt("Professor Putricide", 60, [
            event(60, OWNER, BOSS, 300),
            event(61, PET, BOSS, 30),
            event(62, ABOM, BOSS, 500),
            event(63, OWNER, OWNER, 400, "SPELL_HEAL", 150),
            event(64, ABOM, OWNER, 200, "SPELL_HEAL", 50),
            event(66, BOSS, OWNER, 300),
            event(68, BOSS, PET, 60),
            event(70, BOSS, ABOM, 100),
        ], "kill")

    def add_attempt(self, boss, start, lines, result):
        first = len(self.lines)
        self.lines.extend(lines)
        last = len(self.lines)
        attempts = self.encounters.setdefault(boss, [])
        attempt = len(attempts)
        attempts.append([first, last])
        self.accepted_segments.setdefault(boss, []).append(LogsSegment(
            encounter_name=boss, start=first, end=last, t_start=start,
            t_end=start + 10, difficulty="25H", attempt=attempt,
            attempt_from_last_kill=attempt + 1, attempt_type=result,
            duration=10, duration_str="0:00:10.000",
        ))

    @property
    def LOGS(self):
        return self.lines

    @property
    def ENCOUNTER_DATA(self):
        return self.encounters

    @property
    def SEGMENTS(self):
        return self.accepted_segments

    def get_players_specs_in_segments(self, s, f):
        return {}

    def get_absorbs_by_source(self, s, f):
        return {}


class AddPetsTests(unittest.TestCase):
    def assert_rows(self, data, expected):
        guids = deepcopy(GUIDS)
        original_data, original_guids = deepcopy(data), deepcopy(guids)
        rows = add_pets(data, guids)
        self.assertEqual(rows, expected)
        self.assertEqual(data, original_data)
        self.assertEqual(guids, original_guids)
        return rows

    def test_owner_ordinary_pet_and_abomination_are_counted_once(self):
        data = {OWNER: 1000, PET: 200, ABOM: 500}
        rows = self.assert_rows(data, {"Player": 1200, "Player-A": 500})
        self.assertEqual(sum(rows.values()), sum(data.values()))

    def test_multiple_abominations_are_combined_per_owner(self):
        data = {OWNER: 1000, SECOND_OWNER: 2000, ABOM: 300,
                SECOND_ABOM: 200, OTHER_OWNER_ABOM: 700}
        rows = self.assert_rows(data, {
            "Player": 1000, "Second": 2000, "Player-A": 500, "Second-A": 700,
        })
        self.assertEqual(sum(rows.values()), sum(data.values()))

    def test_owner_only_pet_only_and_abomination_only(self):
        cases = (
            ({OWNER: 1000}, {"Player": 1000}),
            ({PET: 200}, {"Player": 200}),
            ({OWNER: 1000, PET: 200}, {"Player": 1200}),
            ({ABOM: 500}, {"Player-A": 500}),
        )
        for data, expected in cases:
            with self.subTest(data=data):
                rows = self.assert_rows(data, expected)
                self.assertEqual(sum(rows.values()), sum(data.values()))

    def test_empty_and_zero_abomination_contributions(self):
        for data, expected in (
            ({}, {}),
            ({OWNER: 0, ABOM: 0}, {"Player": 0, "Player-A": 0}),
            ({OWNER: 1000, ABOM: 0}, {"Player": 1000, "Player-A": 0}),
        ):
            with self.subTest(data=data):
                self.assert_rows(data, expected)

    def test_non_player_damage_is_still_excluded(self):
        self.assert_rows({OWNER: 1000, ABOM: 500, BOSS: 9000},
                         {"Player": 1000, "Player-A": 500})


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.report = MemoryReport()

    def render(self, query):
        parsed = self.report.parse_request(query)
        result = self.report.get_report_page_all_wrap(parsed["SEGMENTS"], query.boss)
        self.assertEqual(result["SPECS"]["Player-A"],
                         ("Mutated Abomination", "ability_rogue_deviouspoisons"))
        return parsed, result["DATA"]

    def assert_table(self, table, expected):
        # Literal expected values, rates and bar scales include Total's special 0.
        self.assertEqual(table, {
            name: {"value": value, "per_second": rate, "percent": percent}
            for name, (value, rate, percent) in expected.items()
        })

    def test_all_bosses_does_not_copy_other_attempts_into_abomination(self):
        parsed, data = self.render(QuerySegment(boss="all"))
        self.assertEqual((parsed["SLICE_NAME"], parsed["SLICE_TRIES"]),
                         ("Bosses", "All"))
        self.assertEqual(len(parsed["SEGMENTS"]), 3)
        self.assertEqual(len(self.report.SEGMENTS["Professor Putricide"]), 1)
        self.assertEqual(self.report.get_fight_duration_total(parsed["SEGMENTS"]), 30)
        self.assert_table(data["damage"], {
            "Player": ("3 630", "121.0", 100),
            "Player-A": ("500", "16.6", 13),
            "Total": ("4 130", "137.6", 0),
        })
        self.assert_table(data["heal"], {
            "Player": ("600", "20.0", 100),
            "Player-A": ("150", "5.0", 25),
            "Total": ("750", "25.0", 0),
        })
        self.assert_table(data["taken"], {
            "Player": ("720", "24.0", 100),
            "Player-A": ("100", "3.3", 13),
            "Total": ("820", "27.3", 0),
        })
        # The current boss-only report does not expose heal_total.
        self.assertNotIn("heal_total", data)

    def test_single_putricide_attempt_keeps_separate_rows_in_each_column(self):
        parsed, data = self.render(QuerySegment(boss="professor-putricide", attempt="0"))
        self.assertEqual(parsed["SLICE_TRIES"], "25H Kill")
        self.assertEqual(self.report.get_fight_duration_total(parsed["SEGMENTS"]), 10)
        self.assert_table(data["useful"], {
            "Player": ("330", "33.0", 100), "Total": ("330", "33.0", 0),
        })
        for column, expected in {
            "damage": {"Player": ("330", "33.0", 66),
                       "Player-A": ("500", "50.0", 100), "Total": ("830", "83.0", 0)},
            "heal": {"Player": ("250", "25.0", 100),
                     "Player-A": ("150", "15.0", 60), "Total": ("400", "40.0", 0)},
            "taken": {"Player": ("360", "36.0", 100),
                      "Player-A": ("100", "10.0", 27), "Total": ("460", "46.0", 0)},
            "heal_total": {"Player": ("400", "40.0", 100),
                           "Player-A": ("200", "20.0", 50), "Total": ("600", "60.0", 0)},
        }.items():
            with self.subTest(column=column):
                self.assert_table(data[column], expected)

    def test_custom_full_log_slice_includes_intermission_only_once(self):
        parsed, data = self.render(QuerySegment())
        self.assertEqual(parsed["SLICE_NAME"], "Custom Slice")
        self.assertEqual(self.report.get_fight_duration_total(parsed["SEGMENTS"]), 70)
        self.assert_table(data["damage"], {
            "Player": ("53 630", "766.1", 100),
            "Player-A": ("500", "7.1", 0),
            "Total": ("54 130", "773.2", 0),
        })
        self.assert_table(data["heal_total"], {
            "Player": ("900", "12.8", 100),
            "Player-A": ("200", "2.8", 22),
            "Total": ("1 100", "15.7", 0),
        })

    def test_empty_and_zero_table_values_keep_existing_formatting(self):
        self.assertEqual(self.report.convert_to_table_data({}, 0), {})
        self.assert_table(self.report.convert_to_table_data({OWNER: 0, ABOM: 0}, 0), {
            "Player": ("", "", 0), "Player-A": ("", "", 0), "Total": ("", "", 0),
        })


if __name__ == "__main__":
    unittest.main()
