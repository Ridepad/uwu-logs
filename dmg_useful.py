from collections import defaultdict

import constants

VALK_HALF_HP = 2992500 // 2
TOC_CHAMPIONS_USEFUL = {f"0xF130{guid}": name for guid, name in constants.TOC_CHAMPIONS.items()}
TOC_PETS = {
    "0xF130008B1A": "Cat",
    "0xF130008A89": "Demon",
    "0xF130008CE6": "Treants",
}
TOC_CHAMPIONS_ALL = TOC_CHAMPIONS_USEFUL | TOC_PETS

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
        "0xF130009069": "Skybreaker Rifleman",
        "0xF130009068": "Kor'kron Axethrower",
    },
    "Deathbringer Saurfang": {
        "0xF1500093B5": "Deathbringer Saurfang",
        "0xF13000966C": "Blood Beast",
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
        "0xF13000872D": "Swarm Scarab",
        "0xF130008704": "Anub'arak",
    },
    "Toravon the Ice Watcher": {
        "0xF130009621": "Toravon the Ice Watcher",
        "0xF130009638": "Frozen Orb",
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
        "0xF1300093FE": "Gluttonous Abomination",
        "0xF1300093EC": "Risen Archmage",
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
    "Faction Champions": TOC_CHAMPIONS_ALL,
    "Anub'arak": {
        "0xF130008704": "Anub'arak",
        "0xF13000872D": "Swarm Scarab",
        "0xF13000872F": "Nerubian Burrower",
        "0xF13000872E": "Frost Sphere",
    },
    "Baltharus the Warborn": {
        "0xF130009B47": "Baltharus the Warborn",
        "0xF130009BDB": "Baltharus the Warborn",
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
        return {}, {}
    
    if boss_name in USEFUL:
        targets_useful = USEFUL[boss_name]
    elif boss_guid_id:
        targets_useful = {boss_guid_id[:-6]: boss_name}
    else:
        targets_useful = {}

    targets_all = ALL_GUIDS.get(boss_name, targets_useful)
    return targets_useful, targets_all

@constants.running_time
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

VALK = {'0xF130008F01', '0xF150008F01'}
def dmg_gen_valk(logs: list[str]):
    for line in logs:
        if '0008F01' not in line:
            continue
        if "_DAMAGE" not in line:
            continue
        _, _, sGUID, _, tGUID, _, _, _, _, dmg, _ = line.split(',', 10)
        if tGUID[:-6] in VALK:
            yield sGUID, tGUID, int(dmg)

@constants.running_time
def get_valks_dmg(logs: list[str]):
    valks_useful: defaultdict[str, int] = defaultdict(int)
    valks_overkill: defaultdict[str, int] = defaultdict(int)

    valks_dmg_taken: defaultdict[str, int] = defaultdict(int)

    for sGUID, tGUID, amount in dmg_gen_valk(logs):
        if valks_dmg_taken.get(tGUID) == -1:
            valks_overkill[sGUID] += amount
            continue

        current_dmg_taken = valks_dmg_taken.get(tGUID, 0) + amount
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

def combine_pets(data: dict[str, int], guids: dict[str, dict], trim_non_players=False):
    def check_master(guid: str):
        return guids[guid].get('master_guid', guid)
    
    q: dict[str, int] = {}
    for sGUID, w in data.items():
        sGUID = check_master(sGUID)
        if trim_non_players and not sGUID.startswith('0x06'):
            continue
        q[sGUID] = q.get(sGUID, 0) + w
    return q

def combine_pets_all(data: dict, guids, trim_non_players=True):
    return {
        tGUID: combine_pets(d, guids, trim_non_players)
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



def add_space(v):
    return f"{v:,}".replace(',', ' ')

def __test():
    import _main
    name = '21-10-04--19-54--Cedrist'
    name = '21-10-06--20-51--Safiyah'
    name = '21-10-07--21-06--Inia'
    name = '21-10-08--20-57--Nomadra'
    name = '22-03-25--22-02--Nomadra'

    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guids = report.get_all_guids()
    enc_data = report.get_enc_data()

    boss_name = "Blood Prince Council"
    boss_name = "The Lich King"
    boss_name = "Professor Putricide"
    boss_name = "Rotface"
    attempt = -1
    s, f = None, None
    # s = enc_data[boss_name][0][0]
    # f = enc_data[boss_name][-1][-1]
    s, f = enc_data[boss_name][attempt]
    logs_slice = logs[s:f]
    targets_useful, targets_all = get_all_targets(report, boss_name)
    _all_dmg = get_dmg(logs_slice, targets_all)

    if boss_name == "The Lich King":
        valks_dmg = get_valks_dmg(logs_slice, guids)
        _all_dmg['0xF150008F01'] = valks_dmg['useful']

    _all_dmg = combine_pets_all(_all_dmg, guids, trim_non_players=True)
    _total1 = combine_targets(_all_dmg, targets_useful)
    _total1 = sorted(_total1.items(), key=lambda x: x[1], reverse=True)
    for x,y in _total1:
        print(f"{guids[x]['name']:<12} {add_space(y):>10}")

if __name__ == "__main__":
    __test()
