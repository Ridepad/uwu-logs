from constants import BOSSES_GUIDS, duration_to_string, get_delta_simple_precise

DEFAULT_DIFFICULTY = "TBD"
DIFFICULTY = ('10N', '10H', '25N', '25H')
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
}
COWARDS = {
    "0080A2": "Kologarn",
    "00804D": "Hodir",
    "008061": "Thorim",
    "00808A": "Freya",
    "008067": "Algalon the Observer",
}
COWARDS_NAMES = set(COWARDS.values())

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

        players.add(guid)
        if more_than_10_players():
            return DIFFICULTY[2]
    
    return DIFFICULTY[0]

def get_difficulty(logs_slice: list[str], boss_name: str) -> str:
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
        return get_difficulty(logs_slice, boss_ver_2)
    return DEFAULT_DIFFICULTY

def is_overkill_on_boss(line: list[str]):
    if line[10] == "0":
        return
    if line[4][6:-6] not in BOSSES_GUIDS:
        return
    return int(line[9]) - int(line[10]) > 2

def is_kill(last_line: str):
    line = last_line.split(',', 11)
    if line[1] == "UNIT_DIED":
        return True
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

def auras_removed(logs_slice: list[str], size):
    removed = 0
    for line in logs_slice:
        line = line.split(',', 5)
        if line[1] != "SPELL_AURA_REMOVED":
            continue
        if line[4][6:-6] in COWARDS:
            removed += 1
    # print(removed)
    return removed > size

def format_attempt(logs: list[str], segment: tuple[int, int], boss_name: str, attempt: int, shift: int):
    # print(boss_name, segment, shift)
    s, f = segment
    
    logs_slice = logs[s:f]
    # if not logs_slice:
    #     logs_slice = logs[s:]
    #     for x in logs[s:s+100]:
    #         print(x)
    diff = get_difficulty(logs_slice, boss_name)
    
    slice_duration = get_delta_simple_precise(logs_slice[-1], logs_slice[0]).total_seconds()
    slice_duration_str = duration_to_string(slice_duration)
    slice_duration_str = slice_duration_str[2:]

    kill = is_kill(logs_slice[-1])
    # print(kill)
    if not kill:
        if boss_name == "The Lich King":
            kill = has_fury_of_frostmourne(logs[f-10:f+20])
        elif boss_name in COWARDS_NAMES:
            if diff[:2] == "25":
                kill = auras_removed(logs[f-100:f], 20)
            else:
                kill = auras_removed(logs[f-50:f], 10)
    
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



def convert_to_html_name(name: str):
    return name.lower().replace(" ", "-").replace("'", "")

def get_segments(logs, enc_data: dict[str, list[tuple[int, int]]]):
    segments_data: dict[str, list[dict]] = {}
    boss_to_html: dict[str, str] = {}
    for boss_name, segments in enc_data.items():
        boss_to_html[boss_name] = convert_to_html_name(boss_name)

        boss_data = []
        shift = 0
        for attempt, segment in enumerate(segments):
            segment_data = format_attempt(logs, segment, boss_name, attempt, shift)
            if segment_data["attempt_type"] == "kill":
                shift = attempt+1
            boss_data.append(segment_data)
        segments_data[boss_name] = boss_data
    
    return segments_data

def separate_modes(data: dict[str, list[dict]]):
    separated: dict[str, dict[str, list[dict]]] = {}
    for boss_name, segments in data.items():
        new_segments: dict[str, list[list]] = {}
        for segment in segments:
            diff = segment['diff']
            new_segments.setdefault(diff, []).append(segment)
        separated[boss_name] = new_segments
    return separated
