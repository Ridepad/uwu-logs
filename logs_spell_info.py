from collections import defaultdict


import constants
from constants import to_dt

@constants.running_time
def get_spell_count(logs_slice: list[str], spell_id_str: str):
    SPELL = "SWING_" if spell_id_str == "1" else "SPELL_"
    spells: dict[str, dict[str, dict[str, int]]] = {}
    for line in logs_slice:
        if spell_id_str not in line:
            continue
        if SPELL not in line:
            continue

        if "_DISPEL" in line:
            _, flag, _, source_name, _, target_name, _, _, _, s_id, _ = line.split(',', 10)
        else:
            _, flag, _, source_name, _, target_name, s_id, o = line.split(',', 7)
        # if "_DISPEL" in flag and s_id != spell_id_str:
        #     _, _, s_id, _ = o.split(',', 3)

        if s_id == spell_id_str:
            flag_info = spells.setdefault(flag, {"sources": {}, "targets": {}})
            flag_info["sources"][source_name] = flag_info["sources"].get(source_name, 0) + 1
            flag_info["targets"][target_name] = flag_info["targets"].get(target_name, 0) + 1
    return spells

POT_ICON = {
    "53908": "inv_alchemy_elixir_04",
    "53909": "inv_alchemy_elixir_01",
    "28494": "inv_potion_109",
    "28507": "inv_potion_108",
    "28714": "inv_misc_herb_flamecap",
    "53762": "inv_alchemy_elixir_empty",
    "56350": "inv_misc_enggizmos_32",
    "54758": "spell_shaman_elementaloath",
    "56488": "inv_gizmo_supersappercharge",
    "13241": "spell_fire_selfdestruct",
    "30486": "inv_gizmo_supersappercharge",
}
ITEM_INFO = {
    "53908": {
        "name": "Potion of Speed",
        "icon": "inv_alchemy_elixir_04",
    },
    "53909": {
        "name": "Potion of Wild Magic",
        "icon": "inv_alchemy_elixir_01",
    },
    "28494": {
        "name": "Insane Strength Potion",
        "icon": "inv_potion_109",
    },
    "28507": {
        "name": "Haste Potion",
        "icon": "inv_potion_108",
    },
    "28714": {
        "name": "Flame Cap",
        "icon": "inv_misc_herb_flamecap",
    },
    "53762": {
        "name": "Indestructible Potion",
        "icon": "inv_alchemy_elixir_empty",
    },
    "54758": {
        "name": "Hyperspeed Acceleration",
        "icon": "spell_shaman_elementaloath",
    },
    "56350": {
        "name": "Saronite Bomb",
        "icon": "inv_misc_enggizmos_32",
    },
    "56488": {
        "name": "Global Thermal Sapper Charge",
        "icon": "inv_gizmo_supersappercharge",
    },
    "13241": {
        "name": "Goblin Sapper Charge",
        "icon": "spell_fire_selfdestruct",
    },
    "30486": {
        "name": "Super Sapper Charge",
        "icon": "inv_gizmo_supersappercharge",
    },
}

AURAS = {
    "57933": {
        "name": "Tricks of the Trade",
        "icon": "ability_rogue_tricksofthetrade",
    },
    "10060": {
        "name": "Power Infusion",
        "icon": "spell_holy_powerinfusion",
    },
    "49016": {
        "name": "Hysteria",
        "icon": "spell_deathknight_bladedarmor",
    },
    "2825": {
        "name": "Bloodlust",
        "icon": "spell_nature_bloodlust",
    },
    "32182": {
        "name": "Heroism",
        "icon": "ability_shaman_heroism",
    },
    "28714": {
        "name": "Flame Cap",
        "icon": "inv_misc_herb_flamecap",
    },
    "46352": {
        "name": "Fire Festival Fury",
        "icon": "inv_summerfest_fireflower"
    },
    "29333": {
        "name": "Midsummer Sausage",
        "icon": "inv_misc_food_53"
    },
    "29334": {
        "name": "Toasted Smorc",
        "icon": "inv_summerfest_smorc"
    },
    "29332": {
        "name": "Fire-toasted Bun",
        "icon": "inv_misc_food_11"
    },
    "72553": {
        "name": "Gastric Bloat",
        "icon": "achievement_boss_festergutrotface"
    },
    "71533": {
        "name": "Essence of the Blood Queen",
        "icon": "ability_warlock_improvedsoulleech"
    },
    "71531": {
        "name": "Essence of the Blood Queen",
        "icon": "ability_warlock_improvedsoulleech"
    },
    "48889": {
        "name": "Pyroblast Cinnamon Ball",
        "icon": "inv_misc_orb_05"
    },
    "48891": {
        "name": "Soothing Spearmint Candy",
        "icon": "inv_misc_gem_pearl_06"
    },
    "48892": {
        "name": "Chewy Fel Taffy",
        "icon": "inv_misc_slime_01"
    },
    "51800": {
        "name": "Might of Malygos",
        "icon": "inv_misc_head_dragon_blue"
    }
}


ALL_POTS = set(ITEM_INFO) - {"28714", }
POTS_VALUE = {'28714', '53909', '28494', '28507', '53908'}

def count_total(data: dict[str, dict[str, int]]):
    total: defaultdict[str, int] = defaultdict(int)
    for pot_id in POTS_VALUE:
        if pot_id in data:
            for guid, value in data[pot_id].items():
                total[guid] += value
    return total

@constants.running_time
def get_potions_count(logs_slice: list[str]):
    potions: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for line in logs_slice:
        if '_SUCCESS' in line:
            _, _, source_guid, _, _, _, spell_id, _ = line.split(',', 7)
            if spell_id in ALL_POTS:
                potions[spell_id][source_guid] += 1
        elif "28714" in line and "_APPLIED" in line:
            source_guid = line.split(',', 5)[4]
            potions["28714"][source_guid] += 1

    return potions


@constants.running_time
def get_raid_buff_count(logs_slice: list[str], flag_filter='SPELL_AURA'):
    auras: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for line in logs_slice:
        if flag_filter in line:
            timestamp, flag, _, _, target_guid, _, spell_id, _ = line.split(',', 7)
            if spell_id in AURAS:
                auras[target_guid][spell_id].append((flag, timestamp))

    return auras

def get_auras_uptime(logs_slice, data: dict[str, dict[str, list]]):
    s = to_dt(logs_slice[0])
    e = to_dt(logs_slice[-1])
    dur = (e-s).total_seconds()

    new_auras: defaultdict[str, dict[str, float]] = defaultdict(dict)

    for target_guid, data1 in data.items():
        for spell_id, data2 in data1.items():
            a = 0
            c = 0
            last_apply = None
            for flag, timestamp in data2:
                if flag == "SPELL_AURA_REMOVED":
                    if last_apply is None:
                        last_apply = s
                        c += 1
                    a += (to_dt(timestamp)-last_apply).total_seconds()
                    last_apply = None
                elif last_apply is None:
                    c += 1
                    last_apply = to_dt(timestamp)
                elif flag == "SPELL_AURA_REFRESH":
                    c += 1

            if last_apply is not None:
                a += (e-last_apply).total_seconds()

            new_auras[target_guid][spell_id] = (c, a/dur)
    
    return new_auras

def get_filtered_info(data):
    return {
        spell_id: spell_info
        for spell_id, spell_info in AURAS.items()
        if spell_id in data
    }


def __test():
    import logs_main
    report_name = "22-06-25--20-20--Jenbrezul"
    report = logs_main.THE_LOGS(report_name)
    enc_data = report.get_enc_data()
    s, f = enc_data["The Lich King"][4]
    logs = report.get_logs(s, f)
    q = get_raid_buff_count(logs)
    q2 = get_auras_uptime(logs, q)
    print(q2)
    
if __name__ == "__main__":
    __test()
# ids = [46352, 29333, 29332, 29334, 72553, 71533, 71531, 48892, 48891, 48889, 51800]
# trids = [71605, 71636]
# import requests
# import json
# import re

# DATA = {}
# def doshit(spell_id):
#     url = f"https://wotlk.evowow.com/?spell={spell_id}"
#     page = requests.get(url).text
#     data = re.findall("g_spells.*?(\{.*?\})", page)[0]
#     data = json.loads(data)
#     DATA[spell_id] = {"name": data['name_enus'], "icon": data['icon']}

# for spell_id in ids:
#     doshit(spell_id)
# print(json.dumps(DATA, indent=4))