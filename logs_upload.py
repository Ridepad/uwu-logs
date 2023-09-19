import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from threading import Thread
from time import perf_counter
from pathlib import Path

import constants
import file_functions
import logs_archive
import logs_fix
from constants import (
    DEFAULT_SERVER_NAME,
    LOGGER_UPLOADS,
    LOGS_CUT_NAME,
    LOGS_DIR,
    LOGS_RAW_DIR,
    PATH_DIR,
    SERVERS,
    T_DELTA,
    UPLOADED_DIR,
    UPLOADS_DIR,
    get_report_name_info,
)

ARCHIVE_ID_ERROR = "Bad archive.  Don't change extension manually, create archives from 0."
ARCHIVE_ERROR = "Error extracting logs file.  Make sure logs file inside the archive without any folders."
UPLOAD_GONE = "Uploaded file disappeared. Try to upload again."
LOGS_ERROR = "Error parsing logs."
TOP_ERROR = "Done!  Select 1 of the reports below.  Top update encountered an error."
ALREADY_DONE = "File has been uploaded already!  Select 1 of the reports below."
ALREADY_DONE_NONE_FOUND = "File has been uploaded already!  No boss segments were found!  Make sure to use /combatlog"
FULL_DONE = "Done!  Select 1 of the reports below."
FULL_DONE_PARTIAL = "Done!  Some of the raids were already uploaded.  Make sure to delete logs file to keep it fresh.  Select 1 of the reports below."
FULL_DONE_NONE_FOUND = "Done!  No boss segments were found!  Make sure to use /combatlog"
START_SLICING = "Determinating log slices..."
SAVING_SLICES = "Saving log slices..."
SEMI_DONE = "Finishing caching..."
BUGGED_NAMES = {"nil", "Unknown"}
LOGS_RAW_DIR_BKP = file_functions.get_backup_folder(LOGS_RAW_DIR)
file_functions.create_new_folders(PATH_DIR, LOGS_DIR, UPLOADS_DIR, UPLOADED_DIR)

UPLOADS_TODO = file_functions.new_folder_path(UPLOADS_DIR, "0todo")
UPLOADS_TEXT = file_functions.new_folder_path(UPLOADS_DIR, "0archive_pending")
UPLOADED_FILE_INFO = file_functions.new_folder_path(UPLOADS_DIR, "0file_info")

BIG_GAP = T_DELTA["14H"]
SMALL_GAP = T_DELTA["3MIN"]


def format_filename(file_name):
    if not file_name:
        return "archive.7z"

    *words, ext = re.findall('([A-Za-z0-9]+)', file_name)
    return f"{'_'.join(words)}.{ext}"

def get_now_timestamp():
    return datetime.now().strftime("%y-%m-%d--%H-%M-%S")

def new_upload_folder(ip='localhost', timestamp: str=None):
    new_upload_dir_ip = file_functions.new_folder_path(UPLOADS_DIR, ip)
    if not timestamp:
        timestamp = get_now_timestamp()
    new_upload_dir = file_functions.new_folder_path(new_upload_dir_ip, timestamp)
    return new_upload_dir

def save_upload_cache(_data):
    file_id = _data["file_id"]
    new_file_info_file = os.path.join(UPLOADED_FILE_INFO, f"{file_id}.json")
    file_functions.json_write(new_file_info_file, _data)

def get_uploaded_file_info(file_id):
    new_file_info_file = os.path.join(UPLOADED_FILE_INFO, f"{file_id}.json")
    return file_functions.json_read(new_file_info_file)

def get_logs_author_info(logs: list[bytes]):
    for line in logs:
        if b"SPELL_CAST_FAILED" not in line:
            continue
        if line.count(b'  ') > 1:
            continue
        line = line.decode()
        guid, name = line.split(',', 3)[1:3]
        name = name.replace('"', '')
        if name not in BUGGED_NAMES:
            return guid, name
    
    for line in logs[:1000]:
        if b"0x0" not in line:
            continue
        if b"nil" in line:
            continue
        line = line.decode()
        guid = line.split(',', 2)[1]
        return guid, "Unknown"
    
    return None

def _format_name(name: bytes):
    return name.decode().replace('"', '')

def slice_exists(logs_name):
    return os.path.isfile(logs_name) and os.path.getsize(logs_name) > 2048

def raw_exists(logs_id):
    raw_path_new = os.path.join(UPLOADS_TEXT, f"{logs_id}.txt")
    if os.path.isfile(raw_path_new):
        return True
    raw_path = os.path.join(LOGS_RAW_DIR, f"{logs_id}.7z")
    if logs_archive.get_archive_id(raw_path):
        return True
    raw_path_bkp = os.path.join(LOGS_RAW_DIR_BKP, f"{logs_id}.7z")
    if logs_archive.get_archive_id(raw_path_bkp):
        return True
    return False

def slice_is_fully_processed(logs_id):
    logs_folder = os.path.join(LOGS_DIR, logs_id)
    logs_name = os.path.join(logs_folder, LOGS_CUT_NAME)
    return slice_exists(logs_name) and raw_exists(logs_id)

def get_extracted_file_info(logs_path):
    mtime = os.path.getmtime(logs_path)
    _time = int(mtime)
    size = os.path.getsize(logs_path)
    file_id = f"{_time}_{size}"

    data = get_uploaded_file_info(file_id)
    if data:
        return data
    
    mod_time = constants.logs_edit_time(logs_path)
    year = datetime.fromtimestamp(_time).year
    return {
        "file_id": file_id,
        "mod_time": mod_time,
        "year": year,
        "path": logs_path,
    }

def remove_prev_folder(logs_id: str):
    report_name_info = get_report_name_info(logs_id)
    if report_name_info["server"] == DEFAULT_SERVER_NAME:
        return
    
    report_name_info["server"] = DEFAULT_SERVER_NAME
    prev_logs_id = "--".join(report_name_info.values())
    prev_logs_folder = Path(LOGS_DIR).joinpath(prev_logs_id)
    if prev_logs_folder.is_dir():
        shutil.rmtree(prev_logs_folder)


class NewUpload(Thread):
    def __init__(self, upload_data: dict[str, str], forced=False, only_slices=False, keep_temp_folder=False) -> None:
        super().__init__()
        print(upload_data)
        self.has_duplicates = False
        self.upload_data = upload_data
        self.ip = upload_data.get("ip", "localhost")
        self.timestamp = upload_data.get("timestamp")
        self.upload_dir: str = upload_data.get("upload_dir")
        if not self.upload_dir:
            self.timestamp = get_now_timestamp()
            self.upload_dir = new_upload_folder(ip=self.ip, timestamp=self.timestamp)

        self.archive_name = upload_data.get("archive", "")
        self.archive_path = os.path.join(self.upload_dir, self.archive_name)
        
        self.extracted_name = upload_data.get("extracted", "")
        self.extracted_path = os.path.join(self.upload_dir, self.extracted_name)

        self.server: str = upload_data.get("server")
        if not self.server or self.server in SERVERS.values():
            self.server = DEFAULT_SERVER_NAME
        self.forced = forced
        self.only_slices = only_slices
        self.keep_temp_folder = keep_temp_folder
        self.slice_cache: dict[str, dict] = {}

        self.timezone = upload_data.get("timezone", "")

        self.slices: dict[str, dict] = {}
        self.status_dict = {
            'done': 0,
            'status': 'Starting...',
        }

    def status_to_json(self):
        self.status_dict['slices'] = self.slices
        return json.dumps(self.status_dict)

    def change_status(self, msg, all_done=0):
        self.status_dict["status"] = msg
        self.status_dict["done"] = int(all_done)
    
    def change_slice_status(self, slice_id, status_message: str, slice_done=False):
        slice = self.slices[slice_id]
        slice["status"] = status_message
        slice["done"] = int(slice_done)
    
    def add_logger_msg(self, msg, pc: float=None, is_error=False):
        if pc is None:
            pc = perf_counter()
        msg = f"{constants.get_ms_str(pc)} | {self.ip:>15} | {msg}"
        
        if is_error:
            LOGGER_UPLOADS.error(msg)
        else:
            LOGGER_UPLOADS.debug(msg)
    
    def to_dt(self, s):
        return constants.to_dt_bytes_year_fix(s, self.year)

    def get_timedelta(self, now, before):
        return self.to_dt(now) - self.to_dt(before)
    
    def get_first_valid_timedelta(self, logs_slice: list[str], reverse=False):
        index = reverse and -1 or 0
        while logs_slice:
            line = logs_slice[index]
            try:
                return self.to_dt(line)
            except ValueError:
                logs_slice.pop(index)
    
    def to_int(self, line: bytes):
        return int(line.split(b' ', 1)[1][:8].replace(b':', b''))
    
    def to_int(self, line: bytes):
        return int(line[:14].split(b' ', 1)[1][:8].replace(b':', b''))
    
    def find_start(self):
        with open(self.extracted_path, 'rb') as logs_file:
            for line in logs_file:
                try:
                    return self.to_int(line), line
                except Exception:
                    pass
        return None
        
    def get_logs_id(self, logs_slice: list[bytes]):
        for _ in range(10):
            try:
                __date = self.to_dt(logs_slice[0])
                break
            except Exception:
                del logs_slice[0]

        date = __date.strftime("%y-%m-%d--%H-%M")

        logs_author_info = get_logs_author_info(logs_slice)
        if logs_author_info is None:
            return f'{date}--Unknown--{self.server}'

        guid, name = logs_author_info
        server = SERVERS.get(guid[:4], self.server)
        return f'{date}--{name}--{server}'
    
    def get_slice_info(self, logs_slice: list[bytes]):
        entities: defaultdict[bytes, int] = defaultdict(int)
        names = {}

        _skip = len(logs_slice) // 5000 + 1
        for line in logs_slice[::_skip]:
            try:
                guid, name = line.split(b',', 6)[4:6]
            except ValueError:
                continue
            
            names[guid] = name
            entities[guid] += 1

        bosses = []
        players = set()
        for guid, c in entities.items():
            if c < 10:
                continue
            if guid[:5] in {b"0xF13", b"0xF15"}:
                _fight_name = constants.convert_to_fight_name(guid[6:-6].decode())
                if _fight_name and _fight_name not in bosses:
                    bosses.append(_fight_name)
            elif guid[:3] == b"0x0" and guid != b"0x0000000000000000":
                players.add(_format_name(names[guid]))

        duration = 0
        start = self.get_first_valid_timedelta(logs_slice)
        end = self.get_first_valid_timedelta(logs_slice, reverse=True)
        if start and end:
            duration = (end - start).seconds

        return {
            'players': sorted(players),
            'bosses': bosses,
            'duration': duration,
            "length": len(logs_slice)
        }

    def get_slice_info_wrap(self, segment):
        if not segment:
            return {}
        
        first_line = segment[0]
        if first_line in self.slice_cache:
            _slice_info = self.slice_cache[first_line]
            if _slice_info.get("length") == len(segment):
                return self.slice_cache[first_line]
        
        slice_info = self.get_slice_info(segment)
        self.slice_cache[first_line] = slice_info
        return slice_info

    def save_slice_cache(self, logs_slice: list):
        if not logs_slice:
            return
        
        logs_id = self.get_logs_id(logs_slice)
        
        msg = f"Sliced     | {logs_id} | {sys.getsizeof(logs_slice):>12,} | {len(logs_slice):>12,}"
        self.add_logger_msg(msg, pc=self.pc_slice)

        _slice_info = self.get_slice_info_wrap(logs_slice)
        if not _slice_info.get('bosses'):
            return
        self.slices[logs_id] = _slice_info

        if not self.forced and slice_is_fully_processed(logs_id):
            self.has_duplicates = True
            self.change_slice_status(logs_id, "Done!", slice_done=True)
            self.add_logger_msg(f"Exists     | {logs_id}")
            return
    
        if logs_slice[-1][-1] != b'\n':
            del logs_slice[-1]
        
        self.change_slice_status(logs_id, "Standby...")
        pc_slice_save = perf_counter()
        slice_name = os.path.join(self.upload_dir, f"{logs_id}.txt")
        with open(slice_name, 'wb') as file:
            file.writelines(logs_slice)
        logs_slice.clear()
        os.utime(slice_name, (self.mtime, self.mtime))

        self.add_logger_msg(f"Saved      | {logs_id}", pc_slice_save)
    
    def save_slice_cache_wrap(self, logs_slice: list):
        self.save_slice_cache(logs_slice)
        logs_slice.clear()
        self.pc_slice = perf_counter()

    def slice_logs(self):
        _last = self.find_start()
        if _last is None:
            return
        
        last_timestamp, last_line = _last
        current_segment = []
        last_segment = []

        def is_big_gap():
            if not last_segment: return True
            
            segments_tdelta = self.get_timedelta(current_segment[0], last_segment[-1])
            # print("is_big_gap segments_tdelta", segments_tdelta)
            # print(last_segment[-1])
            # print(current_segment[0])
            return segments_tdelta > BIG_GAP

        def __save_segment():
            last_slice_info = self.get_slice_info_wrap(last_segment)
            current_slice_info = self.get_slice_info_wrap(current_segment)

            players_last = set(last_slice_info.get("players", []))
            players_current = set(current_slice_info.get("players", []))
            _intersection = players_last & players_current
            max_len = max(len(players_last), len(players_current))
            if current_slice_info.get("length", 0) < 1000:
                different_raid = len(_intersection) < max_len // 5
            else:
                different_raid = len(_intersection) < max_len // 2

            if different_raid or is_big_gap():
                # print("different_raid")
                # print("players_lst", sorted(players_last))
                # print("players_now ", sorted(players_current))
                # print("bosses_lst ", sorted(last_slice_info.get("bosses", [])))
                # print("bosses_now ", sorted(current_slice_info.get("bosses", [])))
                self.save_slice_cache_wrap(last_segment)
            last_segment.extend(current_segment)
            current_segment.clear()

        with open(self.extracted_path, 'rb') as _file:
            self.pc_slice = perf_counter()
            for line in _file:
                try:
                    timestamp = self.to_int(line)
                except Exception:
                    # print("Exception: self.to_int", line)
                    continue
                
                _delta = timestamp - last_timestamp
                if _delta > 100 or _delta < 0:
                    try:
                        _tdelta = self.get_timedelta(line, last_line)
                    except Exception:
                        # print("Exception: self.get_timedelta")
                        # print(last_line)
                        # print(line)
                        try:
                            self.to_dt(last_line)
                        except TypeError:
                            last_timestamp = timestamp
                            last_line = line
                        continue
                    
                    if _tdelta > SMALL_GAP:
                        # print(f"\nNew jump: {last_timestamp:0>6} {timestamp:0>6}")
                        # print(last_line.decode() + line.decode())
                        __save_segment()

                current_segment.append(line)
                last_timestamp = timestamp
                last_line = line
        
        print("=============== DONE ===============")
        __save_segment()
        self.save_slice_cache_wrap(last_segment)

    def finish_slice(self, logs_id):
        logs_folder = os.path.join(LOGS_DIR, logs_id)
        logs_name = os.path.join(logs_folder, LOGS_CUT_NAME)
        if not self.forced and slice_exists(logs_name):
            return

        if os.path.isdir(logs_folder):
            shutil.rmtree(logs_folder)

        remove_prev_folder(logs_id)
        
        logs_folder = file_functions.new_folder_path(LOGS_DIR, logs_id)
        
        pc_slice_cleaner = perf_counter()
        slice_name = os.path.join(self.upload_dir, f"{logs_id}.txt")
        self.change_slice_status(logs_id, "Formatting slice...")
        logs = logs_fix.trim_logs(slice_name)
        logs = b'\n'.join(logs)
        self.change_slice_status(logs_id, "Saving slice...")
        logs = file_functions.zstd_compress(logs)
        file_functions.bytes_write(logs_name, logs)
        self.change_slice_status(logs_id, "Done!", slice_done=True)

        self.add_logger_msg(f"Done       | {logs_id}", pc_slice_cleaner)

    def is_fully_proccessed(self):
        if self.forced or not self.upload_data:
            return False
        if not self.upload_data.get("slices"):
            return False
        
        old_server = self.upload_data.get("server")
        if old_server and old_server != DEFAULT_SERVER_NAME:
            self.server = old_server
        elif self.server != DEFAULT_SERVER_NAME:
            self.upload_data["server"] = self.server
            return False
        
        file_id = self.upload_data.get('file_id')
        if not file_id:
            return False
        
        done = True
        self.slices = self.upload_data["slices"]
        for slice_id in self.slices:
            if slice_is_fully_processed(slice_id):
                self.has_duplicates = True
                self.change_slice_status(slice_id, "Done!", slice_done=True)
            else:
                self.change_slice_status(slice_id, "Standby...")
                done = False
        
        if not done:
            return False

        self.status_dict["slices"] = self.slices
        if not self.slices:
            self.finish(ALREADY_DONE_NONE_FOUND)
        else:
            self.finish(ALREADY_DONE)
        return True

    def extract_archive(self):
        file_id = logs_archive.get_archive_id(self.archive_path)
        if file_id is None:
            self.change_status(ARCHIVE_ID_ERROR, 1)
            self.add_logger_msg(ARCHIVE_ID_ERROR)
            return False

        self.upload_data["file_id"] = file_id
        uploaded_file_info = get_uploaded_file_info(file_id)
        self.upload_data = self.upload_data | uploaded_file_info
        if uploaded_file_info and self.is_fully_proccessed():
            return False
        
        self.change_status("Extracting...")
        pc_extract = perf_counter()
        uploaded_file_info = logs_archive.get_archive_data(self.archive_path)
        if not uploaded_file_info:
            self.finish(ARCHIVE_ERROR, True)
            return False
        
        self.add_logger_msg("Extracted", pc_extract)

        self.upload_data = self.upload_data | uploaded_file_info
        self.extracted_name = uploaded_file_info["extracted"]
        self.extracted_path = os.path.join(self.upload_dir, self.extracted_name)
        return True

    def main(self):
        self.pc_main = perf_counter()

        if os.path.isfile(self.extracted_path):
            uploaded_file_info = get_extracted_file_info(self.extracted_path)
            self.upload_data = self.upload_data | uploaded_file_info
            if self.is_fully_proccessed():
                return
        elif os.path.isfile(self.archive_path):
            if not self.extract_archive():
                return
        else:
            self.finish(UPLOAD_GONE, True)
            return

        self.year = self.upload_data["year"]
        self.mtime = os.path.getmtime(self.extracted_path)

        logs_fix.check_null_bug(self.extracted_path)

        self.change_status(START_SLICING)
        self.slice_logs()

        if not self.slices:
            self.finish(FULL_DONE_NONE_FOUND)
            return

        if self.only_slices:
            for logs_id in self.slices:
                print(logs_id)
            self.change_status(FULL_DONE, 1)
            return

        self.change_status(SAVING_SLICES)
        for logs_id in self.slices:
            self.finish_slice(logs_id)

        if self.has_duplicates:
            self.finish(FULL_DONE_PARTIAL)
        else:
            self.finish(FULL_DONE)
    
    def move_sliced_logs(self):
        for logs_id in self.slices:
            self.change_slice_status(logs_id, "Done!", slice_done=True)
            raw_path_current = os.path.join(self.upload_dir, f"{logs_id}.txt")
            if not os.path.isfile(raw_path_current):
                continue
            
            if not self.forced and raw_exists(logs_id):
                self.add_logger_msg(f"Raw exists | {logs_id}")
                continue
            
            raw_path_new = os.path.join(UPLOADS_TEXT, f"{logs_id}.txt")
            if os.path.isfile(raw_path_new):
                os.remove(raw_path_new)
            os.rename(raw_path_current, raw_path_new)
            self.add_logger_msg(f"Raw moved  | {logs_id}")
            
            if self.timezone:
                raw_path_tz = os.path.join(UPLOADS_TEXT, f"{logs_id}.timezone")
                file_functions.file_write(raw_path_tz, self.timezone)
                self.add_logger_msg(f"Timezone w | {logs_id}")
    
    def move_uploaded_file(self, is_error=False):
        old = self.archive_path or self.extracted_path
        basename = os.path.basename(old)
        _file_id = f"{self.ip}--{self.timestamp}--{basename}"
        if is_error:
            new_archive_name = os.path.join(UPLOADS_TODO, _file_id)
        else:
            new_archive_name = os.path.join(UPLOADED_DIR, _file_id)
            self.upload_data["uploaded"] = new_archive_name
        os.rename(old, new_archive_name)

    def finish(self, msg: str, is_error=False):
        self.change_status(SEMI_DONE)
        self.move_sliced_logs()
        self.move_uploaded_file(is_error)

        self.upload_data.setdefault("ips", []).append(self.ip)
        self.upload_data.setdefault("timestamps", []).append(self.timestamp)
        self.upload_data["slices"] = self.slices
        save_upload_cache(self.upload_data)

        if not self.keep_temp_folder:
            shutil.rmtree(self.upload_dir, ignore_errors=True)

        self.change_status(msg, 1)
        self.add_logger_msg(msg, pc=self.pc_main, is_error=is_error)

    def run(self):
        try:
            self.main()
        
        except Exception:
            LOGGER_UPLOADS.exception(f"{self.upload_dir} | NewUpload run")
            self.status_dict['slices'] = {}
            self.finish(LOGS_ERROR)


class FileSave:
    def __init__(self) -> None:
        self.date = 0
        self.chunks: list[bytes] = []
        self.upload_thread: NewUpload = None
        self.current_chunk = 0
        self.started = perf_counter()
    
    def done(self, ip, data):
        j: dict[str, str]
        if data:
            j = json.loads(data)
        else:
            j = {}

        timestamp = get_now_timestamp()
        new_upload_dir = new_upload_folder(ip, timestamp)
        filename = format_filename(j.get("filename"))
        full_file_path = os.path.join(new_upload_dir, filename)

        with open(full_file_path, 'wb') as f:
            f.write(b''.join(self.chunks))
        
        upload_data = {
            "upload_dir": new_upload_dir,
            "archive": full_file_path,
            "server": j.get('server'),
            "ip": ip,
            "timezone": j.get('timezone'),
            "timestamp": timestamp,
        }
        
        self.upload_thread = NewUpload(upload_data)
        self.upload_thread.start()

        msg = f"{constants.get_ms_str(self.started)} | {ip:>15} | Uploaded   | {len(self.chunks):>3} | {self.current_chunk:>3}"
        LOGGER_UPLOADS.debug(msg)

    def add_chunk(self, chunk: bytes, chunkN: int, date: int):
        if self.date != date:
            self.chunks.clear()
            self.date = date

        if not chunk:
            return
        
        if chunk in self.chunks[-2:]:
            return True
        
        if len(self.chunks) + 1 != chunkN:
            return
        
        self.current_chunk = chunkN
        self.chunks.append(chunk)
        return True


class File:
    # helper class for Flask.File type hints
    def __init__(self, current_path) -> None:
        self.current_path = current_path
        self.filename: str = os.path.basename(current_path)
        self.name, self.ext = self.filename.rsplit('.', 1)
    
    def save(self, new_path):
        shutil.copyfile(self.current_path, new_path)


def main_archive(file: File, ip='localhost', server=None, timezone=None, forced=False):
    timestamp = get_now_timestamp()
    new_upload_dir = new_upload_folder(ip, timestamp)
    file_name = format_filename(file.filename)
    full_file_path = os.path.join(new_upload_dir, file_name)
    file.save(full_file_path)
    upload_data = {
        "upload_dir": new_upload_dir,
        "archive": full_file_path,
        "server": server,
        "ip": ip,
        "timezone": timezone,
        "timestamp": timestamp,
    }
    return NewUpload(upload_data, forced=forced)


def main_local_text(logs_path, ip="localhost", forced=False, dont_clean=False, only_slices=False):
    upload_data = {
        "upload_dir": new_upload_folder(ip),
        "archive": "",
        "extracted": logs_path,
        "server": None,
        "ip": ip
    }
    return NewUpload(upload_data, forced=forced, keep_temp_folder=dont_clean, only_slices=only_slices)


def __main():
    import sys
    try:
        name = sys.argv[1]
    except IndexError as e:
        name = r"F:\World of Warcraft 3.3.5a HD\Logs\WoWCombatLog.txt"
        print(e)
    if name.endswith('.txt'):
        _main_thread = main_local_text(name)
    else:
        new_file = File(name)
        _main_thread = main_archive(new_file)
    
    if _main_thread is not None:
        _main_thread.start()
        _main_thread.join()
        input("\nDONE!\nPRESS ANY BUTTON OR CLOSE...")


if __name__ == "__main__":
    __main()
