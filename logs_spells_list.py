import _main
import constants

def unusual_spells(v, spell_id):
    _n = v['name'].replace(' ', '-')
    n = f"./unusual_spells/{spell_id}--{_n}--{v['color']}"
    open(n, 'w').close()

def spell_id_to_int(data: dict[str, dict[str, str]]):
    return {int(k): v for k,v in data.items()}

def finish_spells(spells: dict[str, dict]):
    sch = constants.SPELLS_SCHOOLS
    unu = constants.UNUSUAL_SPELLS
    new_spells: dict[int, dict[str, str]] = {}
    for spell_id, v in spells.items():
        color_code_int = int(v['school'], 16)
        try:
            v['color'] = sch[color_code_int]
        except KeyError:
            v['color'] = unu[color_code_int]
            unusual_spells(v, spell_id)
        new_spells[int(spell_id)] = v
    return new_spells

@constants.running_time
def get_all_spells(logs: list[str]):
    '''spells[id] = {"name": line[7], 'school': line[8]}'''
    spells = {
        '1': {'name': 'Melee', 'school': '0x1'},
    }
    for line in logs:
        if ',SPELL' in line or ',RANGE_' in line:
            line = line.split(',')
            spells.setdefault(line[6], {'name': line[7], 'school': line[8]})
    return finish_spells(spells)

def __redo(name):
    print(name)
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    spells = get_all_spells(logs)
    pth = f'LogsDir/{name}/SPELLS_DATA'
    constants.json_write(pth, spells)

if __name__ == '__main__':
    __redo("22-03-25--22-02--Nomadra")
    # constants.redo_data(__redo)
