
from typing import List
import constants
import _main

FLAGS = {'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'SWING_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}

# 0xF150008F01 Val'kyr Shadowguard

# 0xF130008EF5 The Lich King
# 0xF130008F19 Ice Sphere
# 0xF130008F5D Raging Spirit
# 0xF130009916 Wicked Spirit

# 0xF13000933F Drudge Ghoul
# 0xF130009342 Shambling Horror
# 0xF1300093A7 Vile Spirit

IGNORE = {"0xF13000933F", "0xF1300093A7", "0xF130009342"}
USEFUL = {"0xF130008EF5", "0xF130008F19", "0xF130008F5D", "0xF130009916"}
# raw dmg overall dmg usefull dmg

def if_master(guids, guid):
    return guids[guid].get('master_guid', guid)

def filter_gen(logs: list, filter_by: str):
    i = 4 if filter_by.startswith("0x") else 5
    for line in logs:
        if filter_by in line:
            line = line.split(',')
            if line[1] in FLAGS and line[i] == filter_by:
                yield line

def no_filter_gen(logs: list):
    for line in logs:
        line = line.split(',')
        if line[1] in FLAGS:
            yield line

def main(name):
    report = _main.THE_LOGS(name)
    guids, players = report.get_guids()
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    s,f = enc_data["The Lich King"][-3]
    logs_slice = logs[s:f]
    return logs_slice

def get_dmg(logs_slice, filter_by=None):
    g = no_filter_gen(logs_slice) if filter_by is None else filter_gen(logs_slice, filter_by)
    all_dmg = {x: {} for x in USEFUL}
    for line in g:
        if line[4] in players:
            continue
        target_guid = line[4][:-6]
        if target_guid not in USEFUL:
            continue
        source_guid = if_master(guids, line[2])
        # if source_guid not in players:
            # continue
        d = all_dmg[target_guid]
        d[source_guid] = d.get(source_guid, 0) + int(line[9])
    return all_dmg, players

def sort_dict_by_value(d: dict):
    return sorted(d.items(), key=lambda x: x[1], reverse=True)

def add_space(v):
    return f"{v:,}".replace(',', ' ')

if __name__ == "__main__":
    name = '21-09-30--21-06--Inia'
    all_dmg, players = main(name)
    a = all_dmg['0xF130008F5D']
    a = sort_dict_by_value(a)
    for x,y in a:
        print(f"{players[x]:<12} {add_space(y):>10}")