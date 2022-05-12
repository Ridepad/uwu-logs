import json
import os
import re
import shutil
import subprocess
import threading

import _main
import constants
import cut_logs
from constants import T_DELTA_SEP, running_time, to_dt

SIZE_CHECK = 4*1024*1024
BUGGED_NAMES = {"nil", "Unknown"}

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
UPLOADS_DIR = os.path.join(DIR_PATH, "uploads")
RAW_DIR = os.path.join(DIR_PATH, "LogsRaw")
LOGS_DIR = os.path.join(DIR_PATH, "LogsDir")
PARSED_DIR = os.path.join(UPLOADS_DIR, "__parsed__")
constants.create_folder(PARSED_DIR)


def archive_file(file_path: str, archive_path: str):
    print("[UPLOAD LOGS]: ACHIVE RAW:", archive_path)
    cmd = ['7za.exe', 'a', archive_path, file_path, '-m0=PPMd', '-mo=11', '-mx=9']
    subprocess.call(cmd, shell=False)

@running_time
def write_new_logs(logs_id: str, new_logs: str):
    logs_raw_path = os.path.join(PARSED_DIR, f"{logs_id}.txt")
    old_logs = constants.file_read(logs_raw_path)
    print(f"[SLICE LOGS]: LEN OLD: {len(old_logs):>13,} bytes")
    print(f"[SLICE LOGS]: LEN NEW: {len(new_logs):>13,} bytes")

    new_version = len(old_logs) != len(new_logs)
    if new_version:
        constants.file_write(logs_raw_path, new_logs)
    else:
        print('[SLICE LOGS]: LOGS EXIST')
    
    archive_path = os.path.join(RAW_DIR, f"{logs_id}.7z")
    if new_version or not os.path.exists(archive_path) or os.path.getsize(archive_path) < 1024*1024:
        archive_file(logs_raw_path, archive_path)
    

@running_time
def _splitlines(s: str):
    return s.splitlines()

def get_logs_name(logs: list[str]) -> str:
    date = to_dt(logs[0]).strftime("%y-%m-%d--%H-%M")
    for line in logs:
        if "SPELL_CAST_FAILED" not in line:
            continue
        name = line.split(',', 3)[2]
        name = name.replace('"', '')
        if name not in BUGGED_NAMES:
            return f"{date}--{name}"

@running_time
def save_logs(logs, file_name):
    logs_raw = cut_logs.join_logs(logs)
    constants.zlib_text_write(logs_raw, file_name)

def unzip_shit(full_path, upload_dir):
    if not full_path:
        return ""
    cmd = ['7za.exe', 'e', full_path, '-aoa', f"-o{upload_dir}", "*.txt"]
    subprocess.call(cmd, stdout=None)
    for file in os.listdir(upload_dir):
        if ".txt" in file:
            return file

def remove_scuff(logs, scuff, start, finish=None):
    _slice = logs[start:finish]
    for i in reversed(sorted(scuff)):
        del _slice[start+i]
    return _slice

def gothrufile(logs_raw):
    logs_raw_lines = _splitlines(logs_raw)
    index_start = 0
    last_dt = to_dt(logs_raw_lines[0])
    scuff = []
    for index_current, line in enumerate(logs_raw_lines):
        try:
            dt = to_dt(line)
        except (IndexError, ValueError):
            scuff.append(index_current)
            print('[SLICE LOGS] Skipped scuffed line:')
            print(line)
            continue

        if dt - last_dt > T_DELTA_SEP:
            # _slice = logs_raw_lines[index_start:index_current+1]
            # for i in reversed(sorted(scuff)):
            #     del _slice[index_start+i]
            # yield _slice
            yield remove_scuff(logs_raw_lines, scuff, index_start, index_current)

            scuff.clear()
            index_start = index_current
        
        last_dt = dt

    # _slice = logs_raw_lines[index_start:]
    # for i in reversed(sorted(scuff)):
    #     del _slice[index_start+i]
    # yield _slice
    yield remove_scuff(logs_raw_lines, scuff, index_start)
    

class NewUpload(threading.Thread):
    def __init__(self, logs_raw_name: str, upload_dir: str) -> None:
        super().__init__()
        self.logs_raw_name = logs_raw_name
        self.upload_dir = upload_dir

        self.threads: list[threading.Thread] = []
        
        self.status_json = str()
        self.status_dict = {}
        self.logs_list = []
        self.change_status("Preparing...", True)

    def change_status(self, message: str, new_logs=False):
        self.status_dict["msg"] = message
        if new_logs:
            self.status_dict["links"] = self.logs_list
        self.status_json = json.dumps(self.status_dict)
        print(self.status_json)

    def parsed_new_logs(self, logs_id):
        self.logs_list.append(logs_id)
        self.change_status("Determinating new slice...", True)

    def main_parser(self, logs_raw, logs_id):
        logs_dir = os.path.join(LOGS_DIR, logs_id)
        constants.create_folder(logs_dir)

        cut_path = os.path.join(logs_dir, constants.LOGS_CUT_NAME)
        
        self.change_status("Formatting new slice...")
        logs_raw_formatted = cut_logs.logs_format(logs_raw)

        self.change_status("Trimming new slice...")
        logs_trimmed = cut_logs.trim_logs(logs_raw_formatted)
        logs_trimmed_joined = cut_logs.join_logs(logs_trimmed)

        exists = constants.zlib_text_write(logs_trimmed_joined, cut_path, True)
        if exists:
            print('[UPLOAD LOGS] LOGS EXIST!')
            self.parsed_new_logs(logs_id)
            return

        new_logs = _main.THE_LOGS(logs_id)
        new_logs.LOGS = logs_trimmed
        print('[UPLOAD LOGS] NEW LOGS SET')
        
        self.change_status("Parsing encounter data...")
        new_logs.get_enc_data(rewrite=True)
        
        self.change_status("Parsing GUIDs...")
        new_logs.get_guids(rewrite=True)
        
        self.change_status("Parsing player classes...")
        new_logs.get_classes(rewrite=True)
        
        self.change_status("Parsing timings...")
        new_logs.get_timestamp(rewrite=True)
        
        self.change_status("Parsing spells...")
        new_logs.get_spells(rewrite=True)
        
        self.parsed_new_logs(logs_id)
    
    def run(self):
        logs_raw = constants.file_read(self.logs_raw_name)
        for logs_slice in gothrufile(logs_raw):
            logs_slice.append('')
            new_logs = '\n'.join(logs_slice)
            if len(new_logs) < SIZE_CHECK:
                continue

            logs_id = get_logs_name(logs_slice)
            
            t = threading.Thread(target=write_new_logs, args=(logs_id, new_logs))
            self.threads.append(t)
            t.start()
            
            self.main_parser(new_logs, logs_id)

        self.status_dict["done"] = 1
        self.status_json = json.dumps(self.status_dict)
        
        self.change_status("Done! Select 1 of the reports below.", True)

        for t in self.threads:
            t.join()


def new_upload_folder(ip='localhost'):
    timestamp = constants.get_now().strftime("%y-%m-%d--%H-%M-%S")
    new_upload_dir = os.path.join(UPLOADS_DIR, ip)
    new_upload_dir = os.path.join(new_upload_dir, timestamp)
    constants.create_folder(new_upload_dir)
    return new_upload_dir


class File:
    def __init__(self, current_path) -> None:
        self.current_path = current_path
        self.filename: str = os.path.basename(current_path)
        self.name, self.ext = self.filename.split('.')
    
    def save(self, new_path):
        shutil.copyfile(self.current_path, new_path)

def main(file: File, ip='localhost'):
    raw_filename = file.filename
    *words, ext = re.findall('([A-Za-z0-9]+)', raw_filename)
    file_name = f"{'_'.join(words)}.{ext}"

    new_upload_dir = new_upload_folder(ip)
    full_path = os.path.join(new_upload_dir, file_name)
    file.save(full_path)

    logs_raw_name = unzip_shit(full_path, new_upload_dir)
    logs_raw_name_path = os.path.join(new_upload_dir, logs_raw_name)
    
    return NewUpload(logs_raw_name_path, new_upload_dir)

def main2(logs_raw_name_path, move=True):
    new_upload_dir = new_upload_folder()

    if not move:
        return NewUpload(logs_raw_name_path, new_upload_dir)
    os.path.e
    logs_raw_name = os.path.basename(logs_raw_name_path)
    logs_new_name_path = os.path.join(new_upload_dir, logs_raw_name)
    os.rename(logs_raw_name_path, logs_new_name_path)

    return NewUpload(logs_new_name_path, new_upload_dir)

LEGACY_UPLOAD = os.path.join(UPLOADS_DIR, 'legacy')
# constants.create_folder(LEGACY_UPLOAD)

def upload_legacy(full_path):
    print(f"[LOGS UPLOAD] upload_legacy {full_path}")
    file = File(full_path)
    new_upload_dir = os.path.join(LEGACY_UPLOAD, file.name)
    if os.path.exists(new_upload_dir):
        print(f"[LOGS UPLOAD] {file.name} exists")
        return
    
    constants.create_folder(new_upload_dir)
    full_path = os.path.join(new_upload_dir, file.filename)
    file.save(full_path)

    logs_raw_name = unzip_shit(full_path, new_upload_dir)
    logs_raw_name_path = os.path.join(new_upload_dir, logs_raw_name)
    
    return NewUpload(logs_raw_name_path, new_upload_dir)
    


if __name__ == "__main__":
    import sys
    print(sys.argv)
    try:
        # name = sys.argv[1]
        # name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog.txt"
        name = r"F:\Python\wow_logs\LogsRaw\legacy\upload_12062.zip"
    except IndexError as e:
        print(e)
        input()
    if name.endswith('.txt'):
        t = main2(name)
    else:
        new_file = File(name)
        t = main(new_file)
    t.start()
    t.join()
    input("\nDONE!\nPRESS ANY BUTTON OR CLOSE...")
