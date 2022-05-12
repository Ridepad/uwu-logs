from typing import Dict, List, Set

def checkdks(logs: List[str]):
    # 50526 = Wandering Plague
    return {
        line.split(',')[2]
        for line in logs
        if '50526' in line and '0x20' in line and 'SPELL_' in line
    }

def find_solo_dk(boss, logs):
    for s,f in boss:
        logs_slice = logs[s:f]
        dks = checkdks(logs_slice)
        if len(dks) != 1:
            continue
        return dks.pop()

def update_dk_pet_owners(everything, dk_guid, pet_guid):
    dk_name = everything[dk_guid]['name']
    p = {'name': 'Ghoul', 'master_name': dk_name, 'master_guid': dk_guid}
    guid_id = pet_guid[6:12]

    for every_guid in everything:
        if guid_id in every_guid:
            everything[every_guid] = p
            print('Updated owner:', every_guid)

def pet_owners(pets, everything) -> Dict[str, str]:
    d = {}
    for guid in pets:
        master = everything[guid].get('master_guid')
        if master:
            d[guid] = master
    return d

def get_boss_data(tguid, everything, enc_data):
    target_name = everything[tguid]['name']
    return enc_data.get(target_name)

def same_pet_ids(pets: Set[str], pets_tmp: Set[str]):
    if len(pets) != len(pets_tmp):
        return False
    pets = {x[6:12] for x in pets}
    pets_tmp = {x[6:12] for x in pets_tmp}
    return pets == pets_tmp

def remove_parsed_pets(targets, pets):
    for tguid, pets_tmp in dict(targets).items():
        if same_pet_ids(pets, pets_tmp):
            del targets[tguid]

def sort_by_target(data: Dict[str, Set[str]]):
    new: Dict[str, Set[str]] = {}
    for guid, targets in data.items():
        for tguid in targets:
            new.setdefault(tguid, set()).add(guid)
    return new

def missing_targets_f(data):
    return {y for x in data.values() for y in x}

def apply_owner(pairs, everything):
    for guid_id, dk_guid in pairs.items():
        dk_name = everything[dk_guid]['name']
        for guid, p in everything.items():
            if guid_id in guid:
                p['master_name'] = dk_name
                p['master_guid'] = dk_guid
                print('FOUND OWNER:', p['name'], dk_name, guid, dk_guid)

def remove_from_missing(missing, guid_id):
    return {guid:targets for guid, targets in missing.items() if guid_id not in guid}

def missing_dk_pets(pets_data, unholy_DK_pets):
    return {
        guid: v
        for guid, v in unholy_DK_pets.items()
        if guid not in pets_data
    }

def filter_pets_by_combat(targets: Dict[str, Set[str]], everything, enc_data, logs):
    for tguid, pets in targets.items():
        if not pets:
            continue
        boss = get_boss_data(tguid, everything, enc_data)
        if not boss:
            # print(tguid, pets)
            continue
        if len(pets) == 1:
            dk_guid = find_solo_dk(boss, logs)
            if not dk_guid:
                print('ERROR in udk_bullshit: not dk_guid')
                continue
            pet_guid = list(pets)[0]
            update_dk_pet_owners(everything, dk_guid, pet_guid)
            remove_parsed_pets(targets, pets)
            return
        owners = pet_owners(pets, everything)
        pets_tmp = pets - set(owners)
        if len(pets_tmp) != 1:
            print(owners)
            continue
        for s,f in boss:
            logs_slice = logs[s:f]
            dks = checkdks(logs_slice) - set(owners.values())
            if len(dks) != 1:
                print('ERROR in udk_bullshit: len(dks) != 1')
                print(dks)
                print(owners)
                print(pets)
                continue
            pet_guid = pets_tmp.pop()
            dk_guid = dks.pop()
            update_dk_pet_owners(everything, dk_guid, pet_guid)
            remove_parsed_pets(targets, pets)
            return

def get_missing_targets(pets_data, unholy_DK_pets):
    missing = missing_dk_pets(pets_data, unholy_DK_pets)
    missing_targets = missing_targets_f(missing)
    targets = sort_by_target(unholy_DK_pets)
    targets = {x:y for x,y in targets.items() if x in missing_targets}
    return targets
