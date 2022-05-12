import os
import re
import time
from datetime import datetime, timedelta
from multiprocessing import Pool
import sys
# from typing import List
# import constants
# import cut_logs
# import _main
# import subprocess
# import threading

import logs_upload

tm = time.time

ERRORS = []
SLICED_PATH = "./SlicedLogs"
TIME_DELTA = timedelta(minutes=30)
    
def running_time(f):
    def inner(*args, **kwargs):
        st = tm()
        q = f(*args, **kwargs)
        fin = int((tm() - st) * 1000)
        print(f'Done in {fin:>6,} ms with {f.__module__}.{f.__name__}')
        return q
    return inner

CURRENT_YEAR = datetime.today().year
Z = re.compile('(\d{1,2})/(\d{1,2}) (\d\d):(\d\d):(\d\d).(\d\d\d)')
def to_dt(s: str):
    q = list(map(int, Z.findall(s)[0]))
    q[-1] *= 1000
    return datetime(CURRENT_YEAR, *q)

@running_time
def write_new_logs(logs, name):
    name = f"{SLICED_PATH}/{name}.txt"
    with open(name, 'a+') as f:
        for line in logs:
            f.write(line)
    print(name)

@running_time
def slice_main(name):
    if not os.path.exists(SLICED_PATH):
        os.makedirs(SLICED_PATH, exist_ok=True)
        print(f'Created {SLICED_PATH}/')
    logs = []
    with open(name, 'r') as f:
        n = 0
        line = f.readline()
        last_dt = to_dt(line)
        while line:
            try:
                dt = to_dt(line)
                if dt - last_dt > TIME_DELTA:
                    write_new_logs(logs, n)
                    logs.clear()
                if len(line) < 1000:
                    logs.append(line)
                last_dt = dt
            except (IndexError, ValueError):
                print('Skipped scuffed line:')
                print(line)
            n += 1
            line = f.readline()
    write_new_logs(logs, n)

# BUGGED_NAMES = {"nil", "Unknown"}
    # @running_time
    # def get_logs_name(logs: List[str]) -> str:
    #     date = constants.to_dt(logs[0]).strftime("%y-%m-%d--%H-%M")
    #     for line in logs:
    #         if "SPELL_CAST_FAILED" in line:
    #             name = line.split(',')[3]
    #             if name not in BUGGED_NAMES:
    #                 return f"{date}--{name}"
            
    # def create_dir(name):
    #     if not os.path.exists(name):
    #         os.makedirs(name, exist_ok=True)
    #         print('LOG: Created folder:', name)

    # def archive(new_name, logs_raw_name):
    #     archive_path = f"./LogsRaw/{new_name}.7z"
    #     # if os.path.isfile(archive_path) and os.path.getsize(archive_path) > 1024*1024:
    #     #     print("FILE EXISTS:", archive_path)
    #     #     return
    #     cmd = ['7za.exe', 'a', '-m0=PPMd', '-mo=11', '-mx=9', archive_path, logs_raw_name, '-aoa']
    #     subprocess.call(cmd, shell=False)

    # def srfujisdfhuisdfhisdfyhiusdfhui(name):
    #     logs_file = f"{SLICED_PATH}/{name}"
    #     # logs_file_new = f"{SLICED_PATH}/Logs.txt"
    #     # os.rename(logs_file, logs_file_new)

    #     logs_raw = constants.file_read(logs_file)

    #     logs_raw_formatted = cut_logs.logs_format(logs_raw)

    #     new_name = get_logs_name(logs_raw_formatted)
    #     if not new_name:
    #         return

    #     archive_raw = threading.Thread(target=archive, args=(new_name,))
    #     archive_raw.start()

    #     logs_dir = f'./LogsDir/{new_name}/'
    #     n = f"{logs_dir}Logs_cut.txt"
    #     if not rewrite and os.path.isfile(n) and os.path.getsize(n) > 1024*1024:
    #         new_logs = _main.THE_LOGS(new_name)
    #         archive_raw.join()
    #         return

    #     create_dir(logs_dir)

    #     logs = cut_logs.trim_logs(logs_raw_formatted)

    #     cut_save = threading.Thread(target=save_logs, args=(logs, logs_dir))
    #     cut_save.start()

    #     new_logs = _main.THE_LOGS(new_name, logs)
    #     print('NEW LOGS SET')
        
    #     new_logs.get_enc_data()
        
    #     new_logs.get_guids()
        
    #     new_logs.get_classes()

    #     new_logs.get_timestamp()
        
    #     new_logs.get_spells()

    #     cut_save.join()
    #     archive_raw.join()

def upload_main(name):
    if 'txt' not in name:
        return
    name = f"{SLICED_PATH}/{name}"
    t = logs_upload.NewUpload(logs_raw_name=name, rewrite=True)
    t.start()
    t.join()
    
if __name__ == "__main__":
    try:
        name = sys.argv[1]
    except IndexError:
        name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog7.txt"
        name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog10.txt"
        name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog20.txt"
        name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog4.txt"
        name = ""

    if name:
        slice_main(name)
    else:    
        _, _, filenames = next(os.walk(SLICED_PATH))
        for name in filenames:
            print(name)
            try:
                upload_main(name)
            except:
                ERRORS.append(name)
            
        print(ERRORS)
    