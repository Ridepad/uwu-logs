from collections import defaultdict

from constants import TOC_CHAMPIONS, is_player, running_time

VALK_HALF_HP = 2992500 // 2
TOC_CHAMPIONS_USEFUL = {f"0xF130{guid}": name for guid, name in TOC_CHAMPIONS.items()}
TOC_PETS = {
    "0xF130008B1A": "Cat",
    "0xF130008A89": "Demon",
    "0xF130008CE6": "Treants",
}

USEFUL = {
    "Lord Marrowgar": {
        "0xF130008F04": "Lord Marrowgar",
        "0xF150008F0B": "Bone Spike",
    },
    "Lady Deathwhisper": {
        "0xF130008FF7": "Lady Deathwhisper",
        "0xF130009402": "Cult Fanatic",
        "0xF13000943D": "Cult Adherent",
        "0xF130009655": "Darnavan",
    },
    "Gunship": {
        "0xF1300090FC": "Skybreaker Sorcerer",
        "0xF1300090FD": "Kor'kron Battle-Mage",
    },
    "Deathbringer Saurfang": {
        "0xF1500093B5": "Deathbringer Saurfang",
        "0xF13000966C": "Blood Beast",
    },
    "Festergut": {
        "0xF130008F12": "Festergut",
    },
    "Rotface": {
        "0xF130008F13": "Rotface",
    },
    "Professor Putricide": {
        "0xF150008F46": "Professor Putricide",
        "0xF1300092BA": "Gas Cloud",
        "0xF130009341": "Volatile Ooze",
    },
    "Blood Prince Council": {
        "0xF130009455": "Prince Taldaram",
        "0xF130009452": "Prince Valanar",
        "0xF130009454": "Prince Keleseth",
    },
    "Blood-Queen Lana'thel": {
        "0xF130009443": "Blood-Queen Lana'thel",
    },
    "Valithria Dreamwalker": {
        "0xF130009413": "Rot Worm",
        "0xF1300093FE": "Gluttonous Abomination",
        "0xF1300093EC": "Risen Archmage",
        "0xF1300093E7": "Suppresser",
        "0xF13000942E": "Blistering Zombie",
        "0xF130008FB7": "Blazing Skeleton",
    },
    "Sindragosa": {
        "0xF130008FF5": "Sindragosa",
        "0xF130009074": "Ice Tomb",
    },
    "The Lich King": {
        "0xF130008EF5": "The Lich King",
        "0xF130008F19": "Ice Sphere",
        "0xF130008F5D": "Raging Spirit",
        "0xF130009916": "Wicked Spirit",
    },
    "Baltharus the Warborn": {
        "0xF130009B47": "Baltharus the Warborn",
    },
    "Saviana Ragefire": {
        "0xF130009B43": "Saviana Ragefire",
    },
    "General Zarithrian": {
        "0xF130009B42": "General Zarithrian",
    },
    "Halion": {
        "0xF130009BB7": "Halion",
        "0xF130009CCE": "Halion",
        "0xF130009EE9": "Living Inferno",
    },
    "Northrend Beasts": {
        "0xF1500087EC": "Gormok the Impaler",
        "0xF1300087EF": "Dreadscale",
        "0xF130008948": "Acidmaw",
        "0xF1300087ED": "Icehowl",
    },
    "Lord Jaraxxus": {
        "0xF1300087DC": "Lord Jaraxxus",
        "0xF1300087FD": "Infernal Volcano",
        "0xF130008809": "Nether Portal",
    },
    "Faction Champions": TOC_CHAMPIONS_USEFUL,
    "Twin Val'kyr": {
        "0xF1300086C0": "Eydis Darkbane",
        "0xF1300086C1": "Fjola Lightbane",
    },
    "Anub'arak": {
        "0xF130008704": "Anub'arak",
        "0xF13000872D": "Swarm Scarab",
    },
    "Toravon the Ice Watcher": {
        "0xF130009621": "Toravon the Ice Watcher",
        "0xF130009638": "Frozen Orb",
    },
    "Onyxia": {
        "0xF1300027C8": "Onyxia",
    },
    "Malygos": {
        "0xF1300070BB": "Malygos",
    },
    "Sartharion": {
        '0xF1300070BC': "Sartharion",
        '0xF1300076F4': "Tenebron",
        '0xF1300076F3': "Shadron",
        '0xF1300076F1': "Vesperon",
    },
}

ALL_GUIDS = {
    "Gunship": {
        "0xF1300090FC": "Skybreaker Sorcerer",
        "0xF1300090FD": "Kor'kron Battle-Mage",
        "0xF130009069": "Skybreaker Rifleman",
        "0xF130009068": "Kor'kron Axethrower",
        "0xF130009054": "Muradin Bronzebeard",
        "0xF13000904B": "High Overlord Saurfang",
        "0xF1300090A2": "Skybreaker Sorcerer",
        "0xF130009061": "Skybreaker Sergeant",
        "0xF130009056": "Skybreaker Marine",
        "0xF13000905D": "Kor'kron Reaver",
        "0xF130009060": "Kor'kron Sergeant",
        "0xF130009076": "Kor'kron Rocketeer",
    },
    "Rotface": {
        "0xF130008F13": "Rotface",
        "0xF130009023": "Big Ooze",
        "0xF130009021": "Little Ooze",
        # "0xF13000908E": "Sticky Ooze",
    },
    "Blood Prince Council": {
        "0xF130009452": "Prince Valanar",
        "0xF130009455": "Prince Taldaram",
        "0xF130009454": "Prince Keleseth",
        "0xF1300095E1": "Dark Nucleus",
        "0xF130009636": "Kinetic Bomb",
    },
    "Valithria Dreamwalker": {
        "0xF130008FB5": "Valithria Dreamwalker",
        "0xF130008FB7": "Blazing Skeleton",
        "0xF130009413": "Rot Worm",
        "0xF1300093E7": "Suppresser",
        "0xF1300093EC": "Risen Archmage",
        "0xF1300093FE": "Gluttonous Abomination",
        "0xF13000942E": "Blistering Zombie",
    },
    "The Lich King": {
        "0xF150008F01": "Val'kyr Shadowguard",
        "0xF130008EF5": "The Lich King",
        "0xF130008F5D": "Raging Spirit",
        "0xF130008F19": "Ice Sphere",
        "0xF130009916": "Wicked Spirit",
        "0xF13000933F": "Drudge Ghoul",
        "0xF130009342": "Shambling Horror",
        "0xF1300093A7": "Vile Spirit",
    },
    "Northrend Beasts": {
        "0xF1500087EC": "Gormok the Impaler",
        "0xF1300087EF": "Dreadscale",
        "0xF130008948": "Acidmaw",
        "0xF1300087ED": "Icehowl",
        "0xF1300087F0": "Snobold Vassal",
    },
    "Lord Jaraxxus": {
        "0xF1300087DC": "Lord Jaraxxus",
        "0xF1300087FD": "Infernal Volcano",
        "0xF130008809": "Nether Portal",
        "0xF15000880A": "Mistress of Pain",
        "0xF1300087FF": "Felflame Infernal",
    },
    "Faction Champions": TOC_CHAMPIONS_USEFUL | TOC_PETS,
    "Anub'arak": {
        "0xF130008704": "Anub'arak",
        "0xF13000872D": "Swarm Scarab",
        "0xF13000872F": "Nerubian Burrower",
        "0xF13000872E": "Frost Sphere",
    },
    "Baltharus the Warborn": {
        "0xF130009B47": "Baltharus the Warborn",
        "0xF130009BDB": "Baltharus the Copyborn",
    },
    "General Zarithrian": {
        "0xF130009B42": "General Zarithrian",
        "0xF130009B86": "Onyx Flamecaller"
    },
    "Halion": {
        "0xF130009BB7": "Halion",
        "0xF130009CCE": "Halion",
        "0xF130009EE9": "Living Inferno",
        "0xF130009EEB": "Living Ember",
    },
    "Sartharion": {
        '0xF1300070BC': "Sartharion",
        '0xF1300076F4': "Tenebron",
        '0xF1300076F3': "Shadron",
        '0xF1300076F1': "Vesperon",
        '0xF1300077B3': "Lava Blaze",
        '0xF1300079EE': "Sartharion Twilight Whelp",
        '0xF1300079F2': "Acolyte of Shadron",
        '0xF1300079F3': "Acolyte of Vesperon",
    },
    "Malygos": {
        "0xF1300070BB": "Malygos",
        "0xF130007584": "Power Spark",
    },
    "Onyxia": {
        "0xF1300027C8": "Onyxia",
        "0xF130002BFE": "Onyxian Whelp",
        "0xF130008ED1": "Onyxian Lair Guard",
    },
}

def get_all_targets(boss_name: str, boss_guid_id: str=None):
    if not boss_name:
        return {
            "useful": {},
            "all": {},
        }
    
    if boss_name in USEFUL:
        targets_useful = USEFUL[boss_name]
    elif boss_guid_id:
        targets_useful = {boss_guid_id[:-6]: boss_name}
    else:
        targets_useful = {}

    targets_all = ALL_GUIDS.get(boss_name, targets_useful)
    return {
        "useful": targets_useful,
        "all": targets_all,
    }

def get_dmg(logs_slice: list[str], targets: dict):
    all_dmg: dict[str, dict[str, int]] = {x: defaultdict(int) for x in targets}
    for line in logs_slice:
        if "_DAMAGE" not in line:
            continue
        _, _, sGUID, _, tGUID, _, _, _, _, dmg, ok, _ = line.split(',', 11)
        tGUID_ID = tGUID[:-6]
        if tGUID_ID not in targets:
            continue
        all_dmg[tGUID_ID][sGUID] += int(dmg) - int(ok)
    return all_dmg

def dmg_gen_valk(logs: list[str]):
    for line in logs:
        if '8F01' not in line:
            continue
        if "_DAMAGE" not in line:
            continue
        _, _, sGUID, _, tGUID, _, _, _, _, dmg, _ = line.split(',', 10)
        if tGUID[5:-6] == '0008F01':
            yield sGUID, tGUID, int(dmg)

@running_time
def get_valks_dmg(logs: list[str]):
    valks_useful: defaultdict[str, int] = defaultdict(int)
    valks_overkill: defaultdict[str, int] = defaultdict(int)

    valks_dmg_taken: defaultdict[str, int] = defaultdict(int)

    for sGUID, tGUID, amount in dmg_gen_valk(logs):
        _dmg_taken = valks_dmg_taken.get(tGUID, 0)
        if _dmg_taken == -1:
            valks_overkill[sGUID] += amount
            continue

        current_dmg_taken = _dmg_taken + amount
        if current_dmg_taken < VALK_HALF_HP:
            valks_dmg_taken[tGUID] = current_dmg_taken
        else:
            valks_dmg_taken[tGUID] = -1
            overkill = current_dmg_taken - VALK_HALF_HP
            amount -= overkill
            valks_overkill[sGUID] += overkill
        valks_useful[sGUID] += amount

    return {
        'overkill': valks_overkill,
        'useful': valks_useful,
    }

def combine_pets(data: dict[str, int], guids: dict[str, dict], trim_non_players=False, ignore_abom=False):
    def check_master(guid: str):
        return guids[guid].get('master_guid', guid)
    
    combined: dict[str, int] = defaultdict(int)
    for sGUID, value in data.items():
        if ignore_abom and sGUID[6:-6] == "00958D":
            continue
        _sGUID = check_master(sGUID)
        if trim_non_players and not is_player(_sGUID):
            continue
        combined[_sGUID] += value

    return combined

def combine_pets_all(data: dict[str, int], guids, trim_non_players=False, ignore_abom=False):
    return {
        tGUID: combine_pets(d, guids, trim_non_players, ignore_abom)
        for tGUID, d in data.items()
    }

def combine_targets(data: dict[str, dict[str, int]], filter_targets=None):
    total = defaultdict(int)

    for target_guid_id, sources in data.items():
        if filter_targets and target_guid_id not in filter_targets:
            for sGUID in sources:
                total[sGUID] += 0
        else:
            for sGUID, value in sources.items():
                total[sGUID] += value

    return total

def specific_useful(logs_slice, boss_name):
    data = {}
    if boss_name == "The Lich King":
        valks_dmg = get_valks_dmg(logs_slice)
        data['Valks Useful'] = valks_dmg['useful']
        # data['0xF150008F01'] = valks_dmg['useful']
    return data

def specific_useful_combined(logs_slice, boss_name):
    new_data = defaultdict(int)
    data = specific_useful(logs_slice, boss_name)
    for _data in data.values():
        for guid, d in _data.items():
            new_data[guid] += d
    return new_data
