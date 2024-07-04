from collections import defaultdict

import logs_pet_bullshit
from c_player_classes import CLASS_FROM_HTML, SPELL_BOOK
from h_debug import Loggers, running_time
from h_other import sort_dict_by_value

LOGGER_REPORTS = Loggers.reports

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
FLAG_PET_AGGRO = {"SWING_DAMAGE", "SPELL_DAMAGE"}
NAMES_SKIP = {"nil", "Unknown"}
PET_FILTER_SPELLS = {
"43771", # Well Fed (Spiced Mammoth Treats)
"65247", # Well Fed (Kibler's Bits)

# from dk
"48743", # Death Pact
"51328", # Corpse Explosion
"63560", # Ghoul Frenzy

# from warlock
"25228", # Soul Link
"23720", # Blessing of the Black Book
"32553", # Life Tap
"32554", # Mana Feed - Drain Mana
"32752", # Summoning Disorientation
"54181", # Fel Synergy
"54607", # Soul Leech Mana
"59092", # Dark Pact
"70840", # Devious Minds
"755",   # Health Funnel 1
"3698",  # Health Funnel 2
"3699",  # Health Funnel 3
"3700",  # Health Funnel 4
"11693", # Health Funnel 5
"11694", # Health Funnel 6
"11695", # Health Funnel 7
"27259", # Health Funnel 8
"47856", # Health Funnel 9
"16569", # Health Funnel
"40671", # Health Funnel
"60829", # Health Funnel
# from pet
"35696", # Demonic Knowledge
"47283", # Empowered Imp
"7812",  # Sacrifice 1
"19438", # Sacrifice 2
"19440", # Sacrifice 3
"19441", # Sacrifice 4
"19442", # Sacrifice 5
"19443", # Sacrifice 6
"27273", # Sacrifice 7
"47985", # Sacrifice 8
"47986", # Sacrifice 9
# Imp
"23759", # Master Demonologist
"23826", # Master Demonologist
"23827", # Master Demonologist
"23828", # Master Demonologist
"23829", # Master Demonologist
# Voidwalker
"23760", # Master Demonologist
"23841", # Master Demonologist
"23842", # Master Demonologist
"23843", # Master Demonologist
"23844", # Master Demonologist
# Succubus
"23761", # Master Demonologist
"23833", # Master Demonologist
"23834", # Master Demonologist
"23835", # Master Demonologist
"23836", # Master Demonologist
# Felhunter
"23762", # Master Demonologist
"23837", # Master Demonologist
"23838", # Master Demonologist
"23839", # Master Demonologist
"23840", # Master Demonologist
# Felguard
"35702", # Master Demonologist
"35703", # Master Demonologist
"35704", # Master Demonologist
"35705", # Master Demonologist
"35706", # Master Demonologist

# from hunter
"1002", # Eyes of the Beast
"1539", # Feed Pet
"19574", # Bestial Wrath
"19577", # Intimidation
"34952", # Go for the Throat 1
"34953", # Go for the Throat 2
"61669", # Aspect of the Beast
"68130", # Greatness (4T9)
"70728", # Exploit Weakness
"136",   # Mend Pet 1
"3111",  # Mend Pet 2
"3661",  # Mend Pet 3
"3662",  # Mend Pet 4
"13542", # Mend Pet 5
"13543", # Mend Pet 6
"13544", # Mend Pet 7
"27046", # Mend Pet 8
"48989", # Mend Pet 9
"48990", # Mend Pet 10
"33976", # Mend Pet
# from pet
"53434", # Call of the Wild
"57475", # Kindred Spirits
"53412", # Invigoration
"53517", # Roar of Recovery
"70893", # Culling the Herd
"19579", # Spirit Bond 1
"24529", # Spirit Bond 2
"24604", # Furious Howl 1
"64491", # Furious Howl 2
"64492", # Furious Howl 3
"64493", # Furious Howl 4
"64494", # Furious Howl 5
"64495", # Furious Howl 6
}

BOSS_PETS = {
    "008F0B": "008F04", # Bone Spike
    "009738": "008F04", # Bone Spike
    "009737": "008F04", # Bone Spike
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


def pet_group_by_id(pets_raw):
    d: defaultdict[str, set[str]] = defaultdict(set)
    for guid in pets_raw:
        if is_perma_pet(guid):
            d[guid[6:-6]].add(guid)
    return d


def new_entry(name: str, master_name: str, master_guid: str):
    return {
        'name': name,
        'master_name': master_name,
        'master_guid': master_guid
    }

def add_missing_pets(everything: dict[str, str], pets_perma: dict[str, dict[str, str]], pets_perma_all: set[str]):
    def get_name(guid_id):
        for guid in everything:
            if guid[6:-6] == guid_id:
                return everything[guid]['name']

    def get_owner(pet_guids):
        owners = defaultdict(int)
        for pet_guid in pet_guids:
            if pet_guid not in pets_perma:
                continue
            owner_guid = pets_perma[pet_guid].get('master_guid')
            if owner_guid:
                owners[owner_guid] += 1
        
        if None in owners:
            del owners[None]

        if owners:
            owners = sort_dict_by_value(owners)
            return list(owners)[0]
    
    missing_owner = []
    pets_perma_all_groupped = pet_group_by_id(pets_perma_all)
    for guid_id, pet_guids in pets_perma_all_groupped.items():
        master_guid = get_owner(pet_guids)
        if not master_guid:
            missing_owner.append(guid_id)
            continue
        if master_guid not in everything:
            continue
        
        master_name = everything[master_guid]['name']
        pet_name = get_name(guid_id)
        _pet = new_entry(pet_name, master_name, master_guid)
        for pet_guid in pet_guids:
            everything[pet_guid] = _pet
            pets_perma[pet_guid] = _pet

    return missing_owner

@running_time
def logs_parser(logs: list[str]): # sourcery no-metrics
    everything: dict[str, dict[str, str]] = {}
    pets_perma: dict[str, dict[str, str]] = {}
    ghouls: defaultdict[str, set[str]] = defaultdict(set)
    felhunters: defaultdict[str, set[str]] = defaultdict(set)

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
            elif spell_id in SPELL_BOOK and flag != "SPELL_AURA_REMOVED":
                players[sGUID] = sName
                spell_info = SPELL_BOOK[spell_id]
                players_classes[sGUID] = CLASSES[spell_info[0]]
                players_skip.add(sGUID)
                LOGGER_REPORTS.info(f" NEW CLASS | {sName:12} | {line}")

        if spell_id == "47468": # Claw
            if sGUID[6:-6] not in TEMP_DK_PETS and tGUID[:4] == "0xF1":
                ghouls[sGUID].add(tGUID)
                if sName not in GHOUL_NAMES:
                    LOGGER_REPORTS.debug(f"sName not in GHOUL_NAMES {sName}")

        elif spell_id == "54053": # Shadow Bite
            if sGUID[:5] == "0xF14" and tGUID[:4] == "0xF1":
                felhunters[sGUID].add(tGUID)

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
                pet_info = new_entry(tName, sName, sGUID)
                if is_perma_pet(tGUID):
                    pets_perma[tGUID] = pet_info
                    pets_perma_all.add(tGUID)
                else:
                    temp_pets[tGUID] = pet_info
            
            elif is_player(tGUID):
                pet_info = new_entry(sName, tName, tGUID)
                if is_perma_pet(sGUID):
                    pets_perma[sGUID] = pet_info
                    pets_perma_all.add(sGUID)
                else:
                    temp_pets[sGUID] = pet_info

        elif spell_id == "34650": # Mana Leech
            temp_pets[sGUID] = new_entry("Shadowfiend", tName, tGUID)

        elif spell_id == "70308": # Mutated Transformation
            last_abom = new_entry("Mutated Abomination", sName, sGUID)

        elif last_abom and sGUID == tGUID and sGUID[6:-6] == "00958D": # Mutated Abomination
            temp_pets[sGUID] = last_abom
            last_abom = {}

        elif is_perma_pet(sGUID) and flag in FLAG_PET_AGGRO:
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
        "Ghoul": ghouls,
        "Felhunter": felhunters,
        "missing_owner": missing_owner,
    }

def convert_nested_masters(data: dict[str, dict[str, str]]):
    for unit_info in data.values():
        if 'master_guid' not in unit_info:
            continue
        
        master_info = data.get(unit_info['master_guid'])
        if not master_info:
            continue
        
        master_master_guid = master_info.get('master_guid')
        if not master_master_guid:
            continue
        
        unit_info['master_guid'] = master_master_guid
        unit_info['master_name'] = data[master_master_guid]['name']

@running_time
def guids_main(logs, enc_data):
    parsed = logs_parser(logs)
    logs_pet_bullshit.PET_BULLSHIT(logs, enc_data, parsed, "Unholy")
    logs_pet_bullshit.PET_BULLSHIT(logs, enc_data, parsed, "Affliction")

    convert_nested_masters(parsed["everything"])
    return parsed
