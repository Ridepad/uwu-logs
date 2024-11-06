from collections import defaultdict
from dataclasses import dataclass

from h_debug import running_time, Loggers
from h_other import sort_dict_by_value, separate_thousands
from logs_base import THE_LOGS

LOGGER = Loggers.reports

VALK_LIGHT = "Fjola Lightbane"
VALK_DARK  = "Eydis Darkbane"
CAST_DURATION = 15 + 1
TWIN_PACT_IDS = {
    "67303": VALK_DARK,  # 25
    "67304": VALK_DARK,  # 10 H
    "67305": VALK_DARK,  # 25H
    "65875": VALK_DARK,  # 10
    
    "67306": VALK_LIGHT, # 25
    "67307": VALK_LIGHT, # 10 H
    "67308": VALK_LIGHT, # 25H
    "65876": VALK_LIGHT, # 10
}

@dataclass
class ShieldCast:
    start_index: int = 0
    stop_index: int = 0
    shield_spell_id: str = "0"

    @property
    def valk_name(self):
        try:
            return TWIN_PACT_IDS[self.shield_spell_id]
        except KeyError:
            LOGGER.warning(f"{self.shield_spell_id:>5} | missing spell id")
            return "Unknown"


class ValksTOC(THE_LOGS):
    def parse_shields_casts_wrap(self, s, f):
        targets = []
        dmg_on_shield: list[defaultdict[str, int]] = []
        all_players: set[str] = set()
        for cast in self.parse_shields_casts(s, f):
            targets.append(cast.valk_name)

            logs_slice = self.LOGS[s+cast.start_index:s+cast.stop_index]
            abs_dmg = self.get_abs_dmg(logs_slice)
            dmg_on_shield.append(abs_dmg)
            all_players.update(abs_dmg)

        # sort by 1st shield
        all_players = sorted(all_players, key=lambda guid: dmg_on_shield[0][guid], reverse=True)
        player_dmg = defaultdict(list)
        for abs_dmg in dmg_on_shield:
            for guid in all_players:
                dmg = separate_thousands(abs_dmg[guid])
                player_dmg[guid].append(dmg)
        
        specs = self.get_slice_spec_info(s, f)
        return {
            "TARGETS": targets,
            "ATTEMPT_DATA": player_dmg,
            "SPECS": specs,
        }

    def parse_shields_casts(self, s: int, f: int):
        logs_slice = self.LOGS[s:f]
        for cast in self._gen_shields_casts(logs_slice):
            if not cast.start_index:
                continue
            
            if cast.stop_index:
                yield cast
                continue

            # calc stop 15 sec after cast
            cast_line = logs_slice[cast.start_index]
            sec_from_start = self.get_timedelta_seconds(self.LOGS[0], cast_line)
            after_cast = self.TIMESTAMPS[int(sec_from_start + CAST_DURATION)]
            after_cast = min(f, after_cast)
            cast.stop_index = after_cast - s
            yield cast

    def _gen_shields_casts(self, slice: list[str]):
        current_shield_spell_id_filter = None
        cast = ShieldCast()
        for i, line in enumerate(slice):
            if not current_shield_spell_id_filter:
                spell_id = line.rsplit(',', 3)[1]
                if spell_id not in TWIN_PACT_IDS:
                    continue
                
                current_shield_spell_id_filter = f",{spell_id},"
                yield cast

                cast = ShieldCast(
                    start_index=i,
                    shield_spell_id=spell_id,
                )
                continue

            if current_shield_spell_id_filter in line:
                current_shield_spell_id_filter = None
                cast.stop_index = i

        yield cast

    @running_time
    def get_abs_dmg(self, logs_slice: list[str]):
        d = defaultdict(int)
        for line in logs_slice:
            _, flag, source_guid, etc = line.split(",", 3)
            d[source_guid] += 0
            if "_MISS" not in flag:
                continue
            absorb_value = etc.rsplit(",", 1)[1]
            try:
                d[source_guid] += int(absorb_value)
            except ValueError:
                pass
        return self.combine_pets(d, trim_non_players=True)
    
    def _pretty_print_damage(self, damage: dict[str, int]):
        for guid, v in sort_dict_by_value(damage).items():
            name = self.guid_to_name(guid)
            print(f"{name:12} | {v:>11,}")



def test1():
    report = ValksTOC("24-09-06--20-54--Meownya--Lordaeron")
    report.ALL_GUIDS
    report.ENCOUNTER_DATA
    report.LOGS
    s,f = report.ENCOUNTER_DATA["Twin Val'kyr"][-1]
    q = report.parse_shields_casts(s, f)
    for zz in q:
        print(zz.valk_name)
        logs_slice_v = report.LOGS[s+zz.start_index:s+zz.stop_index]
        abs_dmg = report.get_abs_dmg(logs_slice_v)
        report._pretty_print_damage(abs_dmg)


if __name__ == "__main__":
    test1()
