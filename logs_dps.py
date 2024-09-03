from collections import defaultdict

import logs_base
from c_bosses import BOSSES_FROM_HTML
from h_debug import running_time

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
def get_raw_data(logs: list[str], source_guids: set[str], filter_guids: set[str]):
    data: defaultdict[str, int] = defaultdict(int)

    for line in logs:
        if "DAMAGE" not in line:
            continue
        try:
            timestamp, flag, sGUID, _, tGUID, _, _, _, _, damage, _ = line.split(',', 10)
        except ValueError:
            continue
        if sGUID not in source_guids:
            continue
        if tGUID in filter_guids:
            continue
        if flag not in FLAGS:
            continue
        data[timestamp[-9:-2]] += int(damage)

    return data

def to_int(s: str):
    minutes, seconds = s.split(":", 1)
    return int(minutes) * 600 + int(seconds.replace('.', ''))

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

def convert_to_continuous_dps_custom(data: dict[int, int], refresh_window=10):
    DPS = {}
    LAST_KEY = list(data)[-1]
    if not refresh_window:
        refresh_window = 1

    total_dps = 0
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

def convert_to_slice_dps_custom(data: dict[int, int], refresh_window=None):
    DPS = {0: 0}
    LAST_KEY = list(data)[-1]
    if not refresh_window:
        refresh_window = 1

    current_dps = 0
    for sec_from_start in range(LAST_KEY//10+1):
        for tenth_of_sec in range(10):
            current_key = sec_from_start*10+tenth_of_sec
            current_dps += data.get(current_key, 0)
        
        current_sec = sec_from_start + 1
        if current_sec % refresh_window == 0:
            DPS[current_sec] = round(current_dps/refresh_window, 1)
            current_dps = 0

    return DPS

def convert_to_dps(data: dict[int, int], refresh_window=None):
    try:
        refresh_window = int(refresh_window)
    except:
        pass
    
    if not refresh_window:
        return convert_to_continuous_dps_seconds(data)
    return convert_to_slice_dps_custom(data, int(refresh_window))

def convert_keys(data: dict[str, int], pull_start_line: str):
    if not data:
        return
    
    _timestamp = pull_start_line.split(",", 1)[0][-9:-2]
    FIRST_KEY = to_int(_timestamp)
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


class Dps(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def get_dps(self, s, f, player: str):
        logs_slice = self.LOGS[s:f]
        all_guids = self.get_players_and_pets_guids()
        if player:
            source_guids = self.get_units_controlled_by(player)
        else:
            source_guids = all_guids
        data = get_raw_data(logs_slice, source_guids, all_guids)
        convert_keys(data, logs_slice[0])
        return data

    @running_time
    def get_dps_wrap(self, data: dict):
        if not data:
            return {}

        enc_name = data.get("boss")
        attempt = data.get("attempt")
        if not enc_name or not attempt:
            return {}
        
        enc_data = self.get_enc_data()
        enc_name = BOSSES_FROM_HTML[enc_name]
        s, f = enc_data[enc_name][int(attempt)]
        player = data.get("player_name")
        _data = self.get_dps(s, f, player)
        if not _data:
            return {}
        refresh_window = data.get("sec")
        new_data = convert_to_dps(_data, refresh_window)
        convert_keys_to_str(new_data)
        return new_data




def test():
    report = Dps("22-12-30--20-10--Nomadra--Lordaeron")
    report.LOGS
    s, f = report.ENCOUNTER_DATA["The Lich King"][-2]
    dps = report.get_dps(s, f, "Nomadra")
    new_data = convert_to_dps(dps, 1)
    convert_keys_to_str(new_data)
    for x in list(new_data)[:30]:
        print(f"{x} | {new_data[x]:>9,}")

if __name__ == "__main__":
    test()
