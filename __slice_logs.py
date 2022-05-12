from io import TextIOWrapper
import os
import re
from time import perf_counter
from datetime import datetime, timedelta
import threading
import constants


real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
SLICED_PATH = os.path.join(DIR_PATH, "SlicedLogs")
constants.create_folder(SLICED_PATH)

MINSIZE = 5 * 1024 * 1024
ERRORS = []
TIME_DELTA = timedelta(minutes=20)

# CURRENT_YEAR = datetime.now().year
# Z = re.compile('(\d{1,2})/(\d{1,2}) (\d\d):(\d\d):(\d\d).(\d\d\d)')
# def to_dt(s: str):
#     q = list(map(int, Z.findall(s)[0]))
#     q[-1] *= 1000
#     return datetime(CURRENT_YEAR, *q)

# def running_time(f: FunctionType):
#     def inner(*args, **kwargs):
#         st = perf_counter()
#         q = f(*args, **kwargs)
#         fin = int((perf_counter() - st) * 1000)
#         print(f'Done in {fin:>6,} ms with {f.__module__}.{f.__name__}')
#         return q
#     return inner

@constants.running_time
def join_logs(logs):
    return ''.join(logs)

@constants.running_time
def write_new_logs(new_logs: str, new_logs_name: str):
    old_logs = constants.file_read(new_logs_name)
    print(f"[SLICE LOGS]: LEN OLD: {len(old_logs):>13,} bytes")
    print(f"[SLICE LOGS]: LEN NEW: {len(new_logs):>13,} bytes")

    if len(old_logs) == len(new_logs):
        print('[SLICE LOGS]: LOGS EXIST')
    else:
        with open(new_logs_name, 'w') as f:
            f.write(new_logs)
        return True

to_dt = constants.to_dt
def gothrufile(file: TextIOWrapper):
    logs_slice = []
    index_start = 0
    last_dt = None
    for index_current, line in enumerate(file):
        if not last_dt:
            last_dt = to_dt(line)
        
        try:
            dt = to_dt(line)
        except (IndexError, ValueError):
            print('[SLICE LOGS]: Skipped scuffed line:')
            print(line)
            continue

        if dt - last_dt > TIME_DELTA:
            yield logs_slice, index_start
            logs_slice.clear()
            index_start = index_current
        
        if len(line) < 1000:
            logs_slice.append(line)
        
        last_dt = dt

    yield logs_slice, index_start

def new_slice_name(sliced_dir, s):
    return os.path.join(sliced_dir, f"SLICE_{s}.txt")

@constants.running_time
def slice_main2(name, sliced_dir):
    threads = []
    with open(name, 'r') as file:
        st = perf_counter()
        for logs_slice, index_start in gothrufile(file):
            print(f'\n[SLICE LOGS]: NEW PART REACHED IN: {(perf_counter() - st):.2f}s')
            logs_slice_copy = list(logs_slice)
            new_name = os.path.join(sliced_dir, f"SLICE_{index_start}.txt")
            new_logs = ''.join(logs_slice_copy)
            t = threading.Thread(target=write_new_logs, args=(new_logs, new_name))
            threads.append(t)
            t.start()
            st = perf_counter()
    for t in threads:
        t.join()

@constants.running_time
def slice_main(name, sliced_dir):
    threads = []
    with open(name, 'r') as file:
        st = perf_counter()
        for logs_slice, index_start in gothrufile(file):
            logs_slice_copy = list(logs_slice)
            print(f'\n[SLICE LOGS]: NEW PART REACHED IN: {(perf_counter() - st):.2f}s')
            new_name = os.path.join(sliced_dir, f"SLICE_{index_start}.txt")
            t = threading.Thread(target=write_new_logs, args=(logs_slice_copy, new_name))
            threads.append(t)
            t.start()
            st = perf_counter()
    for t in threads:
        t.join()
    
def upload_main(name):
    if 'txt' not in name:
        return
    name = os.path.join(SLICED_PATH, name)
    if os.path.getsize(name) < MINSIZE: return
    t = upload.NewUpload(logs_raw_name=name, rewrite=True)
    t.start()
    t.join()
    
if __name__ == "__main__":
    try:
        # name = sys.argv[1]
        name = "F:/World of Warcraft 3.3.5a HD/Logs/WoWCombatLog.txt"
        slice_main(name, SLICED_PATH)
        input(f"\nDONE SLICING {name}\nPRESS ANY BUTTON OR CLOSE...")
    except IndexError:
        filenames = next(os.walk(SLICED_PATH))[2]
        for name in filenames:
            upload_main(name)
        input("\nDONE UPLOADING\nPRESS ANY BUTTON OR CLOSE...")
            