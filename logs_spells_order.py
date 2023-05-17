from collections import defaultdict

import file_functions
from constants import running_time

def get_spells():
    spells_json = file_functions.json_read("___spells_icons")
    return {
        spell_id: icon_name
        for icon_name, _spells in spells_json.items()
        for spell_id in _spells
    }
SPELLS3 = get_spells()

IGNORED_FLAGS = {
    'SPELL_HEAL',
    'SPELL_PERIODIC_HEAL',
    'ENCHANT_APPLIED',
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
    minutes, seconds = s[-9:-2].split(":", 1)
    return int(minutes) * 60 + float(seconds)

def to_str(k: float):
    seconds = k % 60
    minutes = k // 60
    return f"{minutes:0>2.0f}:{seconds:0>4.1f}"

def to_float(s: str):
    minutes, seconds = s[-9:].split(":", 1)
    return int(minutes) * 60 + float(seconds)

def to_str(k: float):
    seconds = k % 60
    minutes = k // 60
    return f"{minutes:0>2.0f}:{seconds:0>6.3f}"

@running_time
def get_history(logs: list[str], guid: str, other_players_and_pets: set[str]):
    def get_delta(current_ts: str):
        new_key = to_float(current_ts) - FIRST_KEY
        if new_key < 0:
            new_key = new_key + 3600
        return new_key
    
    def get_percentage(from_start: float):
        return from_start / FIGHT_DURATION * 100

    history = defaultdict(list)
    flags = set()
    FIRST_KEY = to_float(logs[0].split(",", 1)[0])
    FIGHT_DURATION = get_delta(logs[-1].split(",", 1)[0])

    if guid in other_players_and_pets:
        other_players_and_pets.remove(guid)
    
    for line in logs:
        if guid not in line:
            continue
        try:
            timestamp, flag, _, sName, tGUID, tName, spell_id, _, *o = line.split(',', 9)
            if flag in IGNORED_FLAGS:
                continue
            if tGUID in other_players_and_pets:
                continue
            # if sGUID != guid:
                # if o[-1] != "BUFF":
                    # continue
            if o[-1] == "BUFF":
                if tGUID != guid and tGUID[:3] == "0x0":
                    continue
            _delta = get_delta(timestamp)
            history[spell_id].append([get_percentage(_delta), to_str(_delta), flag, sName, tName, o[-1]])
            flags.add(flag)
        except:
            # PARTY_KILL UNIT_DIED
            continue
    
    return {
        "DATA": history,
        "FLAGS": flags,
    }
