from collections import defaultdict
import dmg_useful
import logs_main
import logs_check_difficulty
import json
import constants

__top = {
    'boss': {
        'diff': [
            {'guid', 'name', 'date', 'dmg', 'useful', 'dps', 'duration', 'spec', 'tot', 'hyst', 'pi'}
        ]
    }
}
def make_top_dict(report: logs_main.THE_LOGS, dmg, specs, duration):
    top = []
    players = report.get_players_guids()
    for guid, value in dmg.items():
        name = players[guid]
        t = {
            'guid': guid,
            'name': name,
            'report': report.NAME,
            'useful': value,
            'dps': round(value/duration, 2),
            'duration': duration,
            'spec': specs[guid]
        }
        top.append(t)
    return top

def find_kill(segments):
    for segment_info in segments:
        if segment_info['attempt_type'] == 'kill':
            yield segment_info

def doshit(report: logs_main.THE_LOGS, boss_name: str, kill_segment: dict):
    s, f = kill_segment['start'], kill_segment['end']
    boss_guid_id = report.name_to_guid(boss_name)
    targets_useful, targets_all = dmg_useful.get_all_targets(boss_name, boss_guid_id)
    
    all_data = report.useful_damage(s, f, targets_all, boss_name)

    # print(all_data)
    if "Valks Useful" in all_data:
        targets_useful["Valks Useful"] = "Valks Useful"
    
    guids = report.get_all_guids()
    all_data = dmg_useful.combine_pets_all(all_data, guids, trim_non_players=True, ignore_abom=True)
    # print(json.dumps(all_data))
    # for q,w in all_data.items():
    #     print(q, w)
    #     report.pretty_print_players_data(w)
    #     print(q)
    #     break

    targets_useful_dmg = dmg_useful.combine_targets(all_data, targets_useful)
    # print(json.dumps(targets_useful_dmg))
    # print('targets_useful_dmg')
    # report.pretty_print_players_data(targets_useful_dmg)


    specs = report.get_players_specs_in_segments(s, f)
    # print('specs')
    # print(specs)
    dur = report.get_fight_duration(s, f)
    top = make_top_dict(report, targets_useful_dmg, specs, dur)
    # targets_useful_dmg = report.add_total_and_names(targets_useful_dmg)
    return top

def make_report_top(name: str):
    if 'Deydraenna' in name:
        return
    report = logs_main.THE_LOGS(name)
    top = {}
    segments = report.format_attempts()
    for boss_name, boss_segments in segments.items():
        boss_top = top.setdefault(boss_name, {})
        for kill_segment in find_kill(boss_segments):
            diff = kill_segment['diff']
            data = doshit(report, boss_name, kill_segment)
            boss_top[diff] = data

    top_path = report.relative_path('top.json')
    constants.json_write(top_path, top, indent=None)

if __name__ == "__main__":
    constants.redo_data(make_report_top, startfrom=-250)
