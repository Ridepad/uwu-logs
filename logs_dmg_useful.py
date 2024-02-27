from collections import defaultdict
from typing import TypedDict

from constants import (
    TOC_CHAMPIONS,
    is_player,
    running_time,
    sort_dict_by_value,
    separate_thousands_dict,
    add_new_numeric_data,
    BOSSES_GUIDS,
)

import logs_base

NOT_DMG = {
    "DAMAGE_SHIELD_MISSED",
    "DAMAGE_SPLIT",
}
TOC_PETS = {
    "008B1A": "Cat",
    "008A89": "Demon",
    "008CE6": "Treants",
}
USEFUL = {
    "Lord Marrowgar": {
        "008F04": "Lord Marrowgar",
        "008F0B": "Bone Spike",
        "009738": "Bone Spike",
        "009737": "Bone Spike",
    },
    "Lady Deathwhisper": {
        "008FF7": "Lady Deathwhisper",
        "009402": "Cult Fanatic",
        "00943D": "Cult Adherent",
        "009655": "Darnavan",
    },
    "Gunship": {
        "0090FC": "Skybreaker Sorcerer",
        "0090FD": "Kor'kron Battle-Mage",
    },
    "Deathbringer Saurfang": {
        "0093B5": "Deathbringer Saurfang",
        "00966C": "Blood Beast",
    },
    "Festergut": {
        "008F12": "Festergut",
    },
    "Rotface": {
        "008F13": "Rotface",
    },
    "Professor Putricide": {
        "008F46": "Professor Putricide",
        "0092BA": "Gas Cloud",
        "009341": "Volatile Ooze",
    },
    "Blood Prince Council": {
        "009452": "Prince Valanar",
        "009455": "Prince Taldaram",
        "009454": "Prince Keleseth",
    },
    "Blood-Queen Lana'thel": {
        "009443": "Blood-Queen Lana'thel",
    },
    "Valithria Dreamwalker": {
        "008FB7": "Blazing Skeleton",
        "0093EC": "Risen Archmage",
        "009413": "Rot Worm",
        "0093E7": "Suppresser",
        "0093FE": "Gluttonous Abomination",
        "00942E": "Blistering Zombie",
    },
    "Sindragosa": {
        "008FF5": "Sindragosa",
        "009074": "Ice Tomb",
    },
    "The Lich King": {
        "008EF5": "The Lich King",
        "008F19": "Ice Sphere",
        "008F5D": "Raging Spirit",
        "009916": "Wicked Spirit",
    },
    "Baltharus the Warborn": {
        "009B47": "Baltharus the Warborn",
    },
    "Saviana Ragefire": {
        "009B43": "Saviana Ragefire",
    },
    "General Zarithrian": {
        "009B42": "General Zarithrian",
    },
    "Halion": {
        "009BB7": "Halion",
        "009CCE": "Halion",
        "009EE9": "Living Inferno",
    },
    "Northrend Beasts": {
        "0087EC": "Gormok the Impaler",
        "0087EF": "Dreadscale",
        "008948": "Acidmaw",
        "0087ED": "Icehowl",
        "0087F0": "Snobold Vassal",
    },
    "Lord Jaraxxus": {
        "0087DC": "Lord Jaraxxus",
        "0087FD": "Infernal Volcano",
        "008809": "Nether Portal",
    },
    "Faction Champions": TOC_CHAMPIONS,
    "Twin Val'kyr": {
        "0086C0": "Eydis Darkbane",
        "0086C1": "Fjola Lightbane",
    },
    "Anub'arak": {
        "008704": "Anub'arak",
        "00872D": "Swarm Scarab",
    },
    "Toravon the Ice Watcher": {
        "009621": "Toravon the Ice Watcher",
        "009638": "Frozen Orb",
    },
    "Onyxia": {
        "0027C8": "Onyxia",
    },
    "Malygos": {
        "0070BB": "Malygos",
    },
    "Sartharion": {
        "0070BC": "Sartharion",
        "0076F4": "Tenebron",
        "0076F3": "Shadron",
        "0076F1": "Vesperon",
    },
    "Razorscale": {
        "0081A2": "Razorscale",
        "00826C": "Dark Rune Guardian",
        "0082AD": "Dark Rune Watcher",
        "008436": "Dark Rune Sentinel",
    },
    "Ignis the Furnace Master": {
        "00815E": "Ignis the Furnace Master",
    },
    "XT-002 Deconstructor": {
        "00820D": "XT-002 Deconstructor",
        "008231": "Heart of the Deconstructor",
        "0084D4": "Life Spark",
        "008242": "XE-321 Boombot",
        "008240": "XM-024 Pummeller",
        "00823F": "XS-013 Scrapbot",
    },
    "Assembly of Iron": {
        "00809F": "Runemaster Molgeim",
        "008059": "Stormcaller Brundir",
        "008063": "Steelbreaker",
    },
    "Algalon the Observer": {
        "008067": "Algalon the Observer",
        "0080BB": "Collapsing Star",
        "00811C": "Living Constellation",
        "008531": "Unleashed Dark Matter",
    },
    "Kologarn": {
        "0080A2": "Kologarn",
        "0080A5": "Left Arm",
        "0080A6": "Right Arm",
        "0083E8": "Rubble",
    },
    "Auriaya": {
        "0082EB": "Auriaya",
        "0084DE": "Sanctum Sentry",
    },
    "Hodir": {
        "00804D": "Hodir",
        "0080AA": "Flash Freeze",
    },
    "Thorim": {
        "008061": "Thorim",
        "008068": "Runic Colossus",
        "00806A": "Iron Ring Guard",
        "00806B": "Swarming Guardian",
        "008156": "Dark Rune Acolyte",
        "008069": "Ancient Rune Giant",
        "00806B": "Iron Honor Guard",
    },
    "Freya": {
        "00808A": "Freya",
        "0081B3": "Ancient Conservator",
        "0081B2": "Ancient Water Spirit",
        "008096": "Detonating Lasher",
        "0081CC": "Eonar's Gift",
        "008094": "Snaplasher",
        "008097": "Storm Lasher",
        "008190": "Strengthened Iron Roots",
    },
    "Mimiron": {
        "008298": "Leviathan Mk II",
        "008373": "VX-001",
        "008386": "Aerial Command Unit",
        "008509": "Assault Bot",
        "00843F": "Junk Bot",
        "008563": "Emergency Fire Bot",
    },
    "General Vezax": {
        "0081F7": "General Vezax",
        "0082F4": "Saronite Animus",
    },
    "Yogg-Saron": {
        "008208": "Yogg-Saron",
        "008462": "Brain of Yogg-Saron",
        "008170": "Guardian of Yogg-Saron",
        "0084C1": "Corruptor Tentacle",
        "0084BF": "Constrictor Tentacle",
        "0084AE": "Crusher Tentacle",
        "00831F": "Influence Tentacle",
        "0084C4": "Immortal Guardian",
        "0083B4": "Ruby Consort",
        "0083B7": "Emerald Consort",
        "008299": "Suit of Armor",
    },

    "Majordomo Executus": {
        # "002EF2": "Majordomo Executus",
        "002D90": "Flamewaker Elite",
        "002D8F": "Flamewaker Healer",
    },
    "Gehennas": {
        "002FE3": "Gehennas",
        "002D8D": "Flamewaker",
    },
    "Sulfuron Harbringer": {
        "002F42": "Sulfuron Harbinger",
        "002D8E": "Flamewaker Priest",
    },
    "Lucifron": {
        "002F56": "Lucifron",
        "002F57": "Flamewaker Protector",
    },
    "Golemagg the Incinerator": {
        "002ED4": "Golemagg the Incinerator",
        "002D98": "Core Rager",
    },
    "002F43": {
        "002F19": "Garr",
        "002F43": "Firesworn",
    },
}

ALL_GUIDS = {
    "Gunship": {
        "0090FC": "Skybreaker Sorcerer",
        "0090FD": "Kor'kron Battle-Mage",
        "009069": "Skybreaker Rifleman",
        "009068": "Kor'kron Axethrower",
        "009054": "Muradin Bronzebeard",
        "00904B": "High Overlord Saurfang",
        "0090A2": "Skybreaker Sorcerer",
        "009061": "Skybreaker Sergeant",
        "009056": "Skybreaker Marine",
        "00905D": "Kor'kron Reaver",
        "009060": "Kor'kron Sergeant",
        "009076": "Kor'kron Rocketeer",
    },
    "Rotface": {
        "008F13": "Rotface",
        "009023": "Big Ooze",
        "009021": "Little Ooze",
        # "00908E": "Sticky Ooze",
    },
    "Blood Prince Council": {
        "009452": "Prince Valanar",
        "009455": "Prince Taldaram",
        "009454": "Prince Keleseth",
        "0095E1": "Dark Nucleus",
        "009636": "Kinetic Bomb",
    },
    "Valithria Dreamwalker": {
        "008FB5": "Valithria Dreamwalker",
        "008FB7": "Blazing Skeleton",
        "009413": "Rot Worm",
        "0093E7": "Suppresser",
        "0093EC": "Risen Archmage",
        "0093FE": "Gluttonous Abomination",
        "00942E": "Blistering Zombie",
    },
    "The Lich King": {
        "008F01": "Val'kyr Shadowguard",
        "008EF5": "The Lich King",
        "008F5D": "Raging Spirit",
        "008F19": "Ice Sphere",
        "009916": "Wicked Spirit",
        "00933F": "Drudge Ghoul",
        "009342": "Shambling Horror",
        "0093A7": "Vile Spirit",
    },
    "Lord Jaraxxus": {
        "0087DC": "Lord Jaraxxus",
        "0087FD": "Infernal Volcano",
        "008809": "Nether Portal",
        "00880A": "Mistress of Pain",
        "0087FF": "Felflame Infernal",
    },
    "Faction Champions": TOC_CHAMPIONS | TOC_PETS,
    "Anub'arak": {
        "008704": "Anub'arak",
        "00872D": "Swarm Scarab",
        "00872F": "Nerubian Burrower",
        "00872E": "Frost Sphere",
    },
    "Baltharus the Warborn": {
        "009B47": "Baltharus the Warborn",
        "009BDB": "Baltharus the Copyborn",
    },
    "General Zarithrian": {
        "009B42": "General Zarithrian",
        "009B86": "Onyx Flamecaller"
    },
    "Halion": {
        "009BB7": "Halion Fire",
        "009CCE": "Halion Shadow",
        "009EE9": "Living Inferno",
        "009EEB": "Living Ember",
    },
    "Sartharion": {
        '0070BC': "Sartharion",
        '0076F4': "Tenebron",
        '0076F3': "Shadron",
        '0076F1': "Vesperon",
        '0077B3': "Lava Blaze",
        '0079EE': "Sartharion Twilight Whelp",
        '0079F2': "Acolyte of Shadron",
        '0079F3': "Acolyte of Vesperon",
    },
    "Malygos": {
        "0070BB": "Malygos",
        "007584": "Power Spark",
    },
    "Onyxia": {
        "0027C8": "Onyxia",
        "002BFE": "Onyxian Whelp",
        "008ED1": "Onyxian Lair Guard",
    },
    "Ignis the Furnace Master": {
        "00815E": "Ignis the Furnace Master",
        "008161": "Iron Construct",
    },
    "Algalon the Observer": {
        "008067": "Algalon the Observer",
        "0080BB": "Collapsing Star",
    },
    "Mimiron": {
        "008298": "Leviathan Mk II",
        "008373": "VX-001",
        "008386": "Aerial Command Unit",
        "008509": "Assault Bot",
        "00843F": "Junk Bot",
        "00842C": "Bomb Bot",
        "008563": "Emergency Fire Bot",
    },
    "Auriaya": {
        "0082EB": "Auriaya",
        "0084F3": "Feral Defender",
        "0084DE": "Sanctum Sentry",
        "0084F2": "Swarming Guardian",
    },
}

CUSTOM_GROUPS: dict[str, dict[str, tuple[str]]] = {
    "Lady Deathwhisper": {
        "Adds": ("009402", "00943D", "009655"),
    },
    "Professor Putricide": {
        "Oozes": ("0092BA", "009341"),
    },
    "Halion": {
        "Halion": ("009BB7", "009CCE"),
        "Adds": ("009EE9", "009EEB"),
    }
}

USEFUL_NAMES = {
    "008F01": "Valks Useful",
    "00808A": "Freya Useful",
}

ALL_USEFUL_TARGETS = {
    x
    for v in USEFUL.values()
    for x in v
} | set(USEFUL_NAMES) | set(BOSSES_GUIDS)


class ValksDamage(TypedDict):
    overkill: defaultdict[str, int]
    useful: defaultdict[str, int]

class TargetDamageAllType(TypedDict):
    specific_combined: dict[str, defaultdict[str, int]]
    useful_total: defaultdict[str, int]
    damage_combined: dict[str, defaultdict[str, int]]
    damage_total: defaultdict[str, int]


def target_order(boss_name):
    return list(USEFUL.get(boss_name, {})) + list(ALL_GUIDS.get(boss_name, {}))

@running_time
def get_dmg(logs_slice: list[str]):
    all_dmg = defaultdict(lambda: defaultdict(int))
    for line in logs_slice:
        if "DAMAGE" not in line:
            continue
        _line = line.split(',', 11)
        if _line[1] in NOT_DMG:
            continue
        all_dmg[_line[4][6:-6]][_line[2]] += int(_line[9]) - int(_line[10])
    return all_dmg

def dmg_gen_valk(logs: list[str]):
    for line in logs:
        if '8F01' not in line:
            continue
        if "_DAMAGE" not in line:
            continue
        _, _, sGUID, _, tGUID, _, _, _, _, dmg, _ = line.split(',', 10)
        if tGUID[6:-6] == '008F01':
            yield sGUID, tGUID, int(dmg)

@running_time
def get_valks_dmg(logs: list[str], half_hp=2992500 // 2) -> ValksDamage:
    valks_useful = defaultdict(int)
    valks_overkill = defaultdict(int)

    valks_dmg_taken = defaultdict(int)

    for sGUID, tGUID, amount in dmg_gen_valk(logs):
        _dmg_taken = valks_dmg_taken[tGUID]
        if _dmg_taken == -1:
            valks_overkill[sGUID] += amount
            continue

        current_dmg_taken = _dmg_taken + amount
        if current_dmg_taken < half_hp:
            valks_dmg_taken[tGUID] = current_dmg_taken
        else:
            valks_dmg_taken[tGUID] = -1
            overkill = current_dmg_taken - half_hp
            amount -= overkill
            valks_overkill[sGUID] += overkill
        valks_useful[sGUID] += amount

    return {
        'overkill': valks_overkill,
        'useful': valks_useful,
    }

def get_total_damage(data: dict[str, dict[str, int]], filter_targets=None, ignore_targets=None):
    total = defaultdict(int)

    if not ignore_targets:
        ignore_targets = set()
    
    for target_guid_id, sources in data.items():
        if filter_targets and target_guid_id not in filter_targets:
            for sGUID in sources:
                total[sGUID] += 0
        elif target_guid_id not in ignore_targets:
            for sGUID, value in sources.items():
                total[sGUID] += value

    return total

def freya_useful(logs_slice: list[str]):
    FREYA = "00808A"
    DAMAGE: defaultdict[str, int] = defaultdict(int)
    healing = True
    for line in logs_slice:
        if FREYA not in line:
            continue

        if healing:
            if "SPELL_PERIODIC_HEAL" in line and line.split(',', 11)[10] == '0':
                healing = False
            continue
        
        if "DAMAGE" not in line:
            continue
        try:
            _, _, sGUID, _, tGUID, _, _, _, _, dmg, _ = line.split(',', 10)
            if tGUID[6:-6] == FREYA:
                DAMAGE[sGUID] += int(dmg)
        except ValueError:
            pass
    
    return DAMAGE

# 8/31 20:12:36.834  SPELL_PERIODIC_HEAL,00808A000A6D,"Freya",0x10a48,00808A000A6D,"Freya",0x10a48,62528,"Touch of Eonar",0x1,42000,14075,0,nil
# 9/ 1 20:26:43.762  SPELL_PERIODIC_HEAL,00808A000CC3,"Freya",0x10a48,00808A000CC3,"Freya",0x10a48,62892,"Touch of Eonar",0x1,218400,143919,0,nil

def guid_to_custom_name(data):
    return {
        USEFUL_NAMES[q]: w
        for q,w in data.items()
        if q in USEFUL_NAMES
    }

def specific_useful(logs_slice, boss_name):
    data: dict[str, defaultdict[str, int]] = {}
    if boss_name == "The Lich King":
        valks_dmg = get_valks_dmg(logs_slice)
        # data['Valks Useful'] = valks_dmg['useful']
        data['008F01'] = valks_dmg['useful']
    elif boss_name == "Freya":
        data['00808A'] = freya_useful(logs_slice)
        
    return data

def specific_useful_combined(logs_slice, boss_name):
    new_data = defaultdict(int)
    data = specific_useful(logs_slice, boss_name)
    for _data in data.values():
        for guid, d in _data.items():
            new_data[guid] += d
    return new_data

def no_units_from_custom_group(guids, all_units):
    return not set(guids) & all_units

def add_custom_units(data: dict[str, defaultdict[str, int]], encounter_name: str):
    _custom_groups = CUSTOM_GROUPS.get(encounter_name)
    if not _custom_groups:
        return {}

    all_units = set(data)
    custom_data = {}
    for group_name, guids in _custom_groups.items():
        if no_units_from_custom_group(guids, all_units):
            continue
        q = custom_data[group_name] = defaultdict(int)
        for guid in guids:
            if guid not in data:
                continue
            for player_guid, player_damage in data[guid].items():
                q[player_guid] += player_damage

    return custom_data

def add_new_numeric_data_wrap(d1, d2):
    for k, v in d2.items():
        add_new_numeric_data(d1[k], v)

def sort_by_key(data: dict):
    return dict(sorted(data.items()))

def add_total_sort(data: dict):
    data["Total"] = sum(data.values())
    return sort_dict_by_value(data)


class UsefulDamage(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def target_damage(self, s, f):
        logs_slice = self.LOGS[s:f]
        return get_dmg(logs_slice)
    
    @logs_base.cache_wrap
    def target_damage_specific(self, s, f, boss_name: str):
        logs_slice = self.LOGS[s:f]
        return specific_useful(logs_slice, boss_name)

    def target_damage_wrap(self, segments: list, boss_name: str):
        damage = defaultdict(lambda: defaultdict(int))
        useful_specific = defaultdict(lambda: defaultdict(int))

        for s, f in segments:
            _damage = self.target_damage(s, f)
            add_new_numeric_data_wrap(damage, _damage)

            _specific = self.target_damage_specific(s, f, boss_name)
            add_new_numeric_data_wrap(useful_specific, _specific)
        
        return {
            "damage": damage,
            "useful_specific": useful_specific,
        }

    def combine_pets(self, data: dict[str, int], trim_non_players=False, ignore_abom=False):
        guids = self.get_all_guids()
        combined: dict[str, int] = defaultdict(int)
        for sGUID, value in data.items():
            if sGUID not in guids:
                continue
            if ignore_abom and sGUID[6:-6] == "00958D":
                continue
            sGUID = self.get_master_guid(sGUID)
            if trim_non_players and not is_player(sGUID):
                continue
            combined[sGUID] += value

        return combined

    def combine_pets_all(self, data: dict[str, int], trim_non_players=False, ignore_abom=False):
        return {
            tGUID: self.combine_pets(d, trim_non_players, ignore_abom)
            for tGUID, d in data.items()
        }

    @running_time
    def target_damage_combine(self, damage, useful_specific) -> TargetDamageAllType:
        damage_combined = self.combine_pets_all(damage, trim_non_players=True, ignore_abom=True)
        damage_total = get_total_damage(damage_combined, ignore_targets=self.FRIENDLY_IDS)

        specific_combined = self.combine_pets_all(useful_specific, trim_non_players=True, ignore_abom=True)
        _useful = damage_combined | specific_combined
        useful_total = get_total_damage(_useful, filter_targets=ALL_USEFUL_TARGETS)

        return {
            "specific_combined": specific_combined,
            "useful_total": useful_total,
            "damage_combined": damage_combined,
            "damage_total": damage_total,
        }

    @running_time
    def target_damage_all(self, segments: list, boss_name: str):
        _w = self.target_damage_wrap(segments, boss_name)
        return self.target_damage_combine(_w["damage"], _w["useful_specific"])

    def target_damage_all_formatted(self, segments, boss_name):
        _filtered = self.target_damage_all(segments, boss_name)
        
        data_all = {
            "Useful": _filtered["useful_total"],
            "Total": _filtered["damage_total"],
        }

        damage_combined = _filtered["damage_combined"]
        useful_specific_names = guid_to_custom_name(_filtered["specific_combined"])
        data_all.update(useful_specific_names)
        
        custom_groups = add_custom_units(damage_combined, boss_name)
        data_all.update(custom_groups)

        _friendly_fire = damage_combined.pop("000000", {})
        _order = target_order(boss_name)
        damage_combined_sorted = dict(sorted(damage_combined.items(), key=lambda x: x[0] not in _order))
        damage_combined_sorted = self.convert_dict_guids_to_names(damage_combined_sorted)
        data_all.update(damage_combined_sorted)
        
        data_all["Friendly Fire"] = _friendly_fire

        dmg_to_target = {
            name: separate_thousands_dict(add_total_sort(_data))
            for name, _data in data_all.items()
            if _data
        }

        specs = self.get_slice_spec_info(*segments[0])
        sorted_players = list(add_total_sort(sort_by_key(_filtered["useful_total"])))
        return {
            "TARGETS": dmg_to_target,
            "PLAYERS_SORTED": sorted_players,
            "SPECS": specs,
        }
