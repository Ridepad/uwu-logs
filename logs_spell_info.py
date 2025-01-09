from collections import defaultdict

import logs_base
from constants import FLAG_ORDER
from h_debug import Loggers, running_time
from h_other import (
    add_new_numeric_data,
    sort_dict_by_value,
    is_player,
)

LOGGER_REPORTS = Loggers.reports

def get_other_count(logs_slice: list[str], _filter: str):
    spells = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for line in logs_slice:
        if _filter not in line:
            continue

        _, flag, _, source_name, _, target_name, _ = line.split(',', 6)

        spells[flag][source_name][target_name] += 1
    return spells

@running_time
def get_spell_count(logs_slice: list[str], spell_id_str: str) -> defaultdict[str, defaultdict[str, defaultdict[str, int]]]:
    if spell_id_str == "1":
        return get_other_count(logs_slice, "SWING")
    if spell_id_str == "75":
        return get_other_count(logs_slice, "RANGE")

    spell_id_str_commas_wrap = f",{spell_id_str},"
    spells = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for line in logs_slice:
        if spell_id_str_commas_wrap not in line:
            continue
        
        _, flag, _, source_name, _, target_name, s_id, etc = line.split(',', 7)
        
        if s_id != spell_id_str:
            if "_DISPEL" not in flag:
                continue
            _, _, s_id, _ = etc.split(',', 3)
            if s_id != spell_id_str:
                continue

        spells[flag][source_name][target_name] += 1
    return spells

MULTISPELLS = {
    # Essence of the Blood Queen
    "71531": [
        "70879", "71530", "71525", "71531",
        "70867", "71532", "71473", "71533",
        "70871", "70949"
    ],
    # Malleable Goo
    "72550": [
        "72297", "72549", "72548", "72550",
        "70853", "72873", "72458", "72874",
    ],
    # Vile Gas
    "73020": [
        "69240", "73019", "71218", "73020",
        "72272", "72273",
        # "69244", "73173", "71288", "73174"
    ],
    # Mutated Infection
    "73023": [
        "69674", "73022", "71224", "73023"
    ],
    # Volatile Ooze Adhesive - Green Target
    "72838": [
        "70447", "72837", "72836", "72838"
    ],
    # Gaseous Bloat - Red Target
    "72833": [
        "70672", "72832", "72455", "72833"
    ],
    # Chocking Gas
    "72620": [
        "71278", "72619", "72460", "72620",
        "71279", "72621", "72459", "72622",
    ],
    # Unbound Plague
    "72856": [
        "70911", "72855", "72854", "72856"
    ],
    # Harvest Soul
    "74297": [
        "68980", "74296", "74325", "74297"
    ],
    # Legion Flame
    "68125": [
        "66197", "68124", "68123", "68125"
    ],
    # Mistress' Kiss
    "67907": [
        "66334", "67906", "67905", "67907"
    ],
}
MULTISPELLS_D = {y: x for x, spells in MULTISPELLS.items() for y in spells}

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
    "28508": {
        "name": "Destruction Potion",
        "icon": "inv_potion_107",
    },
    "28714": {
        "name": "Flame Cap",
        "icon": "inv_misc_herb_flamecap",
    },
    "43186": {
        "name": "Runic Mana Potion",
        "icon": "inv_alchemy_elixir_02",
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
    "9512": {
        "name": "Thistle Tea",
        "icon": "inv_drink_milk_05",
    },
    "53762": {
        "name": "Indestructible Potion",
        "icon": "inv_alchemy_elixir_empty",
    },
    "53750": {
        "name": "Crazy Alchemist's Potion",
        "icon": "inv_potion_27",
    },
    "28499": {
        "name": "Endless Mana Potion",
        "icon": "inv_alchemy_endlessflask_04",
    },
    "43185": {
        "name": "Healing Potion",
        "icon": "inv_alchemy_elixir_05",
    },
}

AURAS_EXTERNAL = {
    "19753": {
        "name": "Divine Intervention",
        "icon": "spell_nature_timestop",
    },
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
    "58427": {
        "name": "Overkill",
        "icon": "ability_hunter_rapidkilling",
    },
    "54153": {
        "name": "Judgements of the Pure",
        "icon": "ability_paladin_judgementofthepure",
    },
    "51800": {
        "name": "Might of Malygos",
        "icon": "inv_misc_head_dragon_blue"
    },
    "51777": {
        "name": "Arcane Focus",
        "icon": "spell_arcane_teleportironforge"
    },
    "51605": {
        "name": "Zeal",
        "icon": "spell_shadow_shadowworddominate"
    },
    "44335": {
        "name": "Energy Feedback",
        "icon": "spell_arcane_arcane04"
    },
    "72553": {
        "name": "Gastric Bloat",
        "icon": "achievement_boss_festergutrotface"
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

AURAS_BOSS_MECHANICS = {
    "69065": {
        "name": "Impaled",
        "icon": "inv_misc_bone_03"
    },
    "71289": {
        "name": "Dominate Mind",
        "icon": "inv_belt_18"
    },
    "71237": {
        "name": "Curse of Torpor",
        "icon": "ability_creature_cursed_03"
    },
    "69279": {
        "name": "Gas Spore",
        "icon": "spell_shadow_creepingplague"
    },
    "72550": {
        "name": "Malleable Goo",
        "icon": "inv_misc_herb_evergreenmoss"
    },
    "73020": {
        "name": "Vile Gas",
        "icon": "ability_creature_cursed_01"
    },
    "73023": {
        "name": "Mutated Infection",
        "icon": "ability_creature_disease_02"
    },
    "74118": {
        "name": "Ooze Variable",
        "icon": "inv_inscription_inkgreen03"
    },
    "74119": {
        "name": "Gas Variable",
        "icon": "inv_inscription_inkorange01"
    },
    "72838": {
        "name": "Volatile Ooze Adhesive",
        "icon": "ability_warlock_chaosbolt"
    },
    "72833": {
        "name": "Gaseous Bloat",
        "icon": "spell_holiday_tow_spicecloud"
    },
    "72856": {
        "name": "Unbound Plague",
        "icon": "spell_shadow_corpseexplode"
    },
    "72620": {
        "name": "Choking Gas",
        "icon": "ability_creature_cursed_01"
    },
    "71265": {
        "name": "Swarming Shadows",
        "icon": "ability_rogue_shadowdance"
    },
    "71340": {
        "name": "Pact of the Darkfallen",
        "icon": "spell_shadow_destructivesoul"
    },
    "69762": {
        "name": "Unchained Magic",
        "icon": "spell_arcane_focusedpower"
    },
    "70157": {
        "name": "Ice Tomb",
        "icon": "spell_frost_frozencore"
    },
    "74297": {
        "name": "Harvest Soul",
        "icon": "spell_deathknight_strangulate"
    },
    "74795": {
        "name": "Mark of Consumption",
        "icon": "spell_shadow_sealofkings"
    },
    "74567": {
        "name": "Mark of Combustion",
        "icon": "spell_fire_sealoffire"
    },
    "67907": {
        "name": "Mistress' Kiss",
        "icon": "spell_shadow_soothingkiss"
    },
    "68125": {
        "name": "Legion Flame",
        "icon": "spell_fire_felimmolation"
    },
    "66283": {
        "name": "Spinning Pain Spike",
        "icon": "spell_shadow_shadowmend"
    },
    "74509": {
        "name": "Repelling Wave",
        "icon": "spell_fire_playingwithfire"
    },
    "74456": {
        "name": "Conflagration",
        "icon": "inv_misc_orb_05"
    },
    "74384": {
        "name": "Intimidating Roar",
        "icon": "ability_golemthunderclap"
    },
    "74531": {
        "name": "Tail Lash",
        "icon": "ability_criticalstrike"
    },
}

AURAS = AURAS_EXTERNAL | AURAS_CONSUME | AURAS_BOSS_MECHANICS
AURAS |= {spell_id: AURAS[spell_id_hm] for spell_id, spell_id_hm in MULTISPELLS_D.items()}

POT_GROUP = {
    "67490": "43186",
    "67489": "43185",
}

ALL_POTS = set(ITEM_INFO) | set(POT_GROUP)
ALL_POTS.discard("28714")
POTS_VALUE = {
    "53908",
    "53909",
    "28494",
    "28507",
    "28508",
    "28714",
    "43186",
}

def count_total(data: dict[str, dict[str, int]]):
    total: defaultdict[str, int] = defaultdict(int)
    for pot_id in ALL_POTS:
        if pot_id in data:
            for guid, value in data[pot_id].items():
                total[guid] += value
    return total

def count_valuable(data: dict[str, dict[str, int]]):
    total: defaultdict[str, int] = defaultdict(int)
    for pot_id in POTS_VALUE:
        if pot_id in data:
            for guid, value in data[pot_id].items():
                total[guid] += value
    return total

@running_time
def get_potions_count(logs_slice: list[str]):
    potions: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for line in logs_slice:
        if '_SUC' in line:
            _, _, source_guid, _, _, _, spell_id, _ = line.split(',', 7)
            if spell_id in ALL_POTS:
                if spell_id in POT_GROUP:
                    spell_id = POT_GROUP[spell_id]
                potions[spell_id][source_guid] += 1
        elif "28714" in line and "_APPLIED" in line:
            source_guid = line.split(',', 5)[4]
            potions["28714"][source_guid] += 1

    return potions


class Consumables(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def potions_info(self, s, f) -> dict[str, dict[str, int]]:
        logs_slice = self.LOGS[s:f]
        return get_potions_count(logs_slice)
    
    def potions_all(self, segments):
        potions = defaultdict(lambda: defaultdict(int))
        players: set[str] = set()

        for s, f in segments:
            _potions = self.potions_info(s, f)
            for spell_id, sources in _potions.items():
                add_new_numeric_data(potions[spell_id], sources)
                
            _specs = self.get_players_specs_in_segments(s, f)
            players.update(_specs)
        
        p_value = count_valuable(potions)
        for guid in players:
            if guid not in p_value:
                p_value[guid] = 0
        p_value = self.sort_data_guids_by_name(p_value)

        p_total = count_total(potions)
        p_total = self.sort_data_guids_by_name(p_total)

        p_total |= p_value
        p_total = sort_dict_by_value(p_total)
        p_total = self.convert_dict_guids_to_names(p_total)
        
        for spell_id, sources in potions.items():
            potions[spell_id] = self.convert_dict_guids_to_names(sources)

        return {
            "ITEM_INFO": ITEM_INFO,
            "ITEMS_TOTAL": p_total,
            "ITEMS": potions,
        }

class SpellCount(logs_base.THE_LOGS):
    @running_time
    def get_spell_count(self, s, f, spell_id_str):
        logs_slice = self.LOGS[s:f]
        return get_spell_count(logs_slice, spell_id_str)
    
    def spell_count_all(self, segments, spell_id: str):
        def sort_by_total(data: dict):
            return dict(sorted(data.items(), key=lambda x: x[1]["Total"], reverse=True))
        
        spell_id = spell_id.replace("-", "")
        all_spells = self.get_spells()
        if int(spell_id) not in all_spells:
            LOGGER_REPORTS.error(f"{spell_id} not in spells")
            return {
                "SPELLS": {},
            }
        
        spells_data: dict[str, dict[str, dict[str, int]]] = {}
        spells_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        all_targets: list[str] = ["Total", ]
        for s, f in segments:
            print(s)
            s = self.find_shifted_log_line(s, -10)
            print(s)
            _segment_data = self.get_spell_count(s, f, spell_id)
            for flag, sources in _segment_data.items():
                for source_name, targets in sources.items():
                    for target_name, value in targets.items():
                        spells_data[flag][source_name]["Total"] += value
                        spells_data[flag][source_name][target_name] += value
                        if target_name not in all_targets:
                            all_targets.append(target_name)

        for flag in FLAG_ORDER:
            if flag in spells_data:
                spells_data[flag] = sort_by_total(spells_data.pop(flag))

        s_id = abs(int(spell_id))
        SPELL = self.SPELLS[s_id]

        return {
            "SPELLS": spells_data,
            "TARGETS": all_targets,
            "SPELL_ID": spell_id,
            "SPELL_NAME": SPELL.name,
            "SPELL_ICON": SPELL.icon,
            "SPELL_COLOR": SPELL.color,
        }

class _TargetBuffCount(list[tuple[str, str]]):
    pass

def get_raid_buff_count(logs_slice: list[str], flag_filter='SPELL_AURA'):
    auras = defaultdict(lambda: defaultdict(_TargetBuffCount))
    for line in logs_slice:
        if flag_filter not in line:
            continue
        timestamp, flag, _, _, target_guid, _, spell_id, _ = line.split(',', 7)
        if spell_id in AURAS:
            spell_id = MULTISPELLS_D.get(spell_id, spell_id)
            auras[target_guid][spell_id].append((flag, timestamp))

    return auras

def get_filtered_info(data):
    return {
        spell_id: spell_info
        for spell_id, spell_info in AURAS.items()
        if spell_id in data
    }

class _TargetAuraUptime(dict[str, tuple[int, float]]):
    pass

class AuraUptime(logs_base.THE_LOGS):
    def iter_spell(self, data: list[str, str]):
        count = 0
        uptime = 0.0
        start = None
        for flag, timestamp in data:
            if start is None:
                if flag == "SPELL_AURA_APPLIED":
                    start = timestamp
                    count += 1
            elif flag == "SPELL_AURA_REMOVED":
                uptime += self.get_timedelta_seconds(start, timestamp)
                start = None
            else:
                count += 1
        
        return count, uptime

    def get_auras_uptime(self, logs_slice, data: dict[str, dict[str, _TargetBuffCount]]):
        first_line = logs_slice[0]
        last_line = logs_slice[-1]
        DUR = self.get_timedelta_seconds(first_line, last_line)

        new_auras = defaultdict(_TargetAuraUptime)

        for target_guid, spells in data.items():
            for spell_id, spell_data in spells.items():
                if spell_data[0][0] != "SPELL_AURA_APPLIED":
                    spell_data.insert(0, ("SPELL_AURA_APPLIED", first_line))
                if spell_data[-1][0] != "SPELL_AURA_REMOVED":
                    spell_data.append(("SPELL_AURA_REMOVED", last_line))
                count, uptime = self.iter_spell(spell_data)
                new_auras[target_guid][spell_id] = (count, uptime/DUR)
        
        return new_auras

    @logs_base.cache_wrap
    def auras_info(self, s, f):
        logs_slice = self.LOGS[s:f]
        data = get_raid_buff_count(logs_slice)
        return self.get_auras_uptime(logs_slice, data)

    def auras_info_all(self, segments, trim_non_players=True):
        auras_uptime = defaultdict(lambda: defaultdict(list))
        auras_count = defaultdict(lambda: defaultdict(int))

        for s, f in segments:
            _auras = self.auras_info(s, f)
            for guid, aura_data in _auras.items():
                if trim_non_players and not is_player(guid):
                    continue
                for spell_id, (count, uptime) in aura_data.items():
                    auras_count[guid][spell_id] += count
                    auras_uptime[guid][spell_id].append(uptime)

        aura_info_set = set()
        auras_uptime_formatted = defaultdict(lambda: defaultdict(float))
        for guid, aura_data in auras_uptime.items():
            for spell_id, uptimes in aura_data.items():
                aura_info_set.add(spell_id)
                v = sum(uptimes) / len(uptimes) * 100
                auras_uptime_formatted[guid][spell_id] = f"{v:.2f}"
        
        self.add_missing_players(auras_count, {})
        self.add_missing_players(auras_uptime, {})

        auras_count_with_names = self.convert_dict_guids_to_names(auras_count)
        auras_uptime_with_names = self.convert_dict_guids_to_names(auras_uptime_formatted)

        filtered_aura_info = get_filtered_info(aura_info_set)

        return {
            "AURA_UPTIME": auras_uptime_with_names,
            "AURA_COUNT": auras_count_with_names,
            "AURA_INFO": filtered_aura_info,
        }

