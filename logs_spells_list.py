from constants import LOGGER_UNUSUAL_SPELLS, SPELLS_SCHOOLS, UNUSUAL_SPELLS, running_time

CUSTOM_SPELLS = {
    "42925": "Flamestrike (Rank 8)",
    "49240": "Lightning Bolt (Proc)",
    "49269": "Chain Lightning (Proc)",
    "53190": "Starfall (AoE)",
    "55360": "Living Bomb (DoT)",
    # Off Hand
    "66974": "Obliterate (Off Hand)",
    "66962": "Frost Strike (Off Hand)",
    "61895": "Blood-Caked Strike (Off Hand)",
    "66992": "Plague Strike (Off Hand)",
    "44949": "Whirlwind (Off Hand)",
    "52874": "Fan of Knives (Off Hand)",
    "57842": "Killing Spree (Off Hand)",
    "66217": "Rune Strike (Off Hand)",
}

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
                spells[_line[6]] = {'name': CUSTOM_SPELLS.get(_line[6], etc[0]), 'school': etc[1]}
        except IndexError:
            pass
    return finish_spells(spells)
