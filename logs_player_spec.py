import numpy

from c_player_classes import CLASSES_LIST_HTML, SPELL_BOOK_SPEC
from h_debug import running_time

def _specs_gen_columns(logs, class_spells: dict):
    # a spec defining spell is rare, so the three conditions become one mask
    # over the spell, event and source guid columns; every surviving row is
    # re-checked against class_spells, so the yields match the line loop
    events, guids, _, spells, *_ = logs.dicts()

    wanted = set()
    for spell_book in class_spells.values():
        wanted.update(spell_book)

    spell_hit = numpy.array([sid in wanted for sid, _ in spells], dtype=bool)
    event_ok = numpy.array([e != "SPELL_AURA_REMOVED" for e in events], dtype=bool)
    guid_hit = numpy.array([g in class_spells for g in guids], dtype=bool)

    for block, lo, hi in logs.block_ranges():
        mask = spell_hit[block.spell[lo:hi]]
        mask &= event_ok[block.ev[lo:hi]]
        mask &= guid_hit[block.sguid[lo:hi]]

        for row in (numpy.flatnonzero(mask) + lo).tolist():
            guid = guids[block.sguid[row]]
            if guid not in class_spells:
                continue
            spell_id = spells[block.spell[row]][0]
            if spell_id not in class_spells[guid]:
                continue

            yield guid, class_spells.pop(guid)[spell_id]

            if not class_spells:
                return

# 40% faster to slice 3 times, if check and slice 4 more times, than to slice every loop 8 times
def specs_gen(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    class_spells = {
        guid: SPELL_BOOK_SPEC[classes[guid]]
        for guid in players
        if guid in classes
    }
    if hasattr(logs, "block_ranges"):
        yield from _specs_gen_columns(logs, class_spells)
        return

    for line in logs:
        _, flag, guid, etc = line.split(',', 3)
        if guid not in class_spells:
            continue
        if flag == "SPELL_AURA_REMOVED":
            continue
        try:
            _spell_id = etc.split(',', 4)[3]
            if _spell_id not in class_spells[guid]:
                continue
        except IndexError:
            continue
        
        _spells = class_spells.pop(guid)
        spec_index = _spells[_spell_id]
        yield guid, spec_index

        if not class_spells:
            break

@running_time
def get_specs(logs: list[str], players: dict[str, str], classes: dict[str, str], cut=True):
    if cut:
        logs = logs[:100_000]
    
    SPECS = {}
    for guid, spec_index in specs_gen(logs, players, classes):
        player_class = classes[guid]
        class_index = CLASSES_LIST_HTML.index(player_class)
        SPECS[guid] = class_index * 4 + spec_index

    for player_guid, player_class in classes.items():
        if player_guid in SPECS:
            continue
        spec = CLASSES_LIST_HTML.index(player_class) * 4
        if player_class == "warlock":
            # default to Destruction spec if it could not be detected
            spec += 3
        SPECS[player_guid] = spec

    return SPECS

# def convert_specs_to_full_info(specs: dict[str, int], classes: dict[str, str]):
#     new_data: dict[str, tuple[str, str]] = {}
#     for guid, spec_index in specs.items():
#         player_class = classes[guid]
#         new_data[guid] = get_spec_info(player_class, spec_index)
#     return new_data

# def convert_specs_to_spec_index(specs: dict[str, int], classes: dict[str, str]):
#     new_data: dict[str, int] = {}
#     for guid, spec_index in specs.items():
#         player_class = classes[guid]
#         classi = CLASSES.index(player_class)
#         new_data[guid] = classi*4+spec_index
#     return new_data


# TODO: change to bytes for 10% speed improvement
# _SPELL_BOOK_SPEC = {
#     q.encode(): {
#         k.encode(): v
#         for k,v in w.items() 
#     }
#     for q,w in SPELL_BOOK_SPEC.items()
# }

# def specs_gen_bytes(logs: list[bytes], players: dict[bytes, str], classes: dict[bytes, str]):
#     class_spells = {guid: _SPELL_BOOK_SPEC[classes[guid]] for guid in players if guid in classes}
#     for line in logs:
#         _, _, guid, line = line.split(b',', 3)
#         if guid not in class_spells:
#             continue
#         try:
#             _spell_id = line.split(b',', 4)[3]
#             spec_index = class_spells[guid][_spell_id]
#             del class_spells[guid]
#             yield guid, spec_index
#             if not class_spells:
#                 break
#         except (IndexError, KeyError):
#             continue
