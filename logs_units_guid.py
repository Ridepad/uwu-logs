from collections import defaultdict

import logs_udk_bullshit2
from constants import CLASS_FROM_HTML, LOGGER_LOGS, SPELL_BOOK, running_time

CLASSES = list(CLASS_FROM_HTML)
_prefix = [
    'Bat', 'Blight', 'Bone', 'Brain', 'Carrion', 'Casket', 'Corpse', 'Crypt', 'Dirt', 'Earth', 'Eye', 'Grave', 'Gravel', 'Hammer',
    'Limb', 'Marrow', 'Pebble', 'Plague', 'Rat', 'Rib', 'Root', 'Rot', 'Skull', 'Spine', 'Stone', 'Tomb', 'Worm']
_suffix = [
    'basher', 'breaker', 'catcher', 'chewer', 'chomp', 'cruncher', 'drinker', 'feeder', 'flayer', 'gnaw', 'gobbler', 'grinder',
    'keeper', 'leaper', 'masher', 'muncher', 'ravager', 'rawler', 'ripper', 'rumbler', 'slicer', 'stalker', 'stealer', 'thief']
GHOUL_NAMES = {f"{x}{y}" for x in _prefix for y in _suffix}
TEMP_DK_PETS = {
    "005E8F", # Army of the Dead Ghoul
    "00660D", # Risen Ghoul
    "007616", # Risen Ally
}

NIL_GUID = '0x0000000000000000'
FLAG_SKIP = {'PARTY_KILL', 'UNIT_DIED'}
NAMES_SKIP = {'nil', 'Unknown'}
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


def is_player(guid):
    return guid[:3] == "0x0"

def is_perma_pet(guid):
    return guid[:5] == "0xF14"


def pet_sort_by_id(pets_raw):
    d: dict[str, set[str]] = {}
    for guid in pets_raw:
        if is_perma_pet(guid):
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

@running_time
def logs_parser(logs: list[str]): # sourcery no-metrics
    everything: dict[str, dict[str, str]] = {}
    pets_perma: dict[str, dict[str, str]] = {}
    unholy_DK_pets: defaultdict[str, set[str]] = defaultdict(set)

    temp_pets: dict[str, dict[str, str]] = {}
    pets_raw: set[str] = set()
    last_abom = {}

    # players_seen = defaultdict(int)
    # players_names = {}
    players_classes = {}
    players = {}
    players_skip = set()
    _spells = set()
    # _players_spells = {}

    for line in logs:
        _, flag, sGUID, sName, tGUID, tName, *other = line.split(',', 8)

        if flag in FLAG_SKIP or sName == 'Unknown' or tName in NAMES_SKIP:
            continue
        # if sGUID == "0x06000000004F9A9C":
        #     print(line)
        if sGUID not in everything:
            everything[sGUID] = {'name': sName}
        elif tGUID not in everything:
            everything[tGUID] = {'name': tName}

        try:
            spell_id = other[0]
        except IndexError:
            continue

        if sGUID not in players_skip:
            if not is_player(sGUID):
                players_skip.add(sGUID)
            else:
                # print(other)
                # spellname = other[1].split(',', 1)[0]
                if other[0] in SPELL_BOOK:
                    # if sGUID == "0x060000000004B154":
                    #     print(sName, other)
                    players[sGUID] = sName
                    spell_info = SPELL_BOOK[other[0]]
                    players_classes[sGUID] = CLASSES[spell_info[0]]
                    players_skip.add(sGUID)
                if sGUID == "0x06000000004F8377":
                    _spells.add((other[0], other[1]))
                    # _players_spells[other[0]] = other[1]

        if spell_id == '47468':
            if sGUID[6:-6] not in TEMP_DK_PETS and tGUID[:4] == "0xF1":
            # if sName not in BASE_DK_PETS and tGUID[:4] == "0xF1":
                unholy_DK_pets[sGUID].add(tGUID)
                if sName not in GHOUL_NAMES:
                    LOGGER_LOGS.debug(f'sName not in GHOUL_NAMES {sName}')

        elif spell_id == '43771':
            if sGUID != tGUID and tGUID not in pets_perma:
                pets_perma[tGUID] = new_entry(tName, sName, sGUID)
                pets_raw.add(tGUID)

        elif (spell_id in PET_FILTER_SPELLS and is_player(sGUID)
        or flag == 'SPELL_SUMMON' and tGUID[6:-6] not in BOSS_PETS):
            if is_perma_pet(tGUID):
                pets_perma[tGUID] = new_entry(tName, sName, sGUID)
                pets_raw.add(tGUID)
            elif sGUID != tGUID:
                temp_pets[tGUID] = new_entry(tName, sName, sGUID)

        elif spell_id in WARLOCK_SPELLS:
            if is_player(sGUID) and sGUID != tGUID:
                pets_perma[sGUID] = new_entry(sName, tName, tGUID)
                pets_raw.add(sGUID)

        elif spell_id == "34650": # Mana Leech
            temp_pets[sGUID] = new_entry('Shadowfiend', tName, tGUID)

        elif spell_id == '70308': # Mutated Transformation
            last_abom = new_entry('Mutated Abomination', sName, sGUID)

        elif last_abom and sGUID == tGUID and sGUID[6:-6] == '00958D': # Mutated Abomination
            temp_pets[sGUID] = last_abom
            last_abom = {}

    everything |= temp_pets
    for guid, name in players.items():
        everything[guid] = {'name': name}

    add_missing_pets(everything, pets_perma, pets_raw)
    print(_spells)
    return {
        "everything": everything,
        "players": dict(sorted(players.items())),
        "classes": dict(sorted(players_classes.items())),
        "pets_perma": pets_perma,
        "unholy_DK_pets": unholy_DK_pets,
    }

def convert_nested_masters(data: dict[str, dict[str, str]]):
    for p in data.values():
        if 'master_guid' not in p:
            continue
        master_guid = p['master_guid']
        master_master_guid = data.get(master_guid, {}).get('master_guid')
        if not master_master_guid:
            continue
        p['master_guid'] = master_master_guid
        p['master_name'] = data[master_master_guid]['name']

@running_time
def guids_main(logs, enc_data):
    parsed = logs_parser(logs)
    everything: dict[str, dict[str, str]] = parsed["everything"]

    missing_pets_targets = logs_udk_bullshit2.get_missing_targets(parsed["unholy_DK_pets"], parsed["pets_perma"])
    logs_udk_bullshit2.UDK_BULLSHIT(logs, everything, enc_data, missing_pets_targets)

    convert_nested_masters(everything)
    return parsed
