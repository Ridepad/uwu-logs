import json
import os
import re
import shutil
import subprocess
import threading
import traceback

import py7zr

import _main
import constants
import cut_logs
from constants import DIR_PATH, T_DELTA_SEP, new_folder_path, running_time


RAW_DIR = new_folder_path(DIR_PATH, "LogsRaw")
LOGS_DIR = new_folder_path(DIR_PATH, "LogsDir")

UPLOADS_DIR = new_folder_path(DIR_PATH, "uploads")
PARSED_DIR = new_folder_path(UPLOADS_DIR, "__parsed__")
PARSED_LOGS_DIR = new_folder_path(PARSED_DIR, "logs")
LEGACY_UPLOAD = new_folder_path(UPLOADS_DIR, 'legacy')
# UPLOAD_ERRORS = new_folder_path(UPLOADS_DIR, "errors")

BUGGED_NAMES = {"nil", "Unknown"}


def get_archived_len(archive_path):
    try:
        with py7zr.SevenZipFile(archive_path) as a:
            return a.archiveinfo().uncompressed + 1
    except py7zr.exceptions.Bad7zFile:
        os.remove(archive_path)
        return 1
    except FileNotFoundError:
        return 1

@running_time
def write_new_logs(logs_id: str, new_logs: str):
    archive_path = os.path.join(RAW_DIR, f"{logs_id}.7z")
    logs_raw_zlib_path = os.path.join(PARSED_DIR, f"{logs_id}.zlib")

    print("[LOGS UPLOAD] NEW LOGS RAW ACHIVE:", archive_path)

    logs_zlib_old = constants.bytes_read(logs_raw_zlib_path)
    logs_zlib_old_len = len(logs_zlib_old)
    logs_zlib_new = constants.zlib_text_make(new_logs)
    logs_zlib_new_len = len(logs_zlib_new)

    archived_len = get_archived_len(archive_path)
    diff_cache = archived_len / len(new_logs)

    if logs_zlib_new_len == logs_zlib_old_len:
        print('[LOGS UPLOAD] write_new_logs CACHE EXISTS')
        if diff_cache > 1:
            return 0

    print(f"[LOGS UPLOAD] LEN DIFF1: {diff_cache:>.5f}")
    
    print(f"[LOGS UPLOAD] LEN NEWZLIB: {logs_zlib_new_len:>13,} bytes")
    print(f"[LOGS UPLOAD] LEN OLDZLIB: {logs_zlib_old_len:>13,} bytes")
    
    constants.bytes_write(logs_raw_zlib_path, logs_zlib_new)
    
    if diff_cache > 1:
        print('[LOGS UPLOAD] write_new_logs LOGS CACHED')
        return 0
    

    logs_raw_path = os.path.join(PARSED_DIR, f"{logs_id}.txt")
    constants.file_write(logs_raw_path, new_logs)
    
    arhive_logs_path = os.path.join(PARSED_LOGS_DIR, f"{logs_id}.log")
    cmd = ['7za.exe', 'a', archive_path, logs_raw_path, '-m0=PPMd', '-mo=11', '-mx=9']
    with open(arhive_logs_path, 'a+') as f:
        code = subprocess.call(cmd, stdout=f)
        if code == 0 and os.path.isfile(logs_raw_path):
            os.remove(logs_raw_path)
            print('[LOGS UPLOAD] write_new_logs CACHE REMOVED')
        return code
    

@running_time
def _splitlines(s: str):
    return s.splitlines()

def get_logs_author(logs: list[str]) -> str:
    for line in logs:
        if "SPELL_CAST_FAILED" not in line:
            continue
        name = line.split(',', 3)[2]
        name = name.replace('"', '')
        if name not in BUGGED_NAMES:
            return name

def get_logs_id(logs_slice, to_dt):
    date = to_dt(logs_slice[0]).strftime("%y-%m-%d--%H-%M")
    logs_author = get_logs_author(logs_slice)
    return f"{date}--{logs_author}"

def unzip_shit(full_path, upload_dir):
    if not full_path:
        return ""
    
    cmd = ['7za.exe', 'e', full_path, '-aoa', f"-o{upload_dir}", "*.txt"]
    unzip_log = os.path.join(upload_dir, "unzip.log")
    with open(unzip_log, 'a+') as f:
        subprocess.call(cmd, stdout=f)
    
    for file in os.listdir(upload_dir):
        if ".txt" in file:
            return file

def remove_scuff(logs, scuff, start, finish=None):
    _slice = logs[start:finish]
    for i in reversed(sorted(scuff)):
        del _slice[start+i]
    return _slice

@running_time
def prepare_logs(file_name):
    logs_raw = constants.bytes_read(file_name)
    logs_raw_decoded = logs_raw.decode()
    return _splitlines(logs_raw_decoded)

def find_start(logs, to_dt):
    for line in logs:
        if not line:
            continue
        
        try:
            return to_dt(line)
        except Exception:
            print(f'[SLICE LOGS] Skipped scuffed line:')
            print(line[:200])
            continue

def slice_logs(logs: list[str], to_dt):
    last_dt = find_start(logs, to_dt)
    
    current_segment = []
    for index_current, line in enumerate(logs):
        try:
            dt = to_dt(line)
        except Exception:
            print(f'[SLICE LOGS] Skipped scuffed line {index_current:>9,}:')
            print(line[:200])
            continue

        if dt - last_dt > T_DELTA_SEP:
            yield current_segment

            current_segment = []
        
        current_segment.append(line)
        last_dt = dt

    yield current_segment
    

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
        # print(self.status_json)

    def parsed_new_logs(self, logs_id):
        self.logs_list.append(logs_id)
        self.change_status("Determinating new slice...", True)

    def main_parser(self, logs_raw, logs_id):
        logs_dir = new_folder_path(LOGS_DIR, logs_id)

        cut_path = os.path.join(logs_dir, constants.LOGS_CUT_NAME)
        
        self.change_status("Formatting new slice...")
        logs_raw_formatted = cut_logs.logs_format(logs_raw)

        self.change_status("Trimming new slice...")
        logs_trimmed = cut_logs.trim_logs(logs_raw_formatted)
        logs_trimmed_joined = cut_logs.join_logs(logs_trimmed)

        exists = constants.zlib_text_write(logs_trimmed_joined, cut_path)
        if exists:
            print('[LOGS UPLOAD] main_parser LOGS EXIST!')
            self.parsed_new_logs(logs_id)
            return

        new_report = _main.THE_LOGS(logs_id)
        new_report.LOGS = logs_trimmed
        print('[LOGS UPLOAD] NEW LOGS SET')
        
        self.change_status("Parsing encounter data...")
        new_report.get_enc_data(rewrite=True)
        
        self.change_status("Parsing GUIDs...")
        new_report.get_guids(rewrite=True)
        
        self.change_status("Parsing player classes...")
        new_report.get_classes(rewrite=True)
        
        self.change_status("Parsing timings...")
        new_report.get_timestamp(rewrite=True)
        
        self.change_status("Parsing spells...")
        new_report.get_spells(rewrite=True)
        
        self.parsed_new_logs(logs_id)
    
    @running_time
    def doshitwithslice(self, logs_slice: list[str], logs_id: str):
        if logs_slice[-1] != '':
            logs_slice.append('')
        
        if len(logs_slice) < 25000:
            print(f"[LOGS UPLOAD] doshitwithslice LOGS SLICE IS TOO SMALL: {len(new_logs):>13,} bytes")
            return
        
        print(f"[LOGS UPLOAD] doshitwithslice NEW SLICE LEN: {len(logs_slice):>9,}")
        new_logs = '\n'.join(logs_slice)
        
        del logs_slice

        t = threading.Thread(target=write_new_logs, args=(logs_id, new_logs))
        self.threads.append(t)
        t.start()
        
        self.main_parser(new_logs, logs_id)
    
    def run(self):
        to_dt = constants.to_dt_closure()
        try:
            logs = prepare_logs(self.logs_raw_name)
            for logs_slice in slice_logs(logs, to_dt):
                logs_id = get_logs_id(logs_slice, to_dt)
                self.doshitwithslice(logs_slice, logs_id)

            self.status_dict["done"] = 1
            self.status_json = json.dumps(self.status_dict)
            
            self.change_status("Done! Select 1 of the reports below.", True)
            
            os.remove(self.logs_raw_name)
        except:
            traceback.print_exc()
            logfile = os.path.join(self.upload_dir, "error.log")
            with open(logfile, 'a+') as f:
                traceback.print_exc(file=f)

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
    logs_raw_name = os.path.basename(logs_raw_name_path)
    logs_new_name_path = os.path.join(new_upload_dir, logs_raw_name)
    os.rename(logs_raw_name_path, logs_new_name_path)

    return NewUpload(logs_new_name_path, new_upload_dir)

def upload_legacy(full_path, redo=False):
    file = File(full_path)
    new_upload_dir = os.path.join(LEGACY_UPLOAD, file.name)
    if not redo and os.path.exists(new_upload_dir):
        print(f"[LOGS UPLOAD] upload_legacy {file.name} exists")
        return
    
    print(f"[LOGS UPLOAD] upload_legacy {full_path}")
    
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
        name = sys.argv[1]
    except IndexError as e:
        # name = r"F:\Python\wow_logs\LogsRaw\legacy\upload_12062.zip"
        # name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog.txt"
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
