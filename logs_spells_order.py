from collections import defaultdict
import json

import logs_base
from c_spells import COMBINE_SPELLS
from h_debug import running_time


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


class Timeline(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def get_spell_history(self, s: int, f: int, guid: str) -> dict[str, defaultdict[str, int]]:
        ts = self.get_timestamp()
        s_shifted = ts[self.find_index(s, 180)]
        logs_slice = self.LOGS[s_shifted:f]

        players_and_pets = self.get_players_and_pets_guids()
        data = get_history(logs_slice, guid, players_and_pets, s-s_shifted)

        data["SPELLS"] = {
            x: self.SPELLS[int(x)].to_dict()
            for x in data["DATA"]
        }
        data["RDURATION"] = self.get_slice_duration(s, f)
        data["NAME"] = self.guid_to_name(guid)
        data["CLASS"] = self.get_classes().get(guid, "npc")

        return data
    
    def get_spell_history_wrap(self, segments: dict, player_name: str):
        s, f = segments[0]
        player = self.name_to_guid(player_name)
        return self.get_spell_history(s, f, player)
    
    def get_spell_history_wrap_json(self, segments: dict, player_name: str):
        return json.dumps((self.get_spell_history_wrap(segments, player_name)), default=list)
