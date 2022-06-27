from collections import defaultdict
import json
import constants

folders = constants.get_folders('LogsDir')
folders = folders[::-1]
folders = folders[:250]
TOP = defaultdict(lambda: defaultdict(list))
for name in folders[::-1]:
    if 'Deydraenna' in name:
        continue
    topname = f"LogsDir/{name}/top.json"
    top = constants.json_read(topname)
    for boss_name, boss_diffs in top.items():
        print(boss_name)
        for diff_name, data in boss_diffs.items():
            TOP[boss_name][diff_name].extend(data)
        # boss_top = TOP.setdefault(boss_name, {})
        # for kill_segment in find_kill(boss_segments):
        #     diff = kill_segment['diff']
        #     # if kill_segment['diff'] != '25H':
        #         # continue
        #     # print()
        #     # print(boss_name, kill_segment['diff'])
        #     data = doshit(report, boss_name, kill_segment)
        #     boss_top[diff] = data
    # break
# alltoppath = 
constants.json_write('full_top', TOP, indent=None)
# print(json.dumps(TOP))