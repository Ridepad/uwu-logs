import os
from typing import List
import constants
import _main
from multiprocessing import Pool

# melee = {'32': {'Shadowfiend'}, '4': {'Living Ember', 'Living Inferno', 'Greater Fire Elemental'}}
# {'61290'}
# {'SPELL_DAMAGE', 'SPELL_MISSED', 'SPELL_CAST_SUCCESS'}
# {'0x20': {'Shahmaran'}}
# {'61291'}
# {'SPELL_AURA_REMOVED', 'SPELL_PERIODIC_DAMAGE', 'SPELL_AURA_APPLIED'}
# {'0x4': {'Shahmaran'}}

DMG_FLAGS = {'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'DAMAGE_SHIELD', 'DAMAGE_SPLIT'}

HEAL_FLAGS = {'SPELL_HEAL', 'SPELL_PERIODIC_HEAL'}
ALL_FLAGS = DMG_FLAGS | HEAL_FLAGS

@constants.running_time
def get_all_spells(logs: List[str]):
    '''spells[id] = {"name": line[7], 'school': line[8], 'flags': set()}'''
    spells = {}
    digits = '1234567890'
    for line in logs:
        if ',SPELL' not in line:
            continue
        # if ",0x1," in line:
        #     continue
        line = line.split(',')
        # if line[7][0] in digits:
            # continue
        # q = s.get(line[6])
        # if not q:
            # q = s[line[6]] = {"name": line[7], "school": line[8]}
        # q.setdefault("flags", set()).add(line[1])
        try:
            q = spells[line[6]]
        except KeyError:
            q = spells[line[6]] = {'name': line[7], 'school': line[8], 'flags': set()}
            # q = spells[line[6]] = {'name': line[7], 'school': s, 'flags': set()}
        # assert s == q['school'], f"{s} is not equal to current | {q['school']}"
        q['flags'].add(line[1])
    for v in spells.values():
        v['school'] = int(v['school'], 16)
    return spells

def validate_all_in(spells_data: dict):
    for v in spells_data.values():
        s = v['school']
        if s not in constants.SPELLS_SCHOOLS:
            print('WARNING: SPELL SCHOOL MISSING', s, v['name'])


@constants.running_time
def get_all_spells2(logs: List[str]):
    digits = '1234567890'
    sss = set()
    c = 0
    spells = {}
    for line in logs:
        if ",0x1," in line:
            continue
        line = line.split(',')
        if line[1] not in ALL_FLAGS:
            try:
                q = spells[line[7]]
            except KeyError:
                q = spells[line[7]] = {"ids": set(), 'schools': set(), 'flags': set()}
            continue
        # if line[-1] == "0x0": #144 results - skip 
        #     c+=1
        #     continue
        # try:
            # if line[7][0] in digits:
            #     continue
        try:
            q = spells[line[7]]
        except KeyError:
            q = spells[line[7]] = {"ids": set(), 'schools': set(), 'flags': set()}
        q['ids'].add(line[6])
        q['schools'].add(line[8])
        q['flags'].add(line[1])
            # if not q:
                # q = s[line[6]] = {"name": line[7], "school": int(line[8], 16)}
            # q.setdefault("flags", set()).add(line[1])
        # except (IndexError, ValueError):
            # pass
    print(sss)
    print(c)
    return spells

@constants.running_time
def get_all_spells3(logs: List[str]):
    '''spells[id] = {"name": line[7], 'school': line[8], 'flags': set()}'''
    spells = {}
    digits = '1234567890'
    for line in logs:
        if ',SPELL' not in line:
            continue
        # if ",0x1," in line:
        #     continue
        line = line.split(',')
        # if line[7][0] in digits:
            # continue
        # q = s.get(line[6])
        # if not q:
            # q = s[line[6]] = {"name": line[7], "school": line[8]}
        # q.setdefault("flags", set()).add(line[1])
        try:
            q = spells[line[6]]
        except KeyError:
            q = spells[line[6]] = {'name': line[7], 'school': line[8], 'flags': set()}
            # q = spells[line[6]] = {'name': line[7], 'school': s, 'flags': set()}
        # assert s == q['school'], f"{s} is not equal to current | {q['school']}"
        q['flags'].add(line[1])
    for v in spells.values():
        v['school'] = int(v['school'], 16)
    return spells

def main(name):
    print(name)
    LOGS = _main.THE_LOGS(name)
    logs = LOGS.get_logs()
    q = get_all_spells(logs)
    # validate_all_in(q)
    sdname = f'./LogsDir/{name}/SPELLS_DATA'
    constants.pickle_write(sdname, q)


if __name__ == '__main__':
    folders = next(os.walk('./LogsDir/'))[1]
    _list = [x for x in reversed(folders) if '-' in x]
    # i = _list.index('21-05-09--19-29--Meownya')
    # _list = _list[i:]
    with Pool(6) as p:
        print(p.map(main, _list))
        # name = '21-06-06--19-29--Meownya'
