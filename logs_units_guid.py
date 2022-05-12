from collections import defaultdict
import os

import _main
import constants
import logs_udk_bullshit2

_prefix = [
    'Bat', 'Blight', 'Bone', 'Brain', 'Carrion', 'Casket', 'Corpse', 'Crypt', 'Dirt', 'Earth', 'Eye', 'Grave', 'Gravel', 'Hammer',
    'Limb', 'Marrow', 'Pebble', 'Plague', 'Rat', 'Rib', 'Root', 'Rot', 'Skull', 'Spine', 'Stone', 'Tomb', 'Worm']
_suffix = [
    'basher', 'breaker', 'catcher', 'chewer', 'chomp', 'cruncher', 'drinker', 'feeder', 'flayer', 'gnaw', 'gobbler', 'grinder',
    'keeper', 'leaper', 'masher', 'muncher', 'ravager', 'rawler', 'ripper', 'rumbler', 'slicer', 'stalker', 'stealer', 'thief']
GHOUL_NAMES = {f"{x}{y}" for x in _prefix for y in _suffix}
BASE_DK_PETS = {'Army of the Dead Ghoul', 'Risen Ghoul', 'Risen Ally'}

SKIP = {'PARTY_KILL', 'UNIT_DIED'}
PET_FILTER_SPELLS = {
    '34952', # Go for the Throat
    '70840', # Devious Minds
}
WARLOCK_SPELLS = {
    '35706', # Master Demonologist
    '25228', # Soul Link
    '54181', # Fel Synergy
}

BOSS_PETS = {
    '008F0B': '008F04', # Bone Spike
    # '0008F4': '008F04', # Coldflame
    # '00954E': '008FF7', # Vengeful Shade
    '009765': '008EF5', # Defile
    '009513': '009443', # Swarming Shadows
    # '008809': '0087DC', # Nether Portal
    # '0087FD': '0087DC', # Infernal Volcano
}

def pet_sort_by_id(pets_raw):
    d: dict[str, set[str]] = {}
    for guid in pets_raw:
        if '0xF14' in guid:
            d.setdefault(guid[6:-6], set()).add(guid)
    return d


def new_entry(name: str, master_name: str, master_guid: str):
    return {
        'name': name,
        'master_name': master_name,
        'master_guid': master_guid
    }

def add_missing_pets(everything: dict[str, str], pets_data: dict[str, dict[str, str]], pets_raw: set[str]):
    def get_pet_name(guid_id):
        for guid in everything:
            if guid_id in guid:
                return everything[guid]['name']

    sorted_pets_raw = pet_sort_by_id(pets_raw)
    for guid_id, pet_guids in sorted_pets_raw.items():
        q = [pets_data[pet].get('master_guid') for pet in pet_guids]
        q = [x for x in q if x]
        master_guid = max(q, key=q.count)
        master_name = everything[master_guid]['name']
        pet_name = get_pet_name(guid_id)
        _pet = new_entry(pet_name, master_name, master_guid)
        for pet_guid in pet_guids:
            everything[pet_guid] = _pet

@constants.running_time
def logs_parser(logs: list[str]): # sourcery no-metrics
    everything: dict[str, dict[str, str]] = {}
    pets_data: dict[str, dict[str, str]] = {}
    unholy_DK_pets: dict[str, set[str]] = {}

    temp_pets: dict[str, dict[str, str]] = {}
    pets_raw: set[str] = set()
    last_abom = {}

    _dk_missing_ghoul_names = set()

    for line in logs:
        timestamp, flag, sGUID, sName, tGUID, tName, *other = line.split(',', 7)
        # timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')

        if flag in SKIP or \
            sName == 'Unknown' or \
            tName == 'Unknown' or \
            tName == 'nil':
            continue

        if sGUID not in everything:
            everything[sGUID] = {'name': sName}
        elif tGUID not in everything:
            everything[tGUID] = {'name': tName}
        if sGUID == "0x06000000005AA270" or tGUID == "0x06000000005AA270":
            print(sName, tName)
        # spell_id = other.split(',', 1)[0]
        spell_id = other[0]

        if (
            sName in GHOUL_NAMES
            and "0xF14" in sGUID
            or spell_id == '47468'
            and sName not in BASE_DK_PETS
        ) and sGUID != tGUID:  
            unholy_DK_pets.setdefault(sGUID, set()).add(tGUID)
            if sName not in GHOUL_NAMES:
                _dk_missing_ghoul_names.add(sName)

        elif spell_id == '43771' and sGUID != tGUID:
            pets_raw.add(tGUID)
            if tGUID not in pets_data:
                pets_data[tGUID] = new_entry(tName, sName, sGUID)

        elif spell_id in PET_FILTER_SPELLS and '0x06' in sGUID or flag == 'SPELL_SUMMON' and tGUID[6:-6] not in BOSS_PETS:
            if '0xF14' in tGUID:
                pets_data[tGUID] = new_entry(tName, sName, sGUID)
                pets_raw.add(tGUID)
            elif sGUID != tGUID:
                temp_pets[tGUID] = new_entry(tName, sName, sGUID)
        
        elif spell_id == "34650": # Mana Leech
            temp_pets[sGUID] = new_entry('Shadowfiend', tName, tGUID)

        elif spell_id in WARLOCK_SPELLS and '0x06' in sGUID and sGUID != tGUID:
            pets_data[sGUID] = new_entry(sName, tName, tGUID)
            pets_raw.add(sGUID)
        
        elif spell_id == '70308': # Mutated Transformation
            last_abom = new_entry('Mutated Abomination', sName, sGUID)
        
        elif last_abom and sGUID[6:-6] == '00958D' and tGUID[6:-6] == '00958D':
            # Mutated Abomination
            temp_pets[sGUID] = last_abom
            last_abom = {}

    everything.update(temp_pets)
    add_missing_pets(everything, pets_data, pets_raw)
    
    for name in _dk_missing_ghoul_names:
        print(f"=============== {name} ==============")

    return everything, pets_data, unholy_DK_pets

def convert_masters(data: dict[str, dict[str, str]]):
    for p in data.values():
        master_guid = p.get('master_guid')
        if not master_guid:
            continue
        master_master_guid = data.get(master_guid, {}).get('master_guid')
        if not master_master_guid:
            continue
        p['master_guid'] = master_master_guid
        p['master_name'] = data[master_master_guid]['name']


def get_all_players(everything: dict[str, str]):
    players: dict[str, str] = {}
    for guid, properties in everything.items():
        if guid[:4] == "0x06":
            name = properties['name']
            players[guid] = name
            everything[guid] = {'name': name}
    return players

@constants.running_time
def prune_players(logs: list[str], everything):
    p = defaultdict(int)
    players_names = {}
    for line in logs:
        if '0x06' not in line:
            continue
        _line = line.split(',', 4)
        # _, _, sGUID, sName, _ = line.split(',', 4)
        # _, _, sGUID, _ = line.split(',', 3)
        if _line[2].startswith('0x06'):
            players_names[_line[2]] = _line[3]
            p[_line[2]] += 1
    
    players: dict[str, str] = {}
    for guid, v in p.items():
        # print(f"{players_names[guid]:>12} {guid}")
        name = players_names[guid]
        everything[guid] = {'name': name}
        if v > 500: #  or guid not in everything:
            players[guid] = name
    
    return dict(sorted(players.items()))

def guids_main(logs, enc_data):
    everything, pets_data, unholy_DK_pets = logs_parser(logs)
    __qq = logs_udk_bullshit2.UDK_BULLSHIT(logs, everything, enc_data, pets_data, unholy_DK_pets)
    __qq.get_missing_targets()
    missing_targets_cached = dict(__qq.missing_targets)
    for n in range(5):
        __qq.filter_pets_by_combat()
        if __qq.missing_targets == missing_targets_cached:
            break
        print('filter_pets_by_combat Loop:', n+2)
        missing_targets_cached = dict(__qq.missing_targets)
    convert_masters(everything)
    players = prune_players(logs, everything)
    # players = get_players(everything)
    return everything, players

def __main(name):
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    return guids_main(logs, enc_data)


def __redo(name):
    print(name)
    everything, players = __main(name)
    pth = f"LogsDir/{name}"
    constants.json_write(f"{pth}/GUIDS_DATA", everything)
    constants.json_write(f"{pth}/PLAYERS_DATA", players)


def __redo_all(startfrom=None, end=None):
    import os
    from multiprocessing import Pool
    folders = next(os.walk('LogsDir/'))[1]
    if startfrom:
        folders = folders[folders.index(startfrom):]
    if end:
        folders = folders[:folders.index(end)]
    for x in folders:
        __redo(x)
    # with Pool(4) as p:
        # p.map(__redo, folders)

if __name__ == "__main__":
    # __redo_all("22-01-26--20-58--Safiyah")
    __redo('21-12-12--20-54--Nomadra')
