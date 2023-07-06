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
    # return [
    #     [int(spell_id), *spell_data]
    #     for spell_id, spell_data in zz.items()
    # ]

def find_kill(segments):
    for segment_info in segments:
        if segment_info['attempt_type'] == 'kill' and segment_info['diff'] != "TBD":
            yield segment_info

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
    targets_all = targets["all"]
    targets_useful = targets["useful"]

    data = report.useful_damage(S, F, targets_all, boss_name)
    for target_name in data["useful"]:
        targets_useful[target_name] = target_name
    
    useful_damage = data["damage"] | data["useful"]
    all_data_useful = logs_dmg_useful.combine_pets_all(useful_damage, GUIDS, trim_non_players=True, ignore_abom=True)
    dmg_useful = logs_dmg_useful.get_total_damage(all_data_useful, targets_useful)

    # all_data = logs_dmg_useful.combine_pets_all(data["damage"], GUIDS, trim_non_players=True)
    # dmg_total = logs_dmg_useful.get_total_damage(all_data)

    logs_slice = report.get_logs(S, F)
    pp = report.get_players_and_pets_guids()
    dmg_total = logs_dmg_heals.parse_dmg_all_no_friendly(logs_slice, pp)
    dmg_total = logs_dmg_useful.combine_pets(dmg_total, GUIDS, trim_non_players=True)

    return [
        {
            'i': guid[-7:],
            'n': PLAYERS[guid],
            'r': report.NAME,
            'ua': useful,
            'ud': round(useful/DURATION, 2),
            'ta': dmg_total[guid],
            'td': round(dmg_total[guid]/DURATION, 2),
            # 'u': useful,
            # 'f': dmg_total[guid],
            't': DURATION,
            's': SPECS[guid],
            'a': f_auras(AURAS[guid], SPECS[guid])
        }
        for guid, useful in dmg_useful.items()
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
    for boss_name, boss_segments in report.SEGMENTS.items():
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

if __name__ == "__main__":
    def get_player(data, name):
        for x in data:
            if x["n"] == name:
                return x
        return data[0]
    a = make_report_top("23-04-28--21-07--Safiyah--Lordaeron", rewrite=True)
    # print(a)
    a = r"F:\Python\uwulogs\LogsDir\23-04-28--21-07--Safiyah--Lordaeron\top.json"
    b = r"F:\Python\uwulogs\LogsDir\23-04-28--21-07--Safiyah--Lordaeron\top - Copy.json"
    import json
    with open(a) as f:
        aj = json.load(f)
    with open(b) as f:
        bj = json.load(f)

    # print(aj['The Lich King'])
    print(get_player(aj['The Lich King']['25H'], "Safiyah"))
    print(get_player(bj['The Lich King']['25H'], "Safiyah"))
    print()
    print(get_player(aj['Blood Prince Council']['25H'], "Safiyah"))
    print(get_player(bj['Blood Prince Council']['25H'], "Safiyah"))
    print()
    print(get_player(aj['Professor Putricide']['25H'], "Safiyah"))
    print(get_player(bj['Professor Putricide']['25H'], "Safiyah"))
    print()
    print(get_player(aj['Professor Putricide']['25H'], "Zpevacik"))
    print(get_player(bj['Professor Putricide']['25H'], "Zpevacik"))
    # print(aj['The Lich King']['25H'][0])
    # print(bj['The Lich King']['25H'][0])