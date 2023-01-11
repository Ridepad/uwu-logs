from collections import defaultdict

from constants import BOSSES_GUIDS, MULTIBOSSES, T_DELTA, convert_to_fight_name, running_time, get_delta

MULTIBOSSES_MAIN = {guid: boss_guids[0] for boss_guids in MULTIBOSSES.values() for guid in boss_guids[1:]}
BOSSES_GUIDS_ALL = set(MULTIBOSSES_MAIN) | set(MULTIBOSSES_MAIN.values()) | set(BOSSES_GUIDS)
FLAGS = {'UNIT_DIED', 'PARTY_KILL', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE', 'SPELL_AURA_APPLIED', 'SPELL_AURA_REMOVED', 'SPELL_HEAL'}
FLAGS = {'UNIT_DIED', 'SWING_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SPELL_HEAL'}
HEAL_BOSSES = {"008FB5"}
IGNORED_SPELL_IDS = {
    '56190', '56191', '55346', # Lens
    '60122', # Baby Spice
    '53338', '1130', '14323', '14324', '14325', '19421', '19422', '19423', # Hunter's Mark
    '70861', # Sindragosa's Lair Teleport
    '72550', # Malleable Goo
    '72273', # Vile Gas
    '72371', # Blood Power
    '70952', # Invocation of Blood
    '72443', # Boiling Blood
    '72410', # Rune of Blood
    '72905', '72907', '72906', '72908', # Frostbolt Volley
}
BOSS_MAX_SEP = {
    "009BB7": T_DELTA["2MIN"],
    "008704": T_DELTA["2MIN"],
    "008EF5": T_DELTA["3MIN"],
}
BOSSES_LIKE_LK = {
    "008EF5",
}
FINISH_SPELLS = {
    "72350",
}

@running_time
def dump_all_boss_lines(logs: list[str]):
    _bosses: defaultdict[str, list[tuple[int, list[str]]]] = defaultdict(list)
    for n, line in enumerate(logs):
        if '0xF' not in line:
            continue
        line = line.split(',', 11)
        if line[1] not in FLAGS:
            continue
        if line[2] == line[4]:
            continue
        if line[-1] == "BUFF":
            continue
        
        try:
            if line[6] in IGNORED_SPELL_IDS:
                continue
        except IndexError:
            pass

        _guid = line[4][6:-6]
        if _guid not in HEAL_BOSSES and line[1] == "SPELL_HEAL":
            continue
        
        if _guid not in BOSSES_GUIDS_ALL:
            try:
                if line[6] not in FINISH_SPELLS:
                    continue
            except IndexError:
                continue

        _guid = MULTIBOSSES_MAIN.get(_guid, _guid)
        _bosses[_guid].append((n, line))
    return _bosses

def to_int(timestamp: str):
    i = timestamp.index('.')
    return int(timestamp[i-8:i].replace(':', ''))

def is_same_date_hour(new_timestamp: str, last_timestamp: str):
    return new_timestamp.split(':', 1)[0] == last_timestamp.split(':', 1)[0]

def remove_short_segments(segments: list[tuple[int, int]]):
    for pair in list(segments):
        s, f = pair
        if f - s < 500:
            segments.remove(pair)
            # print(f"REMOVED: {s:>8} {f:>8}")

@running_time
def time_pairs(times: tuple[int, list[str]], boss_id):
    # print()
    # print(boss_id)

    last_index, line = times[0]
    last_timestamp = line[0]
    last_time = to_int(last_timestamp)
    INDEXES: set[int] = {
        last_index, # first line
        times[-1][0]+1, # last line
    }

    MAX_SEP = BOSS_MAX_SEP.get(boss_id, T_DELTA["1MIN"])
    for line_index, line in times:
        new_timestamp = line[0]
        now = to_int(new_timestamp)
        # if now - last_time > 100:
        #     _delta = get_delta(new_timestamp, last_timestamp)
        #     if _delta > MAX_SEP:
        #         print(_delta)
        #         print(last_timestamp)
        #         print(new_timestamp)
        if (
            now - last_time > 100
            and get_delta(new_timestamp, last_timestamp) > MAX_SEP
        ):
            INDEXES.add(last_index+1)
            INDEXES.add(line_index)
        last_time = now
        last_index = line_index
        last_timestamp = new_timestamp

    sorted_indexes = sorted(INDEXES)
    # print(sorted_indexes)
    if len(sorted_indexes) & 1:
        sorted_indexes.pop(0)
    # print(sorted_indexes)
    
    segments = list(zip(sorted_indexes[::2], sorted_indexes[1::2]))
    remove_short_segments(segments)
    # print(segments)
    return segments

def is_overkill_on_boss(line: list[str]):
    if line[10] == "0":
        return
    if line[4][6:-6] not in BOSSES_GUIDS:
        return
    # print(line)
    return int(line[9]) - int(line[10]) > 2
def get_more_precise(times: list[tuple[int, list[str]]]):
    LIMIT = 75
    for n, (_, line) in enumerate(times[-LIMIT:], -LIMIT+1):
        try:
            if line[1] == "UNIT_DIED" or is_overkill_on_boss(line):
                return times if n == 0 else times[:n]
        except IndexError:
            pass
    
    return times

@running_time
def filter_bosses(filtered_logs: dict[str, tuple]) -> dict[str, list[tuple[int, int]]]:
    bosses = {}
    
    for boss_id, times in filtered_logs.items():
        if len(times) < 250:
            continue
        
        fight_name = convert_to_fight_name(boss_id)
        if fight_name is None:
            continue

        times = get_more_precise(times)
        
        bosses[fight_name] = time_pairs(times, boss_id)
    
    return bosses

def find_fury_of_frostmourne(logs_slice):
    for n, line in enumerate(logs_slice):
        if '72350' in line and '0008EF5' in line and 'START' not in line:
            return n

def refine_lk(data: dict, logs):
    '''precise LK split at Fury of Frostmourne'''

    LK = data.get('The Lich King')
    if not LK:
        return

    LAST_TRY_S, LAST_TRY_F = LK[-1]

    fof = find_fury_of_frostmourne(logs[LAST_TRY_S:LAST_TRY_F])
    if fof is not None:
        print("refine_lk len(LK) = 1 fof is not None")
        LK[-1:] = [(LAST_TRY_S, LAST_TRY_S+fof+1), (LAST_TRY_S+fof, LAST_TRY_F)]
    
    elif len(LK) > 1:
        prelast_s, prelast_f = LK[-2]
        shifted_f = max(0, prelast_f-5000)
        fof = find_fury_of_frostmourne(logs[shifted_f:prelast_f])
        print(f"{prelast_s=} {prelast_f=} {shifted_f=} {fof=}")
        if fof is not None:
            print("refine_lk len(LK) > 1 fof is not None")
            print(LK)
            LK[-2:] = [(prelast_s, shifted_f+fof+1), (shifted_f+fof, LAST_TRY_F)]
            print(LK)

def refine_lk(data: dict, logs):
    LK = data.get('The Lich King')
    if not LK:
        return
    print(LK)
    to_change = []
    for n, (s, f) in enumerate(LK):
        fof = find_fury_of_frostmourne(logs[s:f])
        if fof is not None:
            new_split = s+fof
            print(n, [(s, new_split+1), (new_split, f)])
            to_change.append((n, [(s, new_split+1), (new_split, f)]))

    for i, z in reversed(to_change):
        print(i, z)
        LK[i:i+1] = z
    print(LK)

@running_time
def main(logs):
    _all_boss_lines = dump_all_boss_lines(logs)
    data = filter_bosses(_all_boss_lines)
    # print(data)
    refine_lk(data, logs)
    # print(data)
    return data
