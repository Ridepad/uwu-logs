from collections import defaultdict

import constants
from constants import to_dt

@constants.running_time
def get_spell_count(logs_slice: list[str], spell_id_str: str):
    _default_dict_factory = lambda: {"sources": defaultdict(int), "targets": defaultdict(int)}
    spells = defaultdict(_default_dict_factory)
    for line in logs_slice:
        if spell_id_str not in line:
            continue

        if "_DISPEL" in line:
            _, flag, _, source_name, _, target_name, _, _, _, s_id, _ = line.split(',', 10)
        else:
            _, flag, _, source_name, _, target_name, s_id, _ = line.split(',', 7)

        if s_id == spell_id_str:
            spells[flag]["sources"][source_name] += 1
            spells[flag]["targets"][target_name] += 1
    return spells

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

AURAS_EXTERNAL = {
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
    "23060": {
        "name": "Battle Squawk",
        "icon": "inv_misc_birdbeck_01",
    },
    "2825": {
        "name": "Bloodlust",
        "icon": "spell_nature_bloodlust",
    },
    "32182": {
        "name": "Heroism",
        "icon": "ability_shaman_heroism",
    },
    "54646": {
        "name": "Focus Magic",
        "icon": "spell_arcane_studentofmagic",
    },
    "29166": {
        "name": "Innervate",
        "icon": "spell_nature_lightning",
    },
    "63848": {
        "name": "Hunger For Blood",
        "icon": "ability_rogue_hungerforblood",
    },
    "51800": {
        "name": "Might of Malygos",
        "icon": "inv_misc_head_dragon_blue"
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
    "67108": {
        "name": "Nether Power",
        "icon": "ability_mage_netherwindpresence"
    },
    "67215": {
        "name": "Empowered Darkness",
        "icon": "spell_shadow_darkritual"
    },
    "67218": {
        "name": "Empowered Light",
        "icon": "spell_holy_searinglightpriest"
    },
}

AURAS_CONSUME = {
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
    "53762": {
        "name": "Indestructible Potion",
        "icon": "inv_alchemy_elixir_empty",
    },
    "28714": {
        "name": "Flame Cap",
        "icon": "inv_misc_herb_flamecap",
    },
    "54758": {
        "name": "Hyperspeed Acceleration",
        "icon": "spell_shaman_elementaloath",
    },
}

AURAS_EVENT = {
    "46352": {
        "name": "Fire Festival Fury",
        "icon": "inv_summerfest_fireflower"
    },
    "26393": {
        "name": "Elune's Blessing",
        "icon": "inv_misc_gem_pearl_02"
    },

    "49856": {
        "name": "VICTORY Perfume",
        "icon": "inv_inscription_inkpurple03"
    },
    "49857": {
        "name": "Enchantress Perfume",
        "icon": "inv_inscription_inkpurple04"
    },
    "49858": {
        "name": "Forever Perfume",
        "icon": "inv_inscription_inkpurple02"
    },
    "49861": {
        "name": "STALWART Cologne",
        "icon": "inv_inscription_inkgreen02"
    },
    "49860": {
        "name": "Wizardry Cologne",
        "icon": "inv_inscription_inkgreen04"
    },
    "49859": {
        "name": "Bravado Cologne",
        "icon": "inv_inscription_inkgreen03"
    },

    "29332": {
        "name": "Fire-toasted Bun",
        "icon": "inv_misc_food_11"
    },
    "29333": {
        "name": "Midsummer Sausage",
        "icon": "inv_misc_food_53"
    },
    "29334": {
        "name": "Toasted Smorc",
        "icon": "inv_summerfest_smorc"
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
}
AURAS = AURAS_EXTERNAL | AURAS_CONSUME | AURAS_EVENT


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


def get_raid_buff_count(logs_slice: list[str], flag_filter='SPELL_AURA'):
    auras: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for line in logs_slice:
        if flag_filter not in line:
            continue
        timestamp, flag, _, _, target_guid, _, spell_id, _ = line.split(',', 7)
        if spell_id in AURAS:
            auras[target_guid][spell_id].append((flag, timestamp))

    return auras

def get_auras_uptime(logs_slice, data: dict[str, dict[str, list]]):
    START = to_dt(logs_slice[0])
    END = to_dt(logs_slice[-1])
    DUR = (END-START).total_seconds()

    new_auras: defaultdict[str, dict[str, float]] = defaultdict(dict)

    for target_guid, data1 in data.items():
        for spell_id, data2 in data1.items():
            count = 0
            uptime = 0
            last_apply = None
            for flag, timestamp in data2:
                if flag == "SPELL_AURA_REMOVED":
                    if last_apply is None:
                        last_apply = START
                        count += 1
                    uptime += (to_dt(timestamp)-last_apply).total_seconds()
                    last_apply = None
                elif last_apply is None:
                    count += 1
                    last_apply = to_dt(timestamp)
                elif flag == "SPELL_AURA_REFRESH":
                    count += 1

            if last_apply is not None:
                uptime += (END-last_apply).total_seconds()

            new_auras[target_guid][spell_id] = (count, uptime/DUR)
    
    return new_auras

def get_filtered_info(data):
    return {
        spell_id: spell_info
        for spell_id, spell_info in AURAS.items()
        if spell_id in data
    }


def __test():
    import logs_main
    report_name = "22-07-15--21-01--Safiyah--Lordaeron"
    report = logs_main.THE_LOGS(report_name)
    enc_data = report.get_enc_data()
    s, f = enc_data["The Lich King"][4]
    logs = report.get_logs(s, f)
    q = get_raid_buff_count(logs)
    q2 = get_auras_uptime(logs, q)
    print(q2)
    
if __name__ == "__main__":
    __test()
