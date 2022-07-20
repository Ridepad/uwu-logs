from collections import defaultdict
from time import perf_counter
import dmg_useful
import logs_main
import constants
from logs_spell_info import AURAS_EXTERNAL, AURAS_CONSUME, AURAS_EVENT

z_spells = [AURAS_EXTERNAL, AURAS_CONSUME]
z_names = ["e", "c", "o"]


def f_auras(auras, spec):
    if spec == 25 and "63848" in auras:
        del auras["63848"]
    elif spec in range(12,16) and "54646" in auras:
        del auras["54646"]
    
    zz = {}
    for spell_id, (count, uptime) in auras.items():
        for n, a in enumerate(z_spells):
            if spell_id in a:
                uptime = round(uptime*100, 1)
                zz[spell_id] = [count, uptime, n]
                break
    return zz

def make_top_dict(report: logs_main.THE_LOGS, dmg, specs, duration, auras):
    players = report.get_players_guids()
    report_name = report.NAME
    return [
        {
            'i': guid,
            'n': players[guid],
            'r': report_name,
            'u': value,
            'd': round(value/duration, 2),
            't': duration,
            's': specs[guid],
            'a': f_auras(auras[guid], specs[guid])
        }
        for guid, value in dmg.items()
    ]

def find_kill(segments):
    for segment_info in segments:
        if segment_info['attempt_type'] == 'kill':
            yield segment_info

def doshit(report: logs_main.THE_LOGS, boss_name: str, kill_segment: dict):
    s, f = kill_segment['start'], kill_segment['end']
    boss_guid_id = report.name_to_guid(boss_name)
    targets = dmg_useful.get_all_targets(boss_name, boss_guid_id)
    
    all_data = report.useful_damage(s, f, targets["all"], boss_name)

    # print(all_data)
    if "Valks Useful" in all_data:
        targets["useful"]["Valks Useful"] = "Valks Useful"
    
    guids = report.get_all_guids()
    all_data = dmg_useful.combine_pets_all(all_data, guids, trim_non_players=True, ignore_abom=True)
    # print(json.dumps(all_data))
    # for q,w in all_data.items():
    #     print(q, w)
    #     report.pretty_print_players_data(w)
    #     print(q)
    #     break

    targets_useful_dmg = dmg_useful.combine_targets(all_data, targets["useful"])
    # print(json.dumps(targets_useful_dmg))
    # print('targets_useful_dmg')
    # report.pretty_print_players_data(targets_useful_dmg)


    specs = report.get_players_specs_in_segments(s, f)
    # print('specs')
    # print(specs)
    dur = report.get_fight_duration(s, f)
    auras = report.auras_info(s, f)
    top = make_top_dict(report, targets_useful_dmg, specs, dur, auras)
    # targets_useful_dmg = report.add_total_and_names(targets_useful_dmg)
    
    return top

def make_report_top(name: str):
    report = logs_main.THE_LOGS(name)
    top_path = report.relative_path('top.json')
    # if os.path.isfile(top_path):
    #     return
    print(name)
    pc = perf_counter()
    top = {}
    segments = report.format_attempts()
    for boss_name, boss_segments in segments.items():
        boss_top = top.setdefault(boss_name, {})
        for kill_segment in find_kill(boss_segments):
            diff = kill_segment['diff']
            data = doshit(report, boss_name, kill_segment)
            boss_top[diff] = data

    constants.json_write(top_path, top, indent=None)
    print(f'{name:<50} | Done in {constants.get_ms(pc):>6} ms')

def main_wrap(name):
    try:
        make_report_top(name)
    # except IndexError:
        # constants.LOGGER_MAIN.debug(f'{name}')
        # print(name)
    except Exception:
        constants.LOGGER_MAIN.exception(f'{name}')


if __name__ == "__main__":
    # make_report_top('22-07-15--21-01--Safiyah--Lordaeron')
    constants.redo_data(main_wrap, filter="Lordaeron")
