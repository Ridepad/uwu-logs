from collections import defaultdict

from constants import BOSSES_GUIDS, MULTIBOSSES, T_DELTA_1MIN, T_DELTA_2MIN, running_time, to_dt

BOSS_MAX_SEP = {
    "Halion": T_DELTA_2MIN,
    "Anub'arak": T_DELTA_2MIN,
}
ANOTHER_BOSSES = {y:x[0] for x in MULTIBOSSES.values() for y in x[1:]}
BOSSES_GUIDS_ALL = set(ANOTHER_BOSSES) | set(ANOTHER_BOSSES.values()) | set(BOSSES_GUIDS)
FLAGS = {'UNIT_DIED', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE', 'SPELL_AURA_APPLIED', 'SPELL_HEAL'}
IGNORED_IDS = {
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
}

def convert_to_names(data: dict):
    B = {guids[0]:name for name, guids in MULTIBOSSES.items()}
    return {B.get(x, BOSSES_GUIDS[x]): y for x,y in data.items()}

@running_time
def dump_all_boss_lines(logs: list[str]):
    _bosses: defaultdict[str, list[tuple[int, list[str]]]] = defaultdict(list)
    for n, line in enumerate(logs):
        line = line.split(',')
        if line[1] not in FLAGS:
            continue
        if line[2] == line[4]:
            continue
        if line[-1] == "BUFF":
            continue
        
        try:
            if line[6] in IGNORED_IDS:
                continue
        except IndexError:
            pass
        
        _guid = line[4][6:-6]
        if _guid not in BOSSES_GUIDS_ALL:
            _guid = line[2][6:-6]
            if _guid not in BOSSES_GUIDS_ALL:
                continue
        _guid = ANOTHER_BOSSES.get(_guid, _guid)
        _bosses[_guid].append((n, line))
    return _bosses

def get_more_precise(times: list[tuple[int, list[str]]], limit: int):
    if "UNIT_DIED" in times[-1][1]:
        return times
    lines = [x[1] for x in times[-limit:]][:-1]
    for n, line in enumerate(reversed(lines)):
        if "UNIT_DIED" in line:
            return times[:-n-1]
    
    for n, line in enumerate(lines):
        if line[1] == 'SPELL_AURA_APPLIED':
            continue
        if line[10] != "0":
            return times[:n-limit+1]
    
    return times

def time_pairs(times: tuple[int, list[str]], boss_name):
    MAX_SEP = BOSS_MAX_SEP.get(boss_name, T_DELTA_1MIN)
    last_index, line = times[0]
    indexes: set[int] = {last_index, }
    last_time_dt = to_dt(line[0])
    times = get_more_precise(times, 20)
    _index = times[-1][0]
    indexes.add(_index+1)
    for line_index, line in times:
        _now = to_dt(line[0])
        if _now - last_time_dt > MAX_SEP:
            indexes.add(last_index+1)
            indexes.add(line_index)
        last_time_dt = _now
        last_index = line_index

    sorted_indexes = sorted(indexes)
    return list(zip(sorted_indexes[::2], sorted_indexes[1::2]))

@running_time
def filter_bosses(filtered_logs: dict[str, tuple]):
    return {
        boss_name: time_pairs(times, boss_name)
        for boss_name, times in filtered_logs.items()
        if len(times) > 250
    }

def find_fof(logs_slice):
    for n, line in enumerate(logs_slice):
        if '72350' in line and '0008EF5' in line and 'SPELL_CAST_START' not in line: # Fury of Frostmourne
            return n

def refine_lk(data, logs):
    '''precise LK split at FOF'''

    if 'The Lich King' not in data:
        return
    LK = data['The Lich King']
    last_s, last_f = LK[-1]
    attempt = -2
    if len(LK) > 1:
        attempt = -1
        prelast_s, prelast_f = LK[-2]
        shifted_f = max(0, prelast_f-5000)
        logs_slice = logs[shifted_f:prelast_f]
        fof = find_fof(logs_slice)
        if fof is not None:
            LK[-2:] = [(prelast_s, shifted_f+fof+1), (shifted_f+fof, last_f)]
            return

    logs_slice = logs[last_s:last_f]
    fof = find_fof(logs_slice)
    if fof is not None:
        LK[attempt:] = [(last_s, last_s+fof+1), (last_s+fof, last_f)]

def remove_short_tries(data: dict[str, list[tuple[int, int]]]):
    for boss_name, pairs in data.items():
        for pair in list(pairs):
            s, f = pair
            if f - s < 500:
                pairs.remove(pair)
                print(f"REMOVED: {s:>8} {f:>8} {boss_name}")

@running_time
def main(logs):
    _all_boss_lines = dump_all_boss_lines(logs)
    _all_boss_lines_names = convert_to_names(_all_boss_lines)
    data = filter_bosses(_all_boss_lines_names)
    refine_lk(data, logs)
    remove_short_tries(data)
    return data
