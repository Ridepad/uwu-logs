import constants
from constants import running_time, sort_dict_by_value, is_player
from collections import defaultdict


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

@running_time
def parse_only_dmg(logs):
    gen_func = DATA_GEN["damage"]
    gen = gen_func(logs)
    return parse_data(gen)

@running_time
def parse_only_dmg_no_friendly(logs, players_and_pets):
    gen_func = DATA_GEN["damage_no_friendly"]
    gen = gen_func(logs, players_and_pets)
    return parse_data(gen)

@running_time
def parse_dmg_targets(logs, targets):
    gen_func = DATA_GEN["damage_targets"]
    gen = gen_func(logs, targets)
    return parse_data(gen)

@running_time
def parse_only_heal(logs):
    gen_func = DATA_GEN["heal"]
    gen = gen_func(logs)
    return parse_data(gen)


@running_time
def parse_both(logs: list[str], players_and_pets: set[str]):
    dmg: defaultdict[str, int] = defaultdict(int)
    heal: defaultdict[str, int] = defaultdict(int)
    for line in logs:
        if "_DAMAGE" in line:
            _, _, guid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
            if tguid in players_and_pets:
                continue
            dmg[guid] += int(d) - int(ok)
        
        elif "_H" in line:
            _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
            if d != ok:
                heal[guid] += int(d) - int(ok)
    
    return {
        "damage": dmg,
        "heal": heal,
    }

CUSTOM_UNITS = {"00958D"}

def add_pets_guids(data: dict[str, int], guids: dict[str, dict[str, str]]):
    players: defaultdict[str, int] = defaultdict(int)
    custom: defaultdict[str, int] = defaultdict(int)
    other: defaultdict[str, int] = defaultdict(int)

    for sGUID, value in data.items():
        if sGUID not in guids:
            print(f"[ERROR] {sGUID} not in GUIDS!")
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


def add_pets2(data: dict[str, dict[str, int]], guids):
    new_data = {}
    for tguid, sources in data.items():
        name = guids[tguid]["name"]
        q = new_data.setdefault(name, {})
        for sguid, value in sources.items():
            # sguid = check_master(sguid, guids)
            sguid = guids[sguid].get('master_guid', sguid)
            q[sguid] = q.get(sguid, 0) + value
    return new_data

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

@running_time
def dmg_taken_fast(logs: list[str], filter_guid: str) -> dict[str, int]:
    dmg_hit = 0
    dmg_ok = 0
    dmg_res = 0
    dmg_blk = 0
    dmg_abs = 0
    for line in logs:
        if filter_guid not in line:
            continue
        if "_DAMAGE" not in line:
            continue
        _, _, _, _, tguid, _, _, _, _, d, ok, _, res, blk, absrb, _ = line.split(',', 15)
        if filter_guid not in tguid:
            continue
        if res!="0":
            print(line)
        dmg_hit += int(d)
        dmg_ok += int(ok)
        dmg_res += int(res)
        dmg_blk += int(blk)
        dmg_abs += int(absrb)
    return dmg_hit-dmg_ok, dmg_ok, dmg_res, dmg_blk, dmg_abs


def main_dmg_taken_test_add_pets(data, guids):
    new_dmg = {}
    for guid, value in data:
        name = guids[guid]['name']
        try:
            new_dmg[name] += value
        except KeyError:
            new_dmg[name] = value

    return sort_dict_by_value(new_dmg)

def combine_pet2(
    data: dict[str, dict[str, int]],
    guids: dict[str, dict[str, str]],
):
    new_data: dict[str, dict[int, int]] = {}

    for source_guid, spells in data.items():
        new_source_guid = guids[source_guid].get('master_guid', source_guid)
        if new_source_guid != source_guid:
            spells = {f"-{x}":y for x,y in spells.items()}
        src = new_data.setdefault(new_source_guid, {})
        for s_id, value in spells.items():
            s_id = int(s_id)
            src[s_id] = src.get(s_id, 0) + value

    for source_guid, spells in new_data.items():
        new_data[source_guid] = dict(sort_dict_by_value(spells))

    return new_data

def parse_dmg_taken_add_pets(data: dict[str, dict], guids):
    """
    new_dmg = {
        target_guid: {
            source_guid:{
                spell_id: dmg,
            }
        }
    }
    new_dmg = {
        target_guid: {
            source_guid:[
                (spell_id, dmg),
            ]
        }
    }
    """
    # new_sources: dict[str, dict[str, int]]
    new_dmg: dict[str, dict[str, dict[int, int]]] = {}
    for target_guid, sources in data.items():
        new_dmg[target_guid] = combine_pet2(sources, guids)
        # new_sources = {}
        # for source_guid, spells in sources.items():
        #     new_source_guid = guids[source_guid].get('master_guid', source_guid)
        #     if new_source_guid != source_guid:
        #         spells = {f"-{x}":y for x,y in spells.items()}
        #     src = new_sources.setdefault(new_source_guid, {})
        #     for s_id, value in spells.items():
        #         src[s_id] = src.get(s_id, 0) + value
        # new_dmg[target_guid] = new_sources

    _ttl_tar: dict[str, int] = {}
    _ttl_src: dict[str, dict[str, int]] = {}
    for target_guid, sources in new_dmg.items():
        src = _ttl_src[target_guid] = {}
        for source_guid, spells in sources.items():
            src[source_guid] = sum(spells.values())
        _ttl_tar[target_guid] = sum(src.values())
            
    return new_dmg, _ttl_tar, _ttl_src


def add_space(v):
    return f"{v:,}".replace(',', ' ')

def __test1():
    name = '21-10-29--21-05--Nomadra'
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    guids = report.get_all_guids()
    spells = report.get_spells()
    f = set()
    n = 'Shoggoth'
    filter_guid = report.name_to_guid(n)
    f.add(filter_guid)
    n = 'Nomadra'
    filter_guid = report.name_to_guid(n)
    f.add(filter_guid)
    n = 'Festergut'
    filter_guid = report.name_to_guid(n)
    f.add(filter_guid)
    assert filter_guid is not None
    d = parse_dmg_taken(logs, filter_guid)
    print(d[filter_guid])
    q,w,e = parse_dmg_taken_add_pets(d, guids)
    print(q[filter_guid])
    print(w[filter_guid])
    print(e[filter_guid])
    e = sort_dict_by_value(e[filter_guid])
    for guid, dmg in e:
        print(f"{guids[guid]['name']:<25}{add_space(dmg):>15}")

def __test2():
    name = '22-04-27--21-02--Safiyah'
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    all_guids = report.get_all_guids()
    player_pets = report.get_players_and_pets_guids()
    h1 = parse_both(logs, player_pets)
    h2 = parse_only_dmg(logs)

if __name__ == "__main__":
    import logs_main
    __test2()
