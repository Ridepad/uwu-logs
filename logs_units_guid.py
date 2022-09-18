from collections import defaultdict

import logs_udk_bullshit2
from constants import (
    CLASS_FROM_HTML, LOGGER_REPORTS, SPELL_BOOK,
    running_time, sort_dict_by_value)

CLASSES = list(CLASS_FROM_HTML)
_prefix = [
    "Bat", "Blight", "Bone", "Brain", "Carrion", "Casket", "Corpse", "Crypt", "Dirt", "Earth", "Eye", "Grave", "Gravel", "Hammer",
    "Limb", "Marrow", "Pebble", "Plague", "Rat", "Rib", "Root", "Rot", "Skull", "Spine", "Stone", "Tomb", "Worm"]
_suffix = [
    "basher", "breaker", "catcher", "chewer", "chomp", "cruncher", "drinker", "feeder", "flayer", "gnaw", "gobbler", "grinder",
    "keeper", "leaper", "masher", "muncher", "ravager", "rawler", "ripper", "rumbler", "slicer", "stalker", "stealer", "thief"]
GHOUL_NAMES = {f"{x}{y}" for x in _prefix for y in _suffix}
TEMP_DK_PETS = {
    "005E8F", # Army of the Dead Ghoul
    "00660D", # Risen Ghoul
    "007616", # Risen Ally
}

NIL_GUID = "0x0000000000000000"
FLAG_SKIP = {"PARTY_KILL", "UNIT_DIED"}
NAMES_SKIP = {"nil", "Unknown"}
PET_FILTER_SPELLS = {
    "43771", # Well Fed

    "34952", # Go for the Throat (Rank 1)
    "34953", # Go for the Throat (Rank 2)
    "53434", # Call of the Wild
    "48990", # Mend Pet
    "70728", # Exploit Weakness
    "1539", # Feed Pet
    "70893", # Culling the Herd
    "64495", # Furious Howl
    "54216", # Master's Call

    "63560", # Ghoul Frenzy

    "35706", # Master Demonologist
    "35696", # Demonic Knowledge
    "25228", # Soul Link
    "54181", # Fel Synergy
    "32553", # Life Tap
    "70840", # Devious Minds
    "755", # Health Funnel (Rank 1)
    "3698", # Health Funnel (Rank 2)
    "3699", # Health Funnel (Rank 3)
    "3700", # Health Funnel (Rank 4)
    "11693", # Health Funnel (Rank 5)
    "11694", # Health Funnel (Rank 6)
    "11695", # Health Funnel (Rank 7)
    "27259", # Health Funnel (Rank 8)
    "47856", # Health Funnel (Rank 9)
    "16569", # Health Funnel?
    "60829", # Health Funnel?
}

BOSS_PETS = {
    "008F0B": "008F04", # Bone Spike
    # "0008F4": "008F04", # Coldflame
    # "00954E": "008FF7", # Vengeful Shade
    # "009765": "008EF5", # Defile
    "009513": "009443", # Swarming Shadows
    # "008809": "0087DC", # Nether Portal
    # "0087FD": "0087DC", # Infernal Volcano
    "009EE9": "009BB7", # Living Inferno
    "009EEB": "009BB7", # Living Ember
    "008170": "008208", # Guardian of Yogg-Saron
    "00823F": "00820D", # XS-013 Scrapbot
    "008242": "00820D", # XE-321 Boombot
    "008240": "00820D", # XM-024 Pummeller
    # "0xF1300084D4000832": "00820D", # Life Spark
    # "0xF1300084D1000833": "00820D", # Void Zone
    "00826B": "00808A", # Writhing Lasher'
    "0085E3": "00808A", # Ward of Life'
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

    def get_owner(pet_guids):
        owners = defaultdict(int)
        for pet in pet_guids:
            owner_guid = pets_data.get(pet, {}).get('master_guid')
            owners[owner_guid] += 1
        
        owners.pop(None, None)
        if owners:
            owners = sort_dict_by_value(owners)
            return list(owners)[0]
    
    missing_owner = []
    sorted_pets_raw = pet_sort_by_id(pets_raw)
    for guid_id, pet_guids in sorted_pets_raw.items():
        master_guid = get_owner(pet_guids)
        if not master_guid:
            missing_owner.append(guid_id)
            continue
        if master_guid not in everything:
            continue
        master_name = everything[master_guid]['name']
        pet_name = get_pet_name(guid_id)
        _pet = new_entry(pet_name, master_name, master_guid)
        for pet_guid in pet_guids:
            everything[pet_guid] = _pet

    return missing_owner

@running_time
def logs_parser(logs: list[str]): # sourcery no-metrics
    everything: dict[str, dict[str, str]] = {}
    pets_perma: dict[str, dict[str, str]] = {}
    unholy_DK_pets: defaultdict[str, set[str]] = defaultdict(set)

    temp_pets: dict[str, dict[str, str]] = {}
    pets_perma_all: set[str] = set()
    last_abom = {}

    players = {}
    players_classes = {}
    players_skip = set()

    for line in logs:
        _, flag, sGUID, sName, tGUID, tName, *other = line.split(',', 8)

        if sName == 'Unknown' or tName in NAMES_SKIP:
            continue

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
            elif other[0] in SPELL_BOOK:
                players[sGUID] = sName
                spell_info = SPELL_BOOK[other[0]]
                players_classes[sGUID] = CLASSES[spell_info[0]]
                players_skip.add(sGUID)

        if spell_id == "47468":
            # Claw
            if sGUID[6:-6] not in TEMP_DK_PETS and tGUID[:4] == "0xF1":
                unholy_DK_pets[sGUID].add(tGUID)
                if sName not in GHOUL_NAMES:
                    LOGGER_REPORTS.debug(f"sName not in GHOUL_NAMES {sName}")

        elif flag == "SPELL_SUMMON":
            if tGUID[6:-6] in BOSS_PETS:
                continue
            if is_perma_pet(tGUID):
                pets_perma[tGUID] = new_entry(tName, sName, sGUID)
                pets_perma_all.add(tGUID)
            elif sGUID != tGUID:
                temp_pets[tGUID] = new_entry(tName, sName, sGUID)

        elif spell_id in PET_FILTER_SPELLS:
            if sGUID == tGUID:
                if is_perma_pet(sGUID):
                    pets_perma_all.add(sGUID)
            
            elif is_player(sGUID):
                guids_entry = new_entry(tName, sName, sGUID)
                if is_perma_pet(tGUID):
                    pets_perma[tGUID] = guids_entry
                    pets_perma_all.add(tGUID)
                else:
                    temp_pets[tGUID] = guids_entry
            
            elif is_player(tGUID):
                guids_entry = new_entry(sName, tName, tGUID)
                if is_perma_pet(sGUID):
                    pets_perma[sGUID] = guids_entry
                    pets_perma_all.add(sGUID)
                else:
                    temp_pets[sGUID] = guids_entry

        elif spell_id == "34650":
            # Mana Leech
            temp_pets[sGUID] = new_entry("Shadowfiend", tName, tGUID)

        elif spell_id == "70308":
            # Mutated Transformation
            last_abom = new_entry("Mutated Abomination", sName, sGUID)

        elif last_abom and sGUID == tGUID and sGUID[6:-6] == "00958D":
            # Mutated Abomination
            temp_pets[sGUID] = last_abom
            last_abom = {}

        elif is_perma_pet(sGUID):
            pets_perma_all.add(sGUID)

    everything |= temp_pets
    for guid, name in players.items():
        everything[guid] = {'name': name}

    missing_owner = add_missing_pets(everything, pets_perma, pets_perma_all)
    return {
        "everything": everything,
        "players": dict(sorted(players.items())),
        "classes": dict(sorted(players_classes.items())),
        "pets_perma": pets_perma,
        "unholy_DK_pets": unholy_DK_pets,
        "missing_owner": missing_owner,
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
