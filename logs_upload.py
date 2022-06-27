import json
import logging
import os
import re
import shutil
import zipfile
from datetime import datetime
from multiprocessing import Process
from threading import Thread

import constants
import logs_cut
import logs_main
import logs_unzip
from constants import (DIR_PATH, LOGS_CUT_NAME, T_DELTA_15MIN, UPLOADED,
                       new_folder_path, running_time, zlib_text_write)

RAW_DIR = new_folder_path(DIR_PATH, "LogsRaw")
LOGS_DIR = new_folder_path(DIR_PATH, "LogsDir")

UPLOADS_DIR = new_folder_path(DIR_PATH, "uploads")
PARSED_DIR = new_folder_path(UPLOADS_DIR, "__parsed__")
PARSED_LOGS_DIR = new_folder_path(PARSED_DIR, "logs")
LEGACY_UPLOAD = new_folder_path(UPLOADS_DIR, 'legacy')

UPLOAD_LOGGER_FILE = os.path.join(UPLOADS_DIR, 'upload.log')
UPLOAD_LOGGER = constants.setup_logger('upload_logger', UPLOAD_LOGGER_FILE)

BUGGED_NAMES = {"nil", "Unknown"}

def write_new_logs(logs_id: str, new_logs: str):
    file_name = f"{logs_id}.txt"
    archive_path = os.path.join(RAW_DIR, f"{logs_id}.zip")
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=5) as archive:
        archive.writestr(file_name, new_logs)
    print('write_new_logs', logs_id)

def get_logs_author(logs: list[str]) -> str:
    for line in logs:
        if "SPELL_CAST_FAILED" not in line:
            continue
        name = line.split(',', 3)[2]
        name = name.replace('"', '')
        if name not in BUGGED_NAMES:
            return name
    return 'Unknown'

def get_logs_id(logs_slice, to_dt):
    date = to_dt(logs_slice[0]).strftime("%y-%m-%d--%H-%M")
    logs_author = get_logs_author(logs_slice)
    return f"{date}--{logs_author}"

@running_time
def prepare_logs(file_name):
    logs_raw = constants.bytes_read(file_name)
    logs_raw_decoded = logs_raw.decode()
    return constants.logs_splitlines(logs_raw_decoded)

def find_start(logs, to_dt):
    for line in logs:
        if not line:
            continue
        
        try:
            return to_dt(line)
        except Exception:
            UPLOAD_LOGGER.debug(f'[SLICE LOGS] Skipped scuffed line {line[:200]}')

def slice_logs(logs: list[str], to_dt):
    last_dt = find_start(logs, to_dt)

    max_delta = T_DELTA_15MIN
    current_segment = []
    for line in logs:
        try:
            dt = to_dt(line)
        except Exception:
            UPLOAD_LOGGER.debug(f'[SLICE LOGS] Skipped scuffed line {line[:200]}')
            continue

        if dt - last_dt > max_delta:
            yield current_segment

            current_segment = []

        current_segment.append(line)
        last_dt = dt

    yield current_segment

def to_int(line: str):
    return int(line.split(' ', 1)[1][:8].replace(':', ''))

def find_start2(logs: list[str]):
    for line in logs:
        try:
            return to_int(line), line
        except Exception:
            pass

def slice_logs(logs_raw: list[str], to_dt):
    _last = find_start2(logs_raw)
    if _last is None:
        return []
    
    last_timestamp, last_line = _last
    get_timedelta = constants.get_time_delta_wrap(to_dt)
    
    current_segment = []
    for line in logs_raw:
        try:
            timestamp = to_int(line)
        except Exception:
            continue
        
        _delta = timestamp - last_timestamp
        if (_delta > 100 or _delta < 0) and get_timedelta(last_line, line) > T_DELTA_15MIN:
            yield current_segment
            current_segment = []

        last_timestamp = timestamp
        last_line = line
        current_segment.append(line)

    yield current_segment


class NewUpload(Thread):
    # def __init__(self, logs_raw_name: str, upload_dir: str) -> None:
    def __init__(self, archive_data: dict) -> None:
        super().__init__()
        self.archive_data = archive_data
        self.upload_dir = archive_data["upload_dir"]
        self.logs_raw_name = archive_data["file"]
        self.logs_list = []
        self.to_dt = constants.to_dt_closure(archive_data['year'])

        self.processes: list[Process] = []
        
        self.status_json = ""
        self.status_dict = {}
        self.change_status("Preparing...", True)

    def change_status(self, message: str, slice_done=False):
        self.status_dict["msg"] = message
        if slice_done:
            self.status_dict["links"] = self.logs_list
        self.status_json = json.dumps(self.status_dict)
        # print(self.status_json)

    def parsed_new_logs_status(self, logs_id):
        self.logs_list.append(logs_id)
        self.change_status("Determinating new slice...", True)
    
    def new_process(self, func, args=None):
        _process = Process(target=func, args=args)
        self.processes.append(_process)
        _process.start()

    @running_time
    def main_parser(self, logs_raw, logs_id):
        logs_dir = new_folder_path(LOGS_DIR, logs_id)
        
        self.change_status("Formatting new slice...")
        logs_raw_formatted = logs_cut.logs_format(logs_raw)

        self.change_status("Trimming new slice...")
        logs_trimmed = logs_cut.trim_logs(logs_raw_formatted)

        logs_trimmed_joined = logs_cut.join_logs(logs_trimmed)
        cut_path = os.path.join(logs_dir, LOGS_CUT_NAME)
        self.new_process(zlib_text_write, args=(logs_trimmed_joined, cut_path))

        new_report = logs_main.THE_LOGS(logs_id)
        new_report.LOGS = logs_trimmed
        print('[LOGS UPLOAD] NEW LOGS SET')

        self.change_status("Parsing encounter data...")
        new_report.get_enc_data(rewrite=True)
        
        self.change_status("Parsing GUIDs...")
        new_report.get_guids(rewrite=True)
        
        self.change_status("Parsing timings...")
        new_report.get_timestamp(rewrite=True)
        
        self.change_status("Parsing spells...")
        new_report.get_spells(rewrite=True)
        
        self.parsed_new_logs_status(logs_id)
    
    # def new_thread(self, func, args=None, process=False):
    #     if process:
    #         t = Process(target=func, args=args)
    #     else:
    #         t = Thread(target=func, args=args)
    #     t.start()
    #     self.processes.append(t)

    @running_time
    def eval_slice(self, logs_slice: list[str], logs_id: str):
        if logs_slice[-1] != '':
            logs_slice.append('')
        
        if len(logs_slice) < 25000:
            UPLOAD_LOGGER.info(f"[LOGS UPLOAD] doshitwithslice LOGS SLICE IS TOO SMALL: {len(logs_slice):>9,}")
            return
        
        UPLOAD_LOGGER.info(f"[LOGS UPLOAD] doshitwithslice NEW SLICE LEN: {len(logs_slice):>9,}")
        new_logs = '\n'.join(logs_slice)

        self.new_process(write_new_logs, args=(logs_id, new_logs))
        return new_logs
    
    def wait_for_processes(self):
        for _process in self.processes:
            _process.join()

    def run(self):
        if "logs_list" in self.archive_data:
            print('file has been uploaded already')
            self.change_status("Done! Select 1 of the reports below.", True)
            return

        try:
            logs_raw = prepare_logs(self.logs_raw_name)
            for logs_slice in slice_logs(logs_raw, self.to_dt):
                if not logs_slice:
                    continue
                logs_id = get_logs_id(logs_slice, self.to_dt)
                new_slice = self.eval_slice(logs_slice, logs_id)
                if new_slice is not None:
                    self.main_parser(new_slice, logs_id)

            self.status_dict["done"] = 1
            self.change_status("Done! Select 1 of the reports below.", True)

            self.archive_data["logs_list"] = self.logs_list
            
            os.remove(self.logs_raw_name)
        
        except Exception:
            logging.exception(f"NewUpload run {self.upload_dir}")
        
        finally:
            self.wait_for_processes()


class File:
    def __init__(self, current_path) -> None:
        self.current_path = current_path
        self.filename: str = os.path.basename(current_path)
        self.name, self.ext = self.filename.split('.')
    
    def save(self, new_path):
        shutil.copyfile(self.current_path, new_path)


def new_upload_folder(ip='localhost'):
    new_upload_dir_ip = new_folder_path(UPLOADS_DIR, ip)
    timestamp = constants.get_now().strftime("%y-%m-%d--%H-%M-%S")
    new_upload_dir = new_folder_path(new_upload_dir_ip, timestamp)
    return new_upload_dir

def main(file: File, ip='localhost'):
    raw_filename = file.filename
    *words, ext = re.findall('([A-Za-z0-9]+)', raw_filename)
    file_name = f"{'_'.join(words)}.{ext}"

    new_upload_dir = new_upload_folder(ip)
    full_file_path = os.path.join(new_upload_dir, file_name)
    file.save(full_file_path)

    data = logs_unzip.new_archive(full_file_path, new_upload_dir)
    
    return NewUpload(data)

# def main_local_text(logs_path, move=True):
def main_local_text(logs_path, move=False):
    ctime = int(os.path.getctime(logs_path))
    size = os.path.getsize(logs_path)
    archive_id = f"{ctime}_{size}"
    if archive_id in UPLOADED and 'logs_list' in UPLOADED[archive_id]:
        return
    
    new_upload_dir = new_upload_folder()

    if move:
        logs_raw_name = os.path.basename(logs_path)
        logs_new_path = os.path.join(new_upload_dir, logs_raw_name)
        os.rename(logs_path, logs_new_path)
        logs_path = logs_new_path

    mod_time = constants.logs_edit_time(logs_path)
    dt = datetime.fromtimestamp(ctime)
    data = UPLOADED[archive_id] = {"mod_time": mod_time, "file": logs_path, "upload_dir": new_upload_dir, "year": dt.year}
    return NewUpload(data)

def main_legacy(full_path, redo=False):
    file = File(full_path)
    new_upload_dir = os.path.join(LEGACY_UPLOAD, file.name)
    if not redo and os.path.exists(new_upload_dir):
        print(f"[LOGS UPLOAD] main_legacy {file.name} exists")
        return
    
    print(f"[LOGS UPLOAD] main_legacy {full_path}")
    
    constants.create_folder(new_upload_dir)
    full_path = os.path.join(new_upload_dir, file.filename)
    file.save(full_path)

    logs_raw_name = unzip_shit(full_path, new_upload_dir)
    logs_raw_name_path = os.path.join(new_upload_dir, logs_raw_name)
    
    return NewUpload(logs_raw_name_path, new_upload_dir)
    
@running_time
def __test2(logs):
    to_dt = constants.to_dt
    q = [len(x) for x in slice_logs2(logs, to_dt)]
    # q = [x for x in slice_logs2(logs, to_dt)]
    ans = [346097, 57172, 362806, 50978, 1930853, 181319, 211, 201048, 1788567]
    print(q)
    assert q == ans
    # for x in slice_logs2(logs, to_dt):
        # print(x)

# if __name__ == "__main__":
#     name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog1.txt"
#     logs = prepare_logs(name)
#     sdfiaksiofjksdifjaof(logs)
#     sdfiaksiofjksdifjaof(logs)
#     sdfiaksiofjksdifjaof(logs)
#     sdfiaksiofjksdifjaof(logs)
#     sdfiaksiofjksdifjaof(logs)

if __name__ == "__main__":
    import sys
    print(sys.argv)
    try:
        name = sys.argv[1]
    except IndexError as e:
        # name = r"F:\Python\wow_logs\LogsRaw\legacy\upload_12062.zip"
        name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog.txt"
        print(e)
        # input()
    if name.endswith('.txt'):
        _main_thread = main_local_text(name)
    else:
        new_file = File(name)
        _main_thread = main(new_file)
    if _main_thread is not None:
        _main_thread.start()
        _main_thread.join()
        input("\nDONE!\nPRESS ANY BUTTON OR CLOSE...")
