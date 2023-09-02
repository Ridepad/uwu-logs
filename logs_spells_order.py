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
    return int(minutes), float(seconds)

def _timestamp(s: str):
    return s.split(',', 1)[0]

def get_delta_wrap(logs_slice, start_index):
    start_minutes, start_seconds = to_float(_timestamp(logs_slice[start_index]))
    first_minutes, _ = to_float(_timestamp(logs_slice[0]))
    end_minutes, _ = to_float(_timestamp(logs_slice[-1]))
    if first_minutes > start_minutes:
        def get_delta(current_ts):
            _minutes, _seconds = to_float(current_ts)
            _seconds = _seconds - start_seconds
            if _minutes > 50:
                _minutes = _minutes - start_minutes - 60
            else:
                _minutes = _minutes - start_minutes
            return int((_minutes * 60 + _seconds)*1000)
    elif start_minutes > end_minutes:
        def get_delta(current_ts: str):
            _minutes, _seconds = to_float(current_ts)
            _seconds = _seconds - start_seconds
            if _minutes < 20:
                _minutes = _minutes - start_minutes + 60
            else:
                _minutes = _minutes - start_minutes
            return int((_minutes * 60 + _seconds)*1000)
    else:
        def get_delta(current_ts):
            _minutes, _seconds = to_float(current_ts)
            _seconds = _seconds - start_seconds
            _minutes = _minutes - start_minutes
            return int((_minutes * 60 + _seconds)*1000)
    return get_delta

@running_time
def get_history(logs_slice: list[str], source_guid: str, ignored_guids: set[str], start_index: int):
    flags = set()
    history = defaultdict(list)

    get_delta = get_delta_wrap(logs_slice, start_index)

    if not ignored_guids:
        ignored_guids = set()
    elif source_guid in ignored_guids:
        ignored_guids.remove(source_guid)
    
    for line in logs_slice:
        if source_guid not in line:
            continue
        try:
            timestamp, flag, _, sName, tGUID, tName, spell_id, _, etc = line.split(',', 8)
            if flag in IGNORED_FLAGS or tGUID in ignored_guids:
                continue
            _delta = get_delta(timestamp)
            history[spell_id].append((_delta, flag, sName, tName, tGUID, etc))
            flags.add(flag)
        except ValueError:
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
