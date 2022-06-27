import logging

import logs_main
import constants
from constants import SPELLS_SCHOOLS, UNUSUAL_SPELLS


def unusual_spells(v, spell_id):
    _n = v['name'].replace(' ', '-')
    n = f"./unusual_spells/{spell_id}--{_n}--{v['color']}"
    open(n, 'w').close()

def spell_id_to_int(data: dict[str, dict[str, str]]):
    return {int(k): v for k,v in data.items()}

def finish_spells(spells: dict[str, dict]):
    new_spells: dict[int, dict[str, str]] = {}
    for spell_id, v in spells.items():
        try:
            color_code_int = int(v['school'], 16)
        except ValueError:
            continue
        try:
            v['color'] = SPELLS_SCHOOLS[color_code_int]
        except KeyError:
            v['color'] = UNUSUAL_SPELLS[color_code_int]
            unusual_spells(v, spell_id)
        new_spells[int(spell_id)] = v
    return new_spells

CUSTOM_SPELLS = {
    "42925": "Flamestrike (Rank 8)",
    "49240": "Lightning Bolt (Proc)",
    "49269": "Chain Lightning (Proc)",
    "53190": "Starfall (AoE)",
    "55360": "Living Bomb (DoT)",
}

@constants.running_time
def get_all_spells(logs: list[str]):
    '''spells[id] = {"name": line[7], 'school': line[8]}'''
    spells = {
        '1': {'name': 'Melee', 'school': '0x1'},
    }
    for line in logs:
        try:
            line = line.split(',', 9)
            if line[6] not in spells:
                spells[line[6]] = {'name': CUSTOM_SPELLS.get(line[6], line[7]), 'school': line[8]}
        except IndexError:
            pass
    return finish_spells(spells)

def __redo(name):
    print(name)
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    spells = get_all_spells(logs)
    # spells = get_all_spells(logs)
    # spells = get_all_spells(logs)
    # spells = get_all_spells(logs)
    # spells = get_all_spells(logs)
    pth = report.relative_path('SPELLS_DATA.json')
    constants.json_write(pth, spells)

def __redo_wrapped(name):
    try:
        __redo(name)
    except Exception:
        logging.exception(f'spells_list __redo {name}')

if __name__ == '__main__':
    __redo("22-06-24--21-13--Nomadra")
    # __redo("22-06-17--20-57--Nomadra")
    # constants.redo_data(inner)
    # constants.redo_data(__redo_wrapped)
