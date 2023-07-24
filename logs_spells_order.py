from collections import defaultdict

import file_functions
from constants import running_time

@running_time
def get_spells_int():
    spells_json = file_functions.json_read("___spells_icons")
    return {
        int(spell_id): icon_name
        for icon_name, _spells in spells_json.items()
        for spell_id in _spells
    }
def _get_spells():
    spells = None
    def get_spells_inner():
        nonlocal spells
        if spells:
            return spells
        spells = get_spells_int()
        return spells
    return get_spells_inner
get_spells = _get_spells()

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

COMBINE_SPELLS = {
    "58381": "48156",
    "53022": "53023",
    # "63675": "48300",
    "23881": "23885",
    "2687": "29131",
    "22858": "20230",
    "7386 Sunder Armor": "58567 Sunder Armor",
    " 42897 Arcane Blast": "36032 Arcane Blast",
    "  55362 Living Bomb": "55360 Living Bomb (DoT)",
    "   22482 Blade Flurry": "13877 Blade Flurry",
    "   57841 Killing Spree": "51690 Killing Spree",
    "   57842 Killing Spree": "51690 Killing Spree",
    "   34075 Aspect of the Viper": "34074 Aspect of the Viper",
    "    58433 Volley": " 58434 Volley",
    "   49065 Explosive Trap Effect ": "49067 Explosive Trap ",
    "   50590 Immolation ": "50589 Immolation Aura ",
    "   47834 Seed of Corruption ": "47836 Seed of Corruption ",
    "   686 Shadow Bolt ": "47809 Shadow Bolt ",
    "    61290 Shadowflame ": " 61291 Shadowflame ",
    "    48466 Hurricane ": " 48467 Hurricane ",
    "49088 Anti-Magic Shell ": " 48707 Anti-Magic Shell ",
    "47632 Death Coil ": " 49895 Death Coil ",
    "52212 Death and Decay ": " 49938 Death and Decay ",
    "53506 Moonkin Form": " 24858 Moonkin Form ",
}

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
