from collections import defaultdict
from dataclasses import dataclass

import logs_base
from c_bosses import (
    BOSSES_GUIDS,
    COWARDS,
    ENCOUNTER_MIN_DURATION,
)
from h_other import convert_to_html_name

CSS_BOSS_LINK = "boss-link"
DEFAULT_DIFFICULTY = "TBD"
DIFFICULTY = ('10N', '10H', '25N', '25H')
COWARDS_NAMES = set(COWARDS.values())
YOGG_SARON_GUARDIAN_BUFFS = {
    "62670": "Resilience of Nature",
    "62650": "Fortitude of Frost",
    "62702": "Fury of the Storm",
    "62671": "Speed of Invention",
}
SPELLS: dict[str, tuple[str]] = {
    "Lord Marrowgar":
        ("69146", "70824", "70823", "70825"), # Coldflame
    "Lady Deathwhisper":
        ("71254", "72503", "72008", "72504"), # Shadow Bolt
    "Lady Deathwhisper2":
        ("71001", "72109", "72108", "72110"), # Death and Decay
    "Gunship":
        ("70162", "72567", "72566", "72568"), # Shoot
    "Gunship2":
        ("70161", "72540", "72539", "72541"), # Hurl Axe
    "Deathbringer Saurfang":
        ("72380", "72439", "72438", "72440"), # Blood Nova
    "Deathbringer Saurfang2":
        ("72385", "72442", "72441", "72443"), # Boiling Blood
    "Festergut":
        ("72219", "72552", "72551", "72553"), # Gastric Bloat
    "Rotface":
        ("69674", "73022", "71224", "73023"), # Mutated Infection
    "Professor Putricide":
        ("70402", "72512", "72511", "72513"), # Mutated Transformation
    "Professor Putricide2":
        ("70351", "71967", "71966", "71968"), # Unstable Experiment
    "Blood Prince Council":
        ("71405", "72805", "72804", "72806"), # Shadow Lance
    "Blood-Queen Lana'thel":
        ("70985", "71699", "71698", "71700"), # Shroud of Sorrow
    "Valithria Dreamwalker":
        ("70759", "72015", "71889", "72016"), # Frostbolt Volley
    "Sindragosa":
        ("70084", "71051", "71050", "71052"), # Frost Aura
    "The Lich King":
        ("70541", "73780", "73779", "73781"), # Infest

    "Saviana Ragefire":
        ("74403", "", "74404", ""), # Flame Breath
    "General Zarithrian":
        ("74394", "", "74395", ""), # Lava Gout
    "Halion":
        ("74525", "74527", "74526", "74528"), # Flame Breath

    "Northrend Beasts":
        ("66331", "67478", "67477", "67479"), # Impale
    "Lord Jaraxxus":
        ("66532", "66964", "66963", "66965"), # Fel Fireball
    "Faction Champions":
        ("65546", "68625", "68624", "68626"), # Dispel Magic
    "Faction Champions2":
        ("65973", "68101", "68100", "68102"), # Earth Shock
    "Faction Champions22":
        ("65868", "67989", "67988", "67990"), # Shoot
    "Faction Champions222":
        ("65821", "68152", "68151", "68153"), # Shadow Bolt
    "Faction Champions2222":
        ("65807", "68004", "68003", "68005"), # Frostbolt
    "Faction Champions22222":
        ("66047", "67936", "67935", "67937"), # Frost Strike
    "Faction Champions222222":
        ("66178", "68760", "68759", "68761"), # Shadowstep
    "Faction Champions2222222":
        ("66100", "68027", "68026", "68028"), # Mana Burn
    "Faction Champions2222222":
        ("65955", "68098", "68097", "68099"), # Fan of Knives
    "Twin Val'kyr":
        ("65767", "67275", "67274", "67276"), # Light Surge
    "Anub'arak":
        ("66013", "68509", "67700", "68510"), # Penetrating Cold

    # "Onyxia":
    #     ("18435", "", "68970", ""), # Flame Breath
    "Malygos":
        ("61693", "", "61694", ""), # Arcane Storm
    "Sartharion":
        ("56908", "", "58956", ""), # Flame Breath

    "Toravon the Ice Watcher":
        ("72082", "", "72097", ""), # Frozen Orb
    "Koralon the Flame Watcher":
        ("66670", "", "67329", ""), # Burning Breath
    "Archavon the Stone Watcher":
        ("58696", "", "60884", ""), # Rock Shards
    "Archavon the Stone Watcher2":
        ("58695", "", "60883", ""), # Rock Shards
    "Emalon the Storm Watcher":
        ("64213", "", "64215", ""), # Chain Lightning

    "XT-002 Deconstructor":
        ("", "64227", "", "64236"), # Life Spark / Static Charged
    "Assembly of Iron":
        ("", "64637", "", "61888"), # Overwhelming Power
    "Thorim":
        ("", " 62597", "", "62605"), # Frost Nova
    "Thorim2":
        ("", " 62583", "", "62601"), # Frostbolt
    "Thorim22":
        ("", " 62580", "", "62604"), # Frostbolt Volley
    "Freya_Stonebark":
        ("", "62437", "", "62859"), # Ground Tremor
    "Freya_Ironbranch":
        ("", "62861", "", "62438"), # Iron Roots
    "Freya_Brightleaf":
        ("", "62451", "", "62865"), # Sun Beam / Unstable Energy
    "Mimiron25N":
        ("", "", "", "64582"), # Emergency Mode
    "Mimiron10N":
        ("", "64582", "", ""), # Emergency Mode
    "General Vezax25N":
        ("", "", "", "63420"), # Saronite Animus / Profound Darkness
    "General Vezax10N":
        ("", "63420", "", ""), # Saronite Animus / Profound Darkness
}
NOT_DETECTED_NORMAL_MODE = {
    "Thorim",
    "XT-002 Deconstructor",
    "Assembly of Iron",
    "Mimiron",
    "General Vezax",
}

def imagine_playing_shit_expansion(logs_slice: list[str]):
    players = set()
    
    def more_than_10_players():
        max_players = 10
        if "0x0000000000000000" in players:
            max_players = 11
        
        return len(players) > max_players

    for line in logs_slice[:2000]:
        _, flag, guid, _ = line.split(',', 3)
        if guid[:3] != '0x0':
            continue
        if guid in players:
            continue
        if flag == 'SPELL_AURA_REMOVED':
            continue
        if flag == 'SPELL_AURA_REFRESH':
            continue

        players.add(guid)
        if more_than_10_players():
            return DIFFICULTY[2]
    
    return DIFFICULTY[0]

def freya_diff(logs_slice: list[str]):
    elder_boss_ids = {
        "Freya_Stonebark",
        "Freya_Ironbranch",
        "Freya_Brightleaf",
    }
    
    for boss_id in elder_boss_ids:
        diff = get_difficulty(logs_slice, boss_id)
        if diff == DEFAULT_DIFFICULTY:
            return None
        
    return diff

def yogg_hm(logs_slice: list[str], default: str=DEFAULT_DIFFICULTY):
    buffs = set()
    for line in logs_slice[:2000]:
        if ",62" not in line:
            continue
        try:
            spell_id = line.split(',', 7)[6]
            if spell_id in YOGG_SARON_GUARDIAN_BUFFS:
                buffs.add(spell_id)
            if len(buffs) > 1:
                return default
        except Exception:
            pass
    
    if default == "25N":
        return "25H"
    return "10H"

def _get_difficulty(logs_slice: list[str], boss_name: str) -> str:
    spell_ids = SPELLS[boss_name]
    for line in logs_slice:
        try:
            spell_id = line.split(',', 7)[6]
            if spell_id in spell_ids:
                return DIFFICULTY[spell_ids.index(spell_id)]
        except Exception:
            pass
    boss_ver_2 = f"{boss_name}2"
    if boss_ver_2 in SPELLS:
        return _get_difficulty(logs_slice, boss_ver_2)
    return DEFAULT_DIFFICULTY

def get_difficulty(logs_slice: list[str], boss_name: str) -> str:
    if boss_name not in SPELLS:
        difficulty = imagine_playing_shit_expansion(logs_slice)
        
        if boss_name == "Freya":
            return freya_diff(logs_slice) or difficulty
        
        if boss_name == "Yogg-Saron":
            return yogg_hm(logs_slice, difficulty) 
        
        boss_name = f"{boss_name}{difficulty}"
        if boss_name not in SPELLS:
            return difficulty
        
    difficulty = _get_difficulty(logs_slice, boss_name)
    if difficulty == DEFAULT_DIFFICULTY and boss_name in NOT_DETECTED_NORMAL_MODE:
        return imagine_playing_shit_expansion(logs_slice)
    return difficulty

def is_overkill_on_boss(line: list[str]):
    if line[10] == "0":
        return
    if line[4][6:-6] not in BOSSES_GUIDS:
        return
    return int(line[9]) - int(line[10]) != 1

def is_kill(last_line: str):
    line = last_line.split(',', 11)
    if line[1] == "UNIT_DIED":
        return line[4][6:-6] in BOSSES_GUIDS
    try:
        return line[6] == "72350" or is_overkill_on_boss(line)
    except IndexError:
        return False

def has_fury_of_frostmourne(logs_slice: list[str]):
    return any(
        '72350' in line
        and '008EF5' in line
        and 'SPELL' in line
        and '_CAST' not in line
        for line in logs_slice
    )

def many_auras_removed(logs_slice: list[str], threshold: int=20):
    removed = 0
    for line in logs_slice:
        line = line.split(',', 5)
        if line[1] != "SPELL_AURA_REMOVED":
            continue
        if line[4][6:-6] in COWARDS:
            removed += 1
    return removed > threshold


@dataclass
class LogsSegment:
    encounter_name: str
    start: int
    end: int
    t_start: int
    t_end: int
    difficulty: str
    attempt: int
    attempt_from_last_kill: int
    attempt_type: str
    duration: int
    duration_str: str

    def __getitem__(self, key):
        return getattr(self, key)

    @property
    def diff(self):
        return self.difficulty

    @property
    def segment_type(self):
        if self.attempt_type == "kill":
            return "Kill"
        return f"Wipe {self.attempt_from_last_kill}"

    @property
    def encounter_name_html(self):
        return convert_to_html_name(self.encounter_name)

    @property
    def segment_str(self):
        return f"{self.duration_str} | {self.segment_type}"

    @property
    def segment_diff_type(self):
        return f"{self.difficulty} {self.segment_type}"

    @property
    def segment_full_str(self):
        return f"{self.duration_str} | {self.difficulty} | {self.encounter_name}"

    @property
    def href_boss(self):
        # ?boss=baltharus-the-warborn
        return f"?boss={self.encounter_name_html}"

    @property
    def href_boss_mode(self):
        # ?boss=baltharus-the-warborn&mode=25N
        return '&'.join((
            f"?boss={self.encounter_name_html}",
            f"mode={self.difficulty}",
        ))

    @property
    def href(self):
        # ?boss=baltharus-the-warborn&mode=25N&attempt=0&s=268&f=340
        return '&'.join((
            f"?boss={self.encounter_name_html}",
            f"mode={self.difficulty}",
            f"attempt={self.attempt}",
            f"s={self.t_start}",
            f"f={self.t_end}",
        ))

    @property
    def css_class(self):
        return f"{self.attempt_type}-link"

    def is_kill(self):
        return self.attempt_type == "kill" and self.difficulty != "TBD"


class BossModesSegments(list[LogsSegment]):
    css_class = CSS_BOSS_LINK

    @property
    def href(self):
        return self[0].href_boss_mode

    @property
    def text(self):
        s = self[0]
        return f"{s.difficulty} {s.encounter_name}"


class BossSegments:
    css_class = CSS_BOSS_LINK

    def __init__(self, boss_name: str, segments: list[LogsSegment]):
        self.boss_name = boss_name
        self.segments = segments

        if boss_name == "all":
            self.href = "?boss=all"
            self.text = f"All boss segments"
        else:
            self.href = segments[0].href_boss
            # self.text = boss_name
            self.text = f"All {boss_name} segments"

    @property
    def by_difficulty(self):
        try:
            return self._children
        except AttributeError:
            pass

        d = defaultdict(BossModesSegments)
        for segment in self.segments:
            d[segment.difficulty].append(segment)
        self._children = d
        return self._children


class LogsSegments(logs_base.THE_LOGS):
    @property
    def SEGMENTS(self):
        try:
            return self.__SEGMENTS
        except AttributeError:
            self.__SEGMENTS = self.get_segments()
            return self.__SEGMENTS

    @property
    def SEGMENTS_QUERIES(self):
        try:
            return self._SEGMENTS_QUERIES
        except AttributeError:
            segm_links = [
                BossSegments(boss_name, segments)
                for boss_name, segments in self.SEGMENTS.items()
            ]
            segm_links.insert(0, BossSegments("all", []))
            self._SEGMENTS_QUERIES = segm_links
            return segm_links

    @property
    def SEGMENTS_KILLS(self):
        try:
            return self._SEGMENTS_KILLS
        except AttributeError:
            self._SEGMENTS_KILLS = [
                segment
                for segments in self.SEGMENTS.values()
                for segment in segments
                if segment.is_kill()
            ]
            return self._SEGMENTS_KILLS

    def get_latest_kill(self, boss_name: str, difficulty: str):
        boss_data = self.SEGMENTS[boss_name]
        for segment in reversed(boss_data):
            if not segment.is_kill():
                continue
            if not difficulty or segment.difficulty == difficulty:
                return segment

    def gen_kill_segments(self):
        for boss_name, boss_segments in self.SEGMENTS.items():
            for segment in boss_segments:
                if segment.is_kill():
                    yield boss_name, segment

    def get_segments(self):
        segments_data: dict[str, list[LogsSegment]] = {}
        for boss_name, segments in self.ENCOUNTER_DATA.items():
            boss_data = []
            shift = 0
            for attempt, (s, f) in enumerate(segments):
                segment_data = self.format_attempt(s, f, boss_name, attempt, shift)
                if segment_data.is_kill():
                    shift = attempt+1
                boss_data.append(segment_data)
            segments_data[boss_name] = boss_data

        return segments_data

    def format_attempt(self, s: int, f: int, boss_name: str, attempt: int, shift: int):
        logs_slice = self.LOGS[s:f]
        diff = get_difficulty(logs_slice, boss_name)

        slice_duration = self.get_slice_duration(s, f)
        slice_duration_str = self.duration_to_string(slice_duration)
        slice_duration_str = slice_duration_str[2:]

        kill = self.is_kill(s, f, boss_name)
        attempt_type = "kill" if kill else "wipe"
        return LogsSegment(
            encounter_name=boss_name,
            start=s,
            end=f,
            t_start=self.find_index(s, shift=-1),
            t_end=self.find_index(f, slice_end=True),
            difficulty=diff,
            attempt=attempt,
            attempt_from_last_kill=attempt-shift+1,
            attempt_type=attempt_type,
            duration=slice_duration,
            duration_str=slice_duration_str,
        )

    def is_kill(self, s: int, f: int, boss_name: str):
        slice_duration = self.get_slice_duration(s, f)
        if slice_duration < ENCOUNTER_MIN_DURATION.get(boss_name, 15):
            return False

        if is_kill(self.LOGS[f-1]):
            return True

        if boss_name == "The Lich King":
            return has_fury_of_frostmourne(self.LOGS[f-10:f+20])

        if boss_name in COWARDS_NAMES:
            _slice = self.LOGS[f-100:f]
            threshold = 20
            return many_auras_removed(_slice, threshold)

        return False


def main():
    report = LogsSegments("24-06-15--20-00--Xeel--Whitemane-Frostmourne")
    print(report.SEGMENTS)

if __name__ == "__main__":
    main()
