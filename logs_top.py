import os
from time import perf_counter

import file_functions
import logs_dmg_heals
import logs_dmg_useful
import logs_main
from constants import LOGGER_REPORTS, get_ms_str, running_time
from logs_spell_info import AURAS_BOSS_MECHANICS, AURAS_CONSUME, AURAS_EXTERNAL, MULTISPELLS_D

Z_SPELLS = [AURAS_EXTERNAL, AURAS_CONSUME, AURAS_BOSS_MECHANICS]

HUNGER_FOR_BLOOD = "63848"
FOCUS_MAGIC = "54646"
BATTLE_SQUAWK = "23060"
SPECS_NO_USE_FOR_CHICKEN = {*range(12, 16), *range(20, 24), 29, 31, 33, 35}

def f_auras(auras: dict[str, tuple[int, float]], spec: int):
    if spec == 25 and HUNGER_FOR_BLOOD in auras:
        del auras[HUNGER_FOR_BLOOD]
    elif spec in range(12, 16) and FOCUS_MAGIC in auras:
        del auras[FOCUS_MAGIC]
    elif spec in SPECS_NO_USE_FOR_CHICKEN and BATTLE_SQUAWK in auras:
        del auras[BATTLE_SQUAWK]
    
    zz: dict[str, list[int, float, int]] = {}
    for spell_id, (count, uptime) in auras.items():
        spell_id = MULTISPELLS_D.get(spell_id, spell_id)
        for n, auras_dict in enumerate(Z_SPELLS):
            if spell_id not in auras_dict:
                continue
            uptime = round(uptime*100, 1)
            if spell_id in zz:
                count += zz[spell_id][0]
                uptime += zz[spell_id][1]
            zz[spell_id] = [count, uptime, n]
            break
    return zz

def find_kill(segments):
    for segment_info in segments:
        if segment_info['attempt_type'] == 'kill' and segment_info['diff'] != "TBD":
            yield segment_info

@running_time
def make_boss_top(report: logs_main.THE_LOGS, boss_name: str, kill_segment: dict):
    def is_player(guid):
        if guid in PLAYERS:
            return True
        LOGGER_REPORTS.error(f"{report.NAME} {boss_name} Missing player {guid}")
    
    S = kill_segment['start']
    F = kill_segment['end']
    GUIDS = report.get_all_guids()
    PLAYERS = report.get_players_guids()
    SPECS = report.get_players_specs_in_segments(S, F)
    DURATION = report.get_slice_duration(S, F)
    AURAS = report.auras_info(S, F)

    boss_guid_id = report.name_to_guid(boss_name)
    targets = logs_dmg_useful.get_all_targets(boss_name, boss_guid_id)
    targets_useful = targets["useful"]

    useful_data = report.useful_damage(S, F, targets["all"], boss_name)
    for target_name in useful_data["specific"]:
        targets_useful[target_name] = target_name
    useful_damage_combined = logs_dmg_useful.combine_pets_all(useful_data["damage"], GUIDS, trim_non_players=True, ignore_abom=True)
    targets_useful_dmg = logs_dmg_useful.get_total_damage(useful_damage_combined, targets_useful)
    
    logs_slice = report.get_logs(S, F)
    players_and_pets = report.get_players_and_pets_guids()
    total_dmg = logs_dmg_heals.parse_only_dmg_no_friendly(logs_slice, players_and_pets)
    data_with_pets_d = logs_dmg_heals.add_pets_guids(total_dmg, GUIDS)
    data_with_pets = data_with_pets_d["players"]

    return [
        {
            'i': guid[-7:],
            'n': PLAYERS[guid],
            'r': report.NAME,
            'ua': useful,
            'ud': round(useful/DURATION, 2),
            'ta': data_with_pets[guid],
            'td': round(data_with_pets[guid]/DURATION, 2),
            't': DURATION,
            's': SPECS[guid],
            'a': f_auras(AURAS[guid], SPECS[guid])
        }
        for guid, useful in targets_useful_dmg.items()
        if is_player(guid)
    ]

@running_time
def make_report_top(name: str, rewrite=False):
    print(name)
    report = logs_main.THE_LOGS(name)
    top_path = report.relative_path('top.json')
    if not rewrite and os.path.isfile(top_path):
        return
    
    pc = perf_counter()
    top = {}
    segments = report.get_segments_data()
    for boss_name, boss_segments in segments.items():
        boss_top = top.setdefault(boss_name, {})
        for kill_segment in find_kill(boss_segments):
            diff = kill_segment['diff']
            data = make_boss_top(report, boss_name, kill_segment)
            boss_top[diff] = data

    file_functions.json_write(top_path, top, indent=None)
    LOGGER_REPORTS.info(f'{get_ms_str(pc)} | {name:<50} | Done top')
    return top

def main_wrap(name):
    try:
        make_report_top(name)
    except Exception:
        LOGGER_REPORTS.exception(name)
