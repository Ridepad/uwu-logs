from h_debug import Loggers, running_time
from c_spells import SPELLS_SCHOOLS, UNUSUAL_SPELLS

LOGGER_UNUSUAL_SPELLS = Loggers.unusual_spells

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
            LOGGER_UNUSUAL_SPELLS.debug(f"MISSING SPELL COLOR: {spell_id:>5} | {v['school']:<5} | {v['color']} | {v['name']}")
        new_spells[int(spell_id)] = v
    return new_spells

@running_time
def get_all_spells(logs: list[str]):
    '''spells[id] = {"name": line[7], 'school': line[8]}'''
    spells = {
        '1': {'name': 'Melee', 'school': '0x1'},
    }
    for line in logs:
        try:
            _line = line.split(',', 7)
            if _line[6] not in spells:
                etc = _line[-1].split(',', 2)
                spells[_line[6]] = {'name': etc[0], 'school': etc[1]}
        except IndexError:
            pass
    return finish_spells(spells)
