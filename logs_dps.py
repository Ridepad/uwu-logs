from collections import defaultdict

import logs_main

FLAGS = {'SWING_DAMAGE', 'RANGE_DAMAGE', 'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'DAMAGE_SHIELD'}

def get_raw_data(logs: list[str], guids: set[str]):
    data = defaultdict(int)

    for line in logs:
        if "DAMAGE" not in line:
            continue
        _line = line.split(',', 10)
        if _line[2] not in guids:
            continue
        if _line[1] not in FLAGS:
            continue
        data[_line[0][-9:-2]] += int(_line[9])

    return data

# 5% faster idk why
def get_raw_data(logs: list[str], guids: set[str]):
    data = defaultdict(int)

    for line in logs:
        if "DAMAGE" not in line:
            continue
        try:
            timestamp, flag, sGUID, _, _, _, _, _, _, damage, _ = line.split(',', 10)
        except ValueError:
            continue
        if sGUID not in guids:
            continue
        if flag not in FLAGS:
            continue
        data[timestamp[-9:-2]] += int(damage)

    return data

def to_int(s: str):
    minutes, seconds = s.split(":", 1)
    return int(minutes) * 600 + int(seconds.replace('.', ''))

def convert_keys(data: dict[str, int]):
    FIRST_KEY = to_int(list(data)[0])
    for k in list(data):
        new_key = to_int(k) - FIRST_KEY
        if new_key < 0:
            new_key = new_key + 36000
        data[new_key] = data.pop(k)

def convert_keys_to_str(data: dict[int, int]):
    for k in list(data):
        seconds = k % 60
        minutes = k // 60
        data[f"{minutes:0>2}:{seconds:0>2}"] = data.pop(k)

def convert_to_continuous_dps_seconds(data: dict[str, int]):
    DPS = {}
    total_dps = 0
    last_key = list(data)[-1]
    
    for sec_from_start in range(last_key//10+1):
        current_dps = 0
        for tenth_of_sec in range(10):
            current_key = sec_from_start*10+tenth_of_sec
            current_dps += data.get(current_key, 0)

        total_dps = total_dps + current_dps
        currentdps = total_dps / (sec_from_start+1)
        DPS[sec_from_start] = round(currentdps, 1)
    
    return DPS

def get_continuous_dps_seconds(logs: list[str], guids: set[str], convert_keys_to_string=True):
    data = get_raw_data(logs, guids)
    convert_keys(data)
    new_data = convert_to_continuous_dps_seconds(data)
    if convert_keys_to_string:
        convert_keys_to_str(new_data)
    return new_data

def convert_to_continuous_dps_custom(data: dict[int, int], refresh_window=2):
    DPS = {}
    LAST_KEY = list(data)[-1]
    total_dps = 0

    _dps = 0
    
    for sec_from_start in range(LAST_KEY//10+1):
        for tenth_of_sec in range(10):
            current_key = sec_from_start*10+tenth_of_sec
            total_dps += data.get(current_key, 0)
            
            current_sec = current_key + 1
            if current_sec % refresh_window == 0:
                current_dps = total_dps / current_sec * 10
                DPS[current_sec] = round(current_dps, 1)
            
            if current_key == LAST_KEY:
                break

    return DPS

def get_continuous_dps_custom(logs: list[str], guids: set[str], refresh_window=2):
    data = get_raw_data(logs, guids)
    convert_keys(data)
    return convert_to_continuous_dps_custom(data, refresh_window)



def test():
    report = logs_main.THE_LOGS("22-12-30--20-10--Nomadra--Lordaeron")
    encdata = report.get_enc_data()
    s, f = encdata["Saviana Ragefire"][-1]
    s, f = encdata["The Lich King"][-2]
    logs = report.get_logs(s, f)

    guids = report.get_players_and_pets_guids()
    guids = report.get_units_controlled_by("Nomadra")
    dps = get_continuous_dps_custom(logs, guids)
    print(dps)

if __name__ == "__main__":
    test()



# def find_dot(line: str):
#     return line.find(".")

# def find_seconds(line):
#     dot_position = find_dot(line)
#     seconds_start = dot_position - 2
#     return dot_position, seconds_start

# def to_float(s):
#     return float(s[-4:])

# def doshit1(data: dict):
#     last_sec = to_float(list(data)[0]) + 1
#     dps = defaultdict(int)
#     s = 0
#     for k, v in data.items():
#         cur_sec = to_float(k)
#         print(cur_sec, last_sec, cur_sec-last_sec)
#         if cur_sec >= last_sec or cur_sec < 5 and last_sec > 59:
#         # if k[-1] == one_tenth_start:
#             s = s + 1
#             # dps[s] = current_dps
#             # current_dps = 0
#             last_sec = last_sec + 1
#             if last_sec > 60:
#                 last_sec = last_sec - 60

#             last_sec = round(last_sec, 1)

#             # print(last_sec)
#         dps[s] += v
#         # current_dps = current_dps + v
#     print(dps)

# def to_s(number):
#     # ms = number%10
#     # number = number // 10
#     return f"{number//600:0>2}:{number//10%60:0>2}.{number%10}"