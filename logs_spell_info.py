from typing import Dict, List

import constants

@constants.running_time
def get_spell_count(logs_slice: List[str], spell_id_str: str):
    SPELL = "SWING_" if spell_id_str == "1" else "SPELL_"
    spells: Dict[str, Dict[str, Dict[str, int]]] = {}
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
POT_INFO = {
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
    "56350": {
        "name": "Saronite Bomb",
        "icon": "inv_misc_enggizmos_32",
    },
    "54758": {
        "name": "Hyperspeed Acceleration",
        "icon": "spell_shaman_elementaloath",
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
ALL_POTS = set(POT_INFO) - {"28714", }
POTS_VALUE = {'28714', '53909', '28494', '28507', '53908'}

def count_total(data):
    total = {}
    for pot_id in POTS_VALUE:
        for guid, value in data.get(pot_id, {}).items():
            total[guid] = total.get(guid, 0) + value
    total = constants.sort_dict_by_value(total)
    return dict(total)

@constants.running_time
def get_potions_count(logs_slice: List[str], flag=None):
    if flag is None:
        flag = '_SUCCESS'

    potions: Dict[str, Dict[str, int]] = {}
    for line in logs_slice:
        if flag in line:
            _, _, source_guid, _, _, _, spell_id, _ = line.split(',', 7)
            if spell_id in ALL_POTS:
                q = potions.setdefault(spell_id, {})
                q[source_guid] = q.get(source_guid, 0) + 1
        elif "28714" in line and "_APPLIED" in line:
            _, _, _, _, source_guid, _ = line.split(',', 5)
            q = potions.setdefault("28714", {})
            q[source_guid] = q.get(source_guid, 0) + 1

    return potions
