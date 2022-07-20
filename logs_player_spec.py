import constants
from constants import CLASS_FROM_HTML, SPECS_LIST, SPELL_BOOK_SPEC

CLASSES = list(CLASS_FROM_HTML)

def specs_gen(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    class_spells = {guid: SPELL_BOOK_SPEC[classes[guid]] for guid in players if guid in classes}
    for line in logs:
        line_split = line.split(',', 8)
        if line_split[2] not in class_spells:
            continue
        try:
            if line_split[6] not in class_spells[line_split[2]]:
                continue
        except IndexError:
            continue
        guid = line_split[2]
        spec_index = class_spells[guid][line_split[6]]
        yield guid, spec_index
        class_spells.pop(guid, None)
        if not class_spells:
            break


def get_specs_guids(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    specs = {guid: 0 for guid in players}
    for guid, spec_index in specs_gen(logs, players, classes):
        specs[guid] = spec_index
    return specs

def get_spec_info(player_class, spec_index=0):
    classi = CLASSES.index(player_class)
    return SPECS_LIST[classi*4+spec_index]

@constants.running_time
def get_specs(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    specs = get_specs_guids(logs, players, classes)
    
    new_data: dict[str, tuple[str, str]] = {}
    for guid, spec_index in specs.items():
        player_class = classes[guid]
        player_name = players[guid]
        new_data[player_name] = get_spec_info(player_class, spec_index)
    
    return new_data

def get_specs_no_names(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    specs = get_specs_guids(logs, players, classes)
    
    new_data: dict[str, tuple[str, str]] = {}
    for guid, spec_index in specs.items():
        player_class = classes[guid]
        classi = CLASSES.index(player_class)
        new_data[guid] = classi*4+spec_index
    
    return new_data
