from constants import BOSSES_GUIDS, convert_duration, get_fight_duration

DIFFICULTY = ('10N', '10H', '25N', '25H')
DEFAULT_DIFFICULTY = "TBD"
SPELLS: dict[str, tuple[str, tuple[str]]] = {
    "Lord Marrowgar": ("69146", "70824", "70823", "70825"), # Coldflame
    # "Lord Marrowgar": ("Bone Spike Graveyard", ("69057", "72088", "70826", "72089")),
    "Lady Deathwhisper": ("71254", "72503", "72008", "72504"), # Shadow Bolt
    "Gunship": ("70162", "72567", "72566", "72568"), # Shoot
    "Gunship2": ("70161", "72540", "72539", "72541"), # Hurl Axe
    "Deathbringer Saurfang": ("72409", "72448", "72447", "72449"), # Rune of Blood
    "Festergut": ("72219", "72552", "72551", "72553"), # Gastric Bloat
    "Rotface": ("69674", "73022", "71224", "73023"), # Mutated Infection
    "Professor Putricide": ("70402", "72512", "72511", "72513"), # Mutated Transformation
    "Professor Putricide2": ("70351", "71967", "71966", "71968"), # Unstable Experiment
    "Blood Prince Council": ("71405", "72805", "72804", "72806"), # Shadow Lance
    # "Blood Prince Council": ("Empowered Shock Vortex", ("72039", "73038", "73037", "73039")),
    "Blood-Queen Lana'thel": ("70985", "71699", "71698", "71700"), # Shroud of Sorrow
    "Valithria Dreamwalker": ("70759", "72015", "71889", "72016"), # Frostbolt Volley
    "Sindragosa": ("70084", "71051", "71050", "71052"), # Frost Aura
    "The Lich King": ("70541", "73780", "73779", "73781"), # Infest

    "Saviana Ragefire": ("74403", "", "74404", ""), # Flame Breath
    "General Zarithrian": ("74394", "", "74395", ""), # Lava Gout
    "Halion": ("74525", "74527", "74526", "74528"), # Flame Breath

    "Northrend Beasts": ("66331", "67478", "67477", "67479"), # Impale
    "Lord Jaraxxus": ("66532", "66964", "66963", "66965"), # Fel Fireball
    "Faction Champions": ("65546", "68625", "68624", "68626"), # Dispel Magic
    "Faction Champions2": ("65973", "68101", "68100", "68102"), # Earth Shock
    "Faction Champions22": ("65868", "67989", "67988", "67990"), # Shoot
    # "Faction Champions": ("Frostbolt", ("65807", "68004", "68003", "68005")),
    # "Faction Champions": ("Frost Strike", ("66047", "67936", "67935", "67937")),
    # "Faction Champions": ("Shadowstep", ("66178", "68760", "68759", "68761")),
    # "Faction Champions2": ("Mana Burn", ("66100", "68027", "68026", "68028")),
    # "Faction Champions": ("Fan of Knives", ("65955", "68098", "68097", "68099")),
    # "Faction Champions2": ("Shadow Bolt", ("65821", "68152", "68151", "68153")),
    "Twin Val'kyr": ("65767", "67275", "67274", "67276"), # Light Surge
    "Anub'arak": ("66013", "68509", "67700", "68510"), # Penetrating Cold

    "Onyxia": ("18435", "", "68970", ""), # Flame Breath
    "Malygos": ("61693", "", "61694", ""), # Arcane Storm
    "Sartharion": ("56908", "", "58956", ""), # Flame Breath

    "Toravon the Ice Watcher": ("72082", "", "72097", ""), # Frozen Orb
    "Koralon the Flame Watcher": ("66670", "", "67329", ""), # Burning Breath
    "Archavon the Stone Watcher": ("58696", "", "60884", ""), # Rock Shards
    "Emalon the Storm Watcher": ("64213", "", "64215", ""), # Chain Lightning
}

def imagine_playing_shit_expansion(logs_slice):
    players = set()
    for line in logs_slice[:2000]:
        if "SPELL_DAMAGE" not in line:
            continue
        sGUID = line.split(',', 3)[2]
        if sGUID[:3] == '0x0':
            players.add(sGUID)
            if len(players) > 10:
                return DIFFICULTY[2]
    return DIFFICULTY[0]

def get_diff(logs_slice: list[str], boss_name: str) -> str:
    if boss_name not in SPELLS:
        return imagine_playing_shit_expansion(logs_slice)
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
        return get_diff(logs_slice, boss_ver_2)
    return DEFAULT_DIFFICULTY

def is_kill(last_line: str):
    if 'UNIT_DIED' in last_line:
        return True
    # if "008FB5" in last_line or "00915F" in last_line or "0092A4" in last_line:
        # return last_line.split(',')[10] != '0'
    # return False
    try:
        line = last_line.split(',', 11)
        return line[10] != '0' and line[4][6:-6] in BOSSES_GUIDS
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

def get_slice_duration(logs_slice):
    s, f = logs_slice[0], logs_slice[-1]
    return get_fight_duration(s, f)

def convert_to_html_name(name: str):
    return name.lower().replace(' ', '-').replace("'", '')

def format_attempt(logs: list[str], segment: tuple[int, int], boss_name: str, attempt: int, shift: int):
    s, f = segment
    
    logs_slice = logs[s:f]
    diff = get_diff(logs_slice, boss_name)
    
    slice_duration = get_slice_duration(logs_slice)
    slice_duration_str = convert_duration(slice_duration)
    slice_duration_str = slice_duration_str[2:]

    kill = is_kill(logs_slice[-1])
    if not kill and boss_name == "The Lich King":
        kill = has_fury_of_frostmourne(logs[f-10:f+20])
    
    if kill:
        attempt_type = "kill"
        segment_type = "Kill"
        # segment_str = f"{slice_duration[2:]} | {diff} {boss_name}"
    else:
        attempt_type = "wipe"
        segment_type = f"Wipe {attempt-shift+1}"
        # segment_str = f"{slice_duration[2:]} | {diff} {boss_name} | Try {attempt-shift+1}"
    
    return {
        "start": s,
        "end": f,
        "diff": diff,
        "attempt": attempt,
        "attempt_type": attempt_type,
        "segment_type": segment_type,
        "duration": slice_duration,
        "duration_str": slice_duration_str,
    }



def get_segments(logs, enc_data: dict[str, list[tuple[int, int]]]):
    new_data = {}
    boss_to_html = {}
    for boss_name, segments in enc_data.items():
        boss_html = convert_to_html_name(boss_name)
        boss_to_html[boss_name] = boss_html

        boss_data = []
        shift = 0
        for attempt, segment in enumerate(segments):
            segment_data = format_attempt(logs, segment, boss_name, attempt, shift)
            if segment_data["attempt_type"] == "kill":
                shift = attempt+1
            boss_data.append(segment_data)
        new_data[boss_name] = boss_data
    
    return {
        "segments": new_data,
        "boss_html": boss_to_html,
    }

def separate_modes(data):
    separated: dict[str, dict[str, list[list]]] = {}
    for boss_name, segments in data.items():
        new_segments: dict[str, list[list]] = {}
        for segment in segments:
            diff = segment['diff']
            new_segments.setdefault(diff, []).append(segment)
        separated[boss_name] = new_segments
    return separated
