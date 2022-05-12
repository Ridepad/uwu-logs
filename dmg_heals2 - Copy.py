from typing import Dict, List
import constants

def sort_dict_by_value(data: dict):
    return sorted(data.items(), key=lambda x: x[1], reverse=True)

def check_master(guid: str, guids: dict):
    master_guid = guids[guid].get('master_guid')
    if not master_guid:
        return guid
    return guids.get(master_guid, {}).get('master_guid', master_guid)

@constants.running_time
def parse_only_dmg(logs: List[str]):
    dmg = {}
    for line in logs:
        if "_DAMAGE," in line:
            if ',SW' in line:
                _, _, guid, _, _, _, d, ok, _ = line.split(',', 8)
            else:
                _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
            value = int(d) - int(ok)
            try:
                dmg[guid] += value
            except KeyError:
                dmg[guid] = value
    return dmg

@constants.running_time
def dmg_taken_no_source(logs: List[str]):
    dmg = {}
    for line in logs:
        if "DAMAGE" not in line:
            continue
        if '_M' in line:
            continue
        if ',SW' in line:
            _, _, _, _, tguid, _, d, ok, _ = line.split(',', 8)
        else:
            _, _, _, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
        value = int(d) - int(ok)
        try:
            dmg[tguid] += value
        except KeyError:
            dmg[tguid] = value
    return dmg

@constants.running_time
def parse_only_heal(logs: List[str]):
    heal = {}
    for line in logs:
        if "_H" in line:
            _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
            value = int(d) - int(ok)
            if value:
                try:
                    heal[guid] += value
                except KeyError:
                    heal[guid] = value
    return heal

def add_pets(data, guids):
    new_data = {}
    for guid, value in dict(data).items():
        guid = check_master(guid, guids)
        name = guids[guid]["name"]
        new_data[name] = new_data.get(name, 0) + value
    return new_data

@constants.running_time
def parse_both(logs: List[str]):
    dmg = {}
    heal = {}
    for line in logs:
        if "_DAMAGE," in line:
            if ',SW' in line:
                _, _, guid, _, tguid, _, d, ok, _ = line.split(',', 8)
            else:
                _, _, guid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
            if tguid[:3] == '0x0':
                continue
            try:
                value = int(d) - int(ok)
            except ValueError:
                print('dmg_heals2 ValueError:')
                print(line)
            try:
                dmg[guid] += value
            except KeyError:
                dmg[guid] = value
        elif "_H" in line:
            _, _, guid, _, _, _, _, _, _, d, ok, _ = line.split(',', 11)
            try:
                value = int(d) - int(ok)
            except ValueError:
                print('dmg_heals2 ValueError:')
                print(line)
            if value:
                try:
                    heal[guid] += value
                except KeyError:
                    heal[guid] = value
    return dmg, heal

# def is_pet(guid, guids):
#     master_guid = guids[guid].get('master_guid')
#     if master_guid:
#         master_master = guids.get(master_guid)
#         if master_master:
#             master_guid = master_master.get('master_guid', master_guid)
#         return master_guid
#     return guid


def add_pets_no_spells(data, guids):
    new_data = {}
    for guid, value in data.items():
        guid = check_master(guid, guids)
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

def sort_dmg_taken(data: Dict[str, Dict[str, int]]):
    for tname, sources in data.items():
        data[tname] = sort_dict_by_value(sources)
    return data

@constants.running_time
def parse_only_dmg_taken(logs: List[str]):
    '''damage_taken = {source_guid: {target_guid: value}}'''
    dmg = {}
    for line in logs:
        if "_DAMAGE," in line:
            if ',SW' in line:
                _, _, sguid, _, tguid, _, d, ok, _ = line.split(',', 8)
            else:
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


def add_pets2(data: Dict[str, Dict[str, int]], guids):
    new_data = {}
    for tguid, sources in data.items():
        name = guids[tguid]["name"]
        q = new_data.setdefault(name, {})
        for sguid, value in sources.items():
            sguid = check_master(sguid, guids)
            q[sguid] = q.get(sguid, 0) + value
    return new_data

@constants.running_time
def parse_dmg_taken_single(logs: List[str], filter_guid) -> Dict[str, Dict[str, int]]:
    '''damage_taken = {source_guid: {target_guid: value}}'''
    dmg = {}
    for line in logs:
        if "_DAMAGE," in line:
        # if "_DAMAGE," in line and filter_guid in line:
            if ',SW' in line:
                _, _, sguid, _, tguid, _, d, ok, _ = line.split(',', 8)
            else:
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

@constants.running_time
def parse_dmg_taken(logs: List[str], filter_guids) -> Dict[str, Dict[str, int]]:
    '''damage_taken = {source_guid: {target_guid: value}}'''
    dmg = {}
    for line in logs:
        if "_DAMAGE," in line:
        # if "_DAMAGE," in line and filter_guid in line:
            if ',SW' in line:
                _, _, sguid, _, tguid, _, d, ok, _ = line.split(',', 8)
            else:
                _, _, sguid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
            # if filter_guid not in tguid:
            # if '0xF150008F01' in tguid:
            #     print(tguid)
            if tguid not in filter_guids:
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

DMG_FLAGS = {'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'ENVIRONMENTAL_DAMAGE', 'DAMAGE_SPLIT'}
# DMG_FLAGS = {'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}

@constants.running_time
def dmg_taken_fast(logs: List[str], filter_guid: str) -> Dict[str, int]:
    dmg = {}
    for line in logs:
        if line[-3:] != 'nil':
            continue
        if filter_guid not in line:
            continue
        if "_HE" in line:
            continue
        line = line.split(',')
        guid = line[4]
        if filter_guid not in guid:
            continue
        i = 6 if line[1] == "SWING_DAMAGE" else 9
        v = int(line[i]) - int(line[i+1])
        try:
            dmg[guid] += v
        except KeyError:
            dmg[guid] = v
    return dmg

@constants.running_time
def dmg_taken_fast(logs: List[str], filter_guid: str) -> Dict[str, int]:
    dmg = {}
    for line in logs:
        if filter_guid not in line:
            continue
        if "_HE" in line:
            continue
        if line[-4:] != ',nil':
            continue
        line = line.split(',')
        target_guid = line[4]
        if filter_guid not in target_guid:
            continue
        i = 6 if line[1] == "SWING_DAMAGE" else 9
        v = int(line[i]) - int(line[i+1])
        try:
            dmg[target_guid] += v
        except KeyError:
            dmg[target_guid] = v
    return dmg

@constants.running_time
def dmg_taken_guid(logs: List[str], filter_guid: str) -> Dict[str, int]:
    dmg = 0
    for line in logs:
        if filter_guid not in line:
            continue
        if "_HE" in line:
            continue
        if line[-3:] != 'nil':
            continue
        line = line.split(',')
        if line[4] != filter_guid :
            continue
        i = 6 if line[1] == "SWING_DAMAGE" else 9
        dmg += int(line[i])
    return dmg

def main_dmg_taken_test_add_pets(data, guids):
    new_dmg = {}
    for guid, value in data:
        name = guids[guid]['name']
        try:
            new_dmg[name] += value
        except KeyError:
            new_dmg[name] = value

    return sort_dict_by_value(new_dmg)


def main_dmg_taken_test(report):
    logs = report.get_logs()
    guids, _ = report.get_guids()
    enc_data = report.get_enc_data()
    s1, f1 = enc_data['the_lich_king'][0]
    s2, f2 = enc_data['the_lich_king'][-1]
    logs_slice = logs[s1:f2]
    lk = "0xF130008EF500020C"
    raging = "0xF130008F5D000285"
    wicked_spirit = "0xF130009916001380"
    all_dmg = {}
    for guid in [lk, raging, wicked_spirit]:
        filter_guid = guid[:12]
        dmg = parse_dmg_taken(logs_slice, filter_guid)
        dmg = add_pets3(dmg, guids)
        dmg = sort_dict_by_value(dmg)
        for guid, value in dmg:
            # print(f"{name:<32}{value:>12}")
            all_dmg[guid] = all_dmg.get(guid, 0) + value
    for s,f in enc_data['the_lich_king']:
        logs_slice = logs[s:f]
        valks_overkill, valks_usefull = valks.get_valks_dmg(logs_slice, guids)
        dmg = sort_dict_by_value(valks_usefull)
        for guid, value in dmg:
            all_dmg[guid] = all_dmg.get(guid, 0) + value
    all_dmg = sort_dict_by_value(all_dmg)
    new_dmg = main_dmg_taken_test_add_pets(all_dmg, guids)
    for name, value in new_dmg:
        print(f"{name:<32}{value:>12}")


def main_dmg_taken_test(report):
    logs = report.get_logs()
    guids, _ = report.get_guids()
    logs_slice = logs
    filter_guid = "0xF13"
    dmg = parse_dmg_taken(logs_slice, filter_guid)
    # print(dmg.keys())
    dmg = add_pets2(dmg, guids)
    q = dmg['Gas Cloud']
    q = sort_dict_by_value(q)
    for guid, value in q:
    # dmg = add_pets3(dmg, guids)
    # dmg = sort_dict_by_value(dmg)
    # for guid, value in dmg:
    #     all_dmg[guid] = all_dmg.get(guid, 0) + value
    # all_dmg = sort_dict_by_value(all_dmg)
    # new_dmg = main_dmg_taken_test_add_pets(all_dmg, guids)
    # for name, value in new_dmg:
        name = guids[guid]['name']
        print(f"{name:<32}{value:>12}")


if __name__ == "__main__":
    import _main
    name = '21-07-30--19-42--Jenbrezul'
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    n = 'Festergut'
    filter_guid = report.name_to_guid(n)
    assert filter_guid is not None
    d = dmg_taken_fast(logs, filter_guid)
    print(d)