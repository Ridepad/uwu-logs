
from constants import running_time
import logs_main

FLAGS = {'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'SWING_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}

def maybe_pet(guids: dict, guid: str):
    # if master_guid:
    #     master_guid = guids.get(master_guid, {}).get('master_guid', master_guid)
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

@running_time
def dmg_to_target(logs: list, guids: dict, filter_by=None):
    g = no_filter_gen(logs) if filter_by is None else filter_gen(logs, filter_by)
    total = {}
    for line in g:
        source_guid = maybe_pet(guids, line[2])
        m = line[1] != 'SWING_DAMAGE'
        try:
            dmg = int(line[6+3*m]) - int(line[7+3*m])
        except:
            print(line)
            dmg = 0
        total[source_guid] = total.get(source_guid, 0) + dmg
    return total

@running_time
def dmg_to_target(logs: list, guids: dict, filter_by=None):
    g = no_filter_gen(logs) if filter_by is None else filter_gen(logs, filter_by)
    total = {}
    for line in g:
        source_guid = maybe_pet(guids, line[2])
        dmg = int(line[9]) - int(line[10])
        total[source_guid] = total.get(source_guid, 0) + dmg
    return total

def combine_same_name(data: dict):
    w = {}
    for guid, v in data.items():
        name = guids[guid]["name"]
        w[name] = w.get(name, 0) + v
    return w

if __name__ == "__main__":
    def sort_dict_by_value(d):
        return dict(sorted(d.items(), key=lambda x: x[1], reverse=True))
    name = '21-09-30--21-06--Inia'
    LOGS = logs_main.THE_LOGS(name)
    guids, _ = LOGS.get_guids()
    logs = LOGS.get_logs()
    enc_data = LOGS.get_enc_data()
    s,f = enc_data["rotface"][-1]
    logs = logs[s:f]
    total = dmg_to_target(logs, guids)
    total = combine_same_name(total)
    total = sort_dict_by_value(total)
    for x, v in total.items():
        v = f"{v:>12,}".replace(',', ' ')
        # n = guids[x]["name"]
        # print(f'{x:<25}{v} {n}')
        print(f'{x:<25}{v}')