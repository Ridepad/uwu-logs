import json
from collections import defaultdict

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

def _timestamp_float(s: str):
    ts = _timestamp(s)
    return to_float(ts)


class LineDeltaSeconds:
    __slots__ = "start_minutes", "start_seconds", 
    def __init__(self, start_minutes: int, start_seconds: float):
        self.start_minutes = start_minutes
        self.start_seconds = start_seconds
    
    def get_delta(self, current_ts: str):
        _minutes, _seconds = to_float(current_ts)
        _seconds = _seconds - self.start_seconds
        _minutes = _minutes - self.start_minutes
        return int((_minutes * 60 + _seconds)*1000)

class EndAfterHour(LineDeltaSeconds):
    def get_delta(self, current_ts: str):
        _minutes, _seconds = to_float(current_ts)
        _seconds = _seconds - self.start_seconds
        if _minutes > 40:
            _minutes = _minutes - self.start_minutes - 60
        else:
            _minutes = _minutes - self.start_minutes
        return int((_minutes * 60 + _seconds)*1000)
    
class StartsBeforeHour(LineDeltaSeconds):
    def get_delta(self, current_ts: str):
        _minutes, _seconds = to_float(current_ts)
        _seconds = _seconds - self.start_seconds
        if _minutes < 20:
            _minutes = _minutes - self.start_minutes + 60
        else:
            _minutes = _minutes - self.start_minutes
        return int((_minutes * 60 + _seconds)*1000)


def get_delta_wrap(logs_slice, combat_start_line: str):
    start_minutes, start_seconds = _timestamp_float(combat_start_line)
    first_minutes, _ = _timestamp_float(logs_slice[0])
    end_minutes, _ = _timestamp_float(logs_slice[-1])
    if first_minutes > start_minutes:
        c = EndAfterHour
    elif start_minutes > end_minutes:
        c = StartsBeforeHour
    else:
        c = LineDeltaSeconds
    return c(start_minutes, start_seconds).get_delta

@running_time
def get_history(logs_slice: list[str], source_guid: str, ignored_guids: set[str], combat_start_line: str):
    flags = set()
    history = defaultdict(list)

    get_delta = get_delta_wrap(logs_slice, combat_start_line)

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
    
    return {
        "DATA": history,
        "FLAGS": flags,
    }


class Timeline(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def get_spell_history(self, s: int, f: int, guid: str) -> dict[str, defaultdict[str, int]]:
        s_shifted = self.find_shifted_log_line(s, -180)
        logs_slice = self.LOGS[s_shifted:f]

        players_and_pets = self.get_players_and_pets_guids()
        combat_start_line = self.LOGS[s]
        data = get_history(logs_slice, guid, players_and_pets, combat_start_line)

        self.spell_history_combine_spells(data["DATA"])
        
        data["SPELLS"] = {
            x: self.SPELLS[int(x)].to_dict()
            for x in data["DATA"]
        }
        data["RDURATION"] = self.get_slice_duration(s, f)
        data["NAME"] = self.guid_to_name(guid)
        data["CLASS"] = self.get_classes().get(guid, "npc")

        return data
    
    def spell_history_combine_spells(self, player_history: dict[str, tuple]):
        for spell_id in list(player_history):
            if spell_id not in COMBINE_SPELLS:
                continue
            main_spell_id = COMBINE_SPELLS[spell_id]
            if main_spell_id not in self.SPELLS:
                continue
            combined = player_history[main_spell_id] + player_history.pop(spell_id)
            player_history[main_spell_id] = sorted(combined)

    @running_time
    def get_spell_history_wrap_json(self, s: int, f: int, player_name: str):
        player_guid = self.name_to_guid(player_name)
        spell_history = self.get_spell_history(s, f, player_guid)
        return json.dumps(spell_history, default=list)
