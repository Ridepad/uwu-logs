from collections import defaultdict

import file_functions
from constants import COMBINE_SPELLS, SPELL_ICONS_DB, running_time

@running_time
def get_spells_int():
    spells_json = file_functions.json_read(SPELL_ICONS_DB)
    return {
        int(spell_id): icon_name
        for icon_name, _spells in spells_json.items()
        for spell_id in _spells
    }

get_spells = file_functions.cache_file_until_new(SPELL_ICONS_DB, get_spells_int)

IGNORED_FLAGS = {
    "SPELL_HEAL",
    "SPELL_PERIODIC_HEAL",
    "ENCHANT_APPLIED",
    "ENCHANT_REMOVED",
    "SPELL_DRAIN",
    "ENVIRONMENTAL_DAMAGE",
}


def to_int(s: str):
    minutes, seconds = s.split(":", 1)
    return int(minutes) * 600 + int(seconds.replace('.', ''))

def convert_keys(data: dict[str, int]):
    FIRST_KEY = to_int(list(data)[0])
    for k in list(data):
        new_key = to_int(k) - FIRST_KEY
        if new_key < 0:
            new_key = new_key + 36000
        data[new_key] = data.pop(k)


def to_float(s: str):
    minutes, seconds = s[-9:].split(":", 1)
    return int(minutes) * 60000 + float(seconds) * 1000

@running_time
def get_history(logs: list[str], source_guid: str, ignored_guids: set[str]=None):
    def get_delta_from_start(current_ts: str):
        new_key = to_float(current_ts) - FIRST_KEY
        if new_key < 0:
            new_key = new_key + 3600000
        return new_key / 1000
    
    history = defaultdict(list)
    flags = set()
    FIRST_KEY = to_float(logs[0].split(",", 1)[0])

    if ignored_guids is None:
        ignored_guids = set()
    elif source_guid in ignored_guids:
        ignored_guids.remove(source_guid)
    
    for line in logs:
        if source_guid not in line:
            continue
        try:
            timestamp, flag, _, sName, tGUID, tName, spell_id, _, etc = line.split(',', 8)
            if flag in IGNORED_FLAGS or tGUID in ignored_guids:
                continue
            _delta = get_delta_from_start(timestamp)
            history[spell_id].append((_delta, flag, sName, tName, tGUID, etc))
            # history[spell_id].append({
            #     "ts": _delta,
            #     "flag": flag,
            #     "sName": sName,
            #     "tName": tName,
            #     "etc": etc,
            # })
            flags.add(flag)
        except ValueError:
            print(line)
            continue

    for spell_id in list(history):
        if spell_id not in COMBINE_SPELLS:
            continue
        main_spell_id = COMBINE_SPELLS[spell_id]
        history[main_spell_id] = sorted(history[main_spell_id] + history.pop(spell_id))
    
    return {
        "DATA": history,
        "FLAGS": flags,
    }
