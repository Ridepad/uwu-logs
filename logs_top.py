import logs_main
import dmg_useful
import dmg_heals
from constants import add_new_numeric_data, sort_dict_by_value
import logs_player_class
import json

PLAYERS = {}
'''
p = {
    boss: {
        diff: {
            guid: {
                date: dmg
}
p = {
    boss: [
        {"reportname":name, diff:25h, duration:int, dmg:{}}
    ]
}
'''


def pretty_print(report, data: dict[str, dict[str, int]]):
    print()
    specs = data['specs']
    p_top = data['players']
    p_top = sort_dict_by_value(p_top)
    players = report.get_players_guids()
    for guid, d in p_top.items():
        if guid not in players:
            continue
        if guid not in specs:
            print(f'{guid} not in specs')
            continue
        print(f"{players[guid]:<12} {specs[guid]:<10} {d:>9}")

def get_dmg(report: logs_main.THE_LOGS, segment: dict[str, str], boss_name: str):
    DATA = {}

    boss_guid_id = report.name_to_guid(boss_name)
    targets_useful, targets_all = dmg_useful.get_all_targets(boss_name, boss_guid_id)
    # print(targets_useful)
    s = segment['start']
    f = segment['end']
    logs_slice = report.get_logs(s, f)
    dmg = dmg_heals.parse_dmg_targets(logs_slice, targets_useful)
    specific_useful = dmg_useful.specific_useful_combined(logs_slice, boss_name)
    add_new_numeric_data(dmg, specific_useful)

    guids = report.get_all_guids()
    data = dmg_heals.add_pets_guids(dmg, guids)
    DATA['damage'] = data['players']

    # print(data['players'])
    classes = report.get_classes()
    players = report.get_players_guids(filter_guids=data['players'])
    DATA['specs'] = logs_player_class.get_specs_guids(logs_slice, players, classes)

    DATA['duration'] = report.get_fight_duration(s, f)

    # data['name']

    return DATA

    
def get_lk(report: logs_main.THE_LOGS):
    boss_name = "Blood Prince Council"
    boss_name = "The Lich King"
    sep = report.SEGMENTS_SEPARATED
    # print(sep)
    boss_segs = sep[boss_name]
    if '25H' not in boss_segs:
        return
    for segment in boss_segs['25H']:
        if segment['attempt_type'] == 'kill':
            data = get_dmg(report, segment, boss_name)
            print(json.dumps(data))
            pretty_print(report, data)
            
def get_data(report: logs_main.THE_LOGS):
    sep = report.SEGMENTS_SEPARATED
    for boss_name, diff_data in sep.items():
        for diff_id, segments in diff_data.items():
            for segment in segments:
                if segment['attempt_type'] == 'kill':
                    data = get_dmg(report, segment, boss_name)
                    data['diff'] = diff_id
                    pretty_print(report, data)

def main():
    name = "22-04-27--21-02--Safiyah"
    report = logs_main.THE_LOGS(name)
    enc_data = report.get_enc_data()
    boss = "The Lich King"
    # s, f = enc_data[boss][-2]
    # logs = report.get_logs(s, f)
    players = report.get_players_guids()
    PLAYERS.update(players)
    classes = report.get_classes()
    # ud = report.useful_damage()
    report.format_attempts()
    get_lk(report)
    # for x, y in specs.items():
        # print(f"{players[x]:<12} {y[0]}")


if __name__ == "__main__":
    main()