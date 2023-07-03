from collections import defaultdict

from constants import LOGGER_REPORTS, is_player, running_time, sort_dict_by_value

FLAG_DAMAGE = {
    "SPELL_DAMAGE",
    "SPELL_PERIODIC_DAMAGE",
    "SWING_DAMAGE",
    "RANGE_DAMAGE",
    "DAMAGE_SHIELD",
}
FLAG_HEAL = {
    "SPELL_HEAL",
    "SPELL_PERIODIC_HEAL",
}

def dmg_gen(logs: list[str]):
    for line in logs:
        if "_DAMAGE" not in line:
            continue
        _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
        yield guid, int(d) - int(ok)

def dmg_gen_no_friendly(logs: list[str], players_and_pets: set[str]):
    for line in logs:
        if "_DAMAGE" not in line:
            continue
        _, _, guid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
        if tguid in players_and_pets:
                continue
        yield guid, int(d) - int(ok)

def dmg_gen_targets(logs: list[str], targets: set[str]):
    for line in logs:
        if "_DAMAGE" not in line:
            continue
        _, _, guid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
        if tguid[:-6] not in targets:
                continue
        yield guid, int(d) - int(ok)

def heal_gen(logs: list[str]):
    for line in logs:
        if "_H" not in line:
            continue
        _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
        if d != ok:
            yield guid, int(d) - int(ok)

def heal_gen_target(logs: list[str], target_guid=None):
    if target_guid is None:
        return heal_gen(logs)
    
    for line in logs:
        if "_H" not in line:
            continue
        _, _, guid, _, tGUID, _, _, _, _, d, ok, _ = line.split(',', 11)
        if d != ok and tGUID == target_guid:
            yield guid, int(d) - int(ok)

DATA_GEN = {
    "damage": dmg_gen,
    "heal": heal_gen,
    "damage_no_friendly": dmg_gen_no_friendly,
    "damage_targets": dmg_gen_targets,
}

def parse_data(gen):
    data = defaultdict(int)
    for guid, amount in gen:
        data[guid] += amount
    return data

def parse_only_dmg(logs):
    gen_func = DATA_GEN["damage"]
    gen = gen_func(logs)
    return parse_data(gen)

def parse_only_dmg_no_friendly(logs, players_and_pets):
    gen_func = DATA_GEN["damage_no_friendly"]
    gen = gen_func(logs, players_and_pets)
    return parse_data(gen)

def parse_dmg_targets(logs, targets):
    gen_func = DATA_GEN["damage_targets"]
    gen = gen_func(logs, targets)
    return parse_data(gen)

def parse_only_heal(logs):
    gen_func = DATA_GEN["heal"]
    gen = gen_func(logs)
    return parse_data(gen)


@running_time
def parse_both(logs: list[str], players_and_pets: set[str]):
    DMG: defaultdict[str, int] = defaultdict(int)
    HEAL: defaultdict[str, int] = defaultdict(int)
    TAKEN: defaultdict[str, int] = defaultdict(int)
    
    for line in logs:
        if "_DAMAGE" in line:
            _, _, guid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
            if tguid in players_and_pets:
                TAKEN[tguid] += int(d)
            else:
                DMG[guid] += int(d)
        
        elif "_H" in line:
            _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
            if d != ok:
                HEAL[guid] += int(d) - int(ok)

    return {
        "damage": DMG,
        "heal": HEAL,
        "taken": TAKEN
    }

def parse_dmg_all_no_friendly(logs: list[str], players_and_pets: set[str]):
    data = defaultdict(int)
    for line in logs:
        if "_DAMAGE" not in line:
            continue
        _line = line.split(',', 10)
        if _line[2] in players_and_pets and _line[4] not in players_and_pets:
            data[_line[2]] += int(_line[9])
    return data

CUSTOM_UNITS = {"00958D"}

def add_pets_guids(data: dict[str, int], guids: dict[str, dict[str, str]]):
    players: defaultdict[str, int] = defaultdict(int)
    custom: defaultdict[str, int] = defaultdict(int)
    other: defaultdict[str, int] = defaultdict(int)

    for sGUID, value in data.items():
        if sGUID not in guids:
            LOGGER_REPORTS.error(f"{sGUID} not in GUIDS!")
            continue

        masterGUID = guids[sGUID].get('master_guid', sGUID)
        if sGUID[6:-6] in CUSTOM_UNITS:
            custom[masterGUID] += value
        elif is_player(masterGUID):
            players[masterGUID] += value
        else:
            other[masterGUID] += value

    return {
        "players": players,
        "custom": custom,
        "other": other,
    }

def add_pets(data: dict[str, int], guids: dict[str, dict[str, str]]):
    combined_data = add_pets_guids(data, guids)
    players_dmg: dict[str, int] = {}
    
    for sGUID, value in combined_data["players"].items():
        name = guids[sGUID]["name"]
        players_dmg[name] = value
    
    for sGUID, value in combined_data["custom"].items():
        name = guids[sGUID]["name"]
        players_dmg[f"{name}-A"] = players_dmg.get(name, 0) + value
    
    return players_dmg


@running_time
def dmg_taken_no_source(logs: list[str]):
    dmg = {}
    for line in logs:
        if "_DAMAGE," not in line:
            continue
        # if '_M' in line:
        #     continue
        _, _, _, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
        value = int(d) - int(ok)
        try:
            dmg[tguid] += value
        except KeyError:
            dmg[tguid] = value
    return dmg



def add_pets_no_spells(data, guids):
    new_data = {}
    for guid, value in data.items():
        # guid = check_master(guid, guids)
        guid = guids[guid].get('master_guid', guid)
        new_data[guid] = new_data.get(guid, 0) + value
    return new_data

def uno_reverse(data, guids):
    new_data = {}
    for sname, targets in dict(data).items():
        for tguid, value in targets.items():
            try:
                tname = guids[tguid]["name"]
                q = new_data.setdefault(tname, {})
                q[sname] = q.get(sname, 0) + value
            except KeyError:
                # irrelevant
                pass
    return new_data

def sort_dmg_taken(data: dict[str, dict[str, int]]):
    for tname, sources in data.items():
        data[tname] = sort_dict_by_value(sources)
    return data

@running_time
def parse_dmg_by_src(logs: list[str]):
    '''damage_taken = {source_guid: {target_guid: value}}'''
    dmg = {}
    for line in logs:
        if "_DAMAGE," in line:
            _, _, sguid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
            value = int(d) - int(ok)
            try:
                q = dmg[sguid]
            except KeyError:
                q = dmg[sguid] = {}
            try:
                q[tguid] += value
            except KeyError:
                q[tguid] = value
    return dmg


@running_time
def parse_dmg_taken_single(logs: list[str], filter_guid) -> dict[str, dict[str, int]]:
    '''damage_taken = {source_guid: {target_guid: value}}'''
    dmg = {}
    for line in logs:
        if "_DAMAGE," in line:
        # if "_DAMAGE," in line and filter_guid in line:
            _, _, sguid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
            if filter_guid not in tguid:
                continue
            value = int(d) - int(ok)
            try:
                q = dmg[tguid]
            except KeyError:
                q = dmg[tguid] = {}
            try:
                q[sguid] += value
            except KeyError:
                q[sguid] = value
    return dmg

@running_time
def parse_dmg_taken(logs: list[str], filter_guids):
    '''damage_taken = {source_guid: {target_guid: value}}'''
    dmg: dict[str, dict[str, dict[str, int]]] = {}
    for line in logs:
        if "_DAMAGE" not in line:
            continue
        _, _, sguid, _, tguid, _, s_id, _, _, d, ok, _ = line.split(',', 11)
        if tguid not in filter_guids:
            continue
        try:
            tar = dmg[tguid]
        except KeyError:
            tar = dmg[tguid] = {}
        try:
            src = tar[sguid]
        except KeyError:
            src = tar[sguid] = {}
        value = int(d) - int(ok)
        try:
            src[s_id] += value
        except KeyError:
            src[s_id] = value
    return dmg

def readable_logs_line(line: str):
    _line = line.split(',', 8)
    try:
        return f"{_line[0]} {_line[1]} {_line[3]} -> {_line[5]} with {_line[7]}"
    except IndexError:
        return f"{_line[0]} {_line[1]} {_line[3]} -> {_line[5]}"
