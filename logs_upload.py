import json
import os
import re
import shutil
import sys
import zlib
from collections import defaultdict
from datetime import datetime
from threading import Thread
from time import perf_counter

import constants
import file_functions
import logs_archive
import logs_fix
import logs_top
import logs_top_server
from constants import LOGGER_UPLOADS, LOGS_CUT_NAME, LOGS_DIR, PATH_DIR, SERVERS, T_DELTA, UPLOADED_DIR, UPLOADS_DIR

ARCHIVE_ID_ERROR = "Bad archive. Don't rename files to .zip/.7z, create archives from 0."
ARCHIVE_ERROR = "Error unziping file. Make sure logs file inside the archive without any folders."
LOGS_ERROR = "Error parsing logs."
TOP_ERROR = "Done! Select 1 of the reports below. Top update encountered an error."
ALREADY_DONE = "File has been uploaded already! Select 1 of the reports below."
FULL_DONE = "Done! Select 1 of the reports below."
FULL_DONE_NONE_FOUND = "Done! No boss segments were found! Make sure to use /combatlog"
SAVING_SLICES = "Saving log slices..."
SEMI_DONE = "Finishing caching..."
TOP_UPDATE = "Updating top..."
BUGGED_NAMES = {"nil", "Unknown"}
file_functions.create_new_folders(PATH_DIR, LOGS_DIR, UPLOADS_DIR, UPLOADED_DIR)

UPLOADED_FILES_FILE = os.path.join(PATH_DIR, '_uploaded_files.json')
UPLOADED_FILES: dict[str, dict] = file_functions.json_read(UPLOADED_FILES_FILE)
UPLOADED_LOGS_FILE = os.path.join(PATH_DIR, '_uploaded_logs.json')
UPLOADED_LOGS: dict[str, dict] = file_functions.json_read(UPLOADED_LOGS_FILE)
def save_upload_cache(_data, slices):
    u_logs = file_functions.json_read(UPLOADED_LOGS_FILE)
    u_logs_old = dict(u_logs)
    u_logs.update(slices)   
    if u_logs != u_logs_old:
        file_functions.json_write(UPLOADED_LOGS_FILE, u_logs)
        UPLOADED_LOGS.update(u_logs)

    new_upload_data = dict(_data)
    new_upload_data['logs_list'] = sorted(slices)
    file_id = _data["file_id"]
    u_files = file_functions.json_read(UPLOADED_FILES_FILE)
    u_files_old = dict(u_files)
    u_files[file_id] = new_upload_data
    if u_files != u_files_old:
        file_functions.json_write(UPLOADED_FILES_FILE, u_files)
        UPLOADED_FILES.update(u_files)

def get_logs_author_info(logs: list[bytes]):
    for line in logs:
        if b"SPELL_CAST_FAILED" not in line:
            continue
        line = line.decode()
        guid, name = line.split(',', 3)[1:3]
        name = name.replace('"', '')
        if name not in BUGGED_NAMES:
            return guid, name
    return None

def _format_name(name: bytes):
    return name.decode().replace('"', '')

def slice_exists(logs_name):
    return os.path.isfile(logs_name) and os.path.getsize(logs_name) > 2048

def slice_fully_processed(logs_id):
    logs_folder = os.path.join(LOGS_DIR, logs_id)
    logs_name = os.path.join(logs_folder, f"{LOGS_CUT_NAME}.zlib")
    return slice_exists(logs_name) and logs_archive.valid_raw_logs(logs_id)

def get_extracted_file_info(logs_path):
    mtime = os.path.getmtime(logs_path)
    _time = int(mtime)
    size = os.path.getsize(logs_path)
    file_id = f"{_time}_{size}"

    data = UPLOADED_FILES.get(file_id)
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


class NewUpload(Thread):
    def __init__(self, upload_data: dict[str, str], forced=False, only_slices=False, keep_temp_folder=False) -> None:
        super().__init__()
        self.upload_data = upload_data
        self.upload_dir: str = upload_data["upload_dir"]
        self.server: str = upload_data.get("server") or "Unknown"
        self.forced = forced
        self.only_slices = only_slices
        self.keep_temp_folder = keep_temp_folder
        self.slice_cache: dict[str, dict] = {}

        self.slices: dict[str, dict] = {}
        self.status_dict = {
            'done': 0,
            'status': 'Determinating log slices...',
            'slices': self.slices
        }
        self.status_json = json.dumps(self.status_dict)

    def status_to_json(self):
        self.status_json = json.dumps(self.status_dict)

    def change_status(self, msg, all_done=0):
        self.status_dict["status"] = msg
        self.status_dict["done"] = int(all_done)
        self.status_to_json()
    
    def change_slice_status(self, slice_id, status_message: str, slice_done=False):
        slice = self.slices[slice_id]
        slice["status"] = status_message
        slice["done"] = int(slice_done)
        self.status_to_json()
    
    def add_logger_msg(self, msg, timestamp: float=None, is_error=False):
        msg = f"{self.upload_dir} | {msg}"
        if timestamp is not None:
            msg = f"{constants.get_ms_str(timestamp)} | {msg}"
        
        if is_error:
            LOGGER_UPLOADS.error(msg)
        else:
            LOGGER_UPLOADS.debug(msg)
    
    def to_dt(self, s):
        return constants.to_dt_bytes_year_fix(s, self.year)

    def get_timedelta(self, now, before):
        return self.to_dt(now) - self.to_dt(before)
    
    def to_int(self, line: bytes):
        return int(line.split(b' ', 1)[1][:8].replace(b':', b''))
    
    def to_int(self, line: bytes):
        return int(line[:14].split(b' ', 1)[1][:8].replace(b':', b''))
    
    def find_start(self):
        with open(self.extracted_file, 'rb') as logs_file:
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

        entities = {k:v for k,v in entities.items() if v > 10}
        bosses = set()
        players = set()
        for guid in entities:
            if guid[:5] in {b"0xF13", b"0xF15"}:
                _fight_name = constants.convert_to_fight_name(guid[6:-6].decode())
                if _fight_name:
                    bosses.add(_fight_name)
            elif guid[:3] == b"0x0" and guid != b"0x0000000000000000":
                players.add(_format_name(names[guid]))

        _tdelta = self.get_timedelta(logs_slice[-1], logs_slice[0])
        return {
            'players': sorted(players),
            'bosses': sorted(bosses),
            'duration': _tdelta.seconds,
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
        
        # timestamp = perf_counter()
        slice_info = self.get_slice_info(segment)
        # self.add_logger_msg("Got slice info", timestamp)

        self.slice_cache[first_line] = slice_info
        return slice_info

    def save_slice_cache(self, logs_slice: list):
        if not logs_slice:
            return
        
        logs_id = self.get_logs_id(logs_slice)
        
        msg = f"Sliced | {logs_id} | {sys.getsizeof(logs_slice):>12,} | {len(logs_slice):>12,}"
        self.add_logger_msg(msg, self.timestamp)

        _slice_info = self.get_slice_info_wrap(logs_slice)
        print("_slice_info", _slice_info)
        if not _slice_info.get('bosses'):
            return
        self.slices[logs_id] = _slice_info

        if not self.forced and slice_fully_processed(logs_id):
            self.change_slice_status(logs_id, "Done!", slice_done=True)
            self.add_logger_msg(f"{logs_id} | Exists")
            return
        
        if logs_slice[-1][-1] != b'\n':
            del logs_slice[-1]
        
        self.change_slice_status(logs_id, "Standby...")
        timestamp = perf_counter()
        slice_name = os.path.join(self.upload_dir, f"{logs_id}.txt")
        data_joined, _ = b''.join(logs_slice), logs_slice.clear()
        file_functions.bytes_write(slice_name, data_joined)
        os.utime(slice_name, (self.mtime, self.mtime))

        self.add_logger_msg(f"{logs_id} | Slice saved", timestamp)
    
    def save_slice_cache_wrap(self, logs_slice: list):
        self.save_slice_cache(logs_slice)
        logs_slice.clear()
        self.timestamp = perf_counter()

    def slice_logs(self):
        _last = self.find_start()
        if _last is None:
            return
        
        last_timestamp, last_line = _last
        current_segment = []
        last_segment = []

        SMALL_GAP = T_DELTA["1MIN"]
        THIRTY_MINUTES = T_DELTA["30MIN"]

        def __save_segment(big_gap):
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

            if big_gap:
                if different_raid:
                    self.save_slice_cache_wrap(current_segment)
                else:
                    last_segment.extend(current_segment)
                    current_segment.clear()
                
                self.save_slice_cache_wrap(last_segment)
            else:
                if not last_slice_info.get("bosses"):
                    last_segment.clear()
                elif different_raid:
                    self.save_slice_cache_wrap(last_segment)
                last_segment.extend(current_segment)
                current_segment.clear()

        with open(self.extracted_file, 'rb') as _file:
            self.timestamp = perf_counter()
            for line in _file:
                try:
                    timestamp = self.to_int(line)
                except Exception:
                    print("Exception: self.to_int", line)
                    continue
                
                _delta = timestamp - last_timestamp
                if _delta > 100 or _delta < 0:
                    print("\nNew jump:", last_timestamp, timestamp)
                    print(last_line.decode() + line.decode())
                    try:
                        _tdelta = self.get_timedelta(line, last_line)
                    except Exception:
                        print("Exception: self.get_timedelta", line, last_line)
                        continue
                    
                    if _tdelta > SMALL_GAP:
                        print("_tdelta > SMALL_GAP")
                        __save_segment(_tdelta > THIRTY_MINUTES)

                current_segment.append(line)
                last_timestamp = timestamp
                last_line = line
        
        __save_segment(True)

    def finish_slice(self, logs_id):
        logs_folder = os.path.join(LOGS_DIR, logs_id)
        logs_name = os.path.join(logs_folder, f"{LOGS_CUT_NAME}.zlib")
        if not self.forced and self.slices[logs_id].get('done') and slice_exists(logs_name):
            self.change_slice_status(logs_id, "Done!", slice_done=True)
            return

        if logs_id in logs_folder:
            shutil.rmtree(logs_folder, ignore_errors=True)
        logs_folder = file_functions.new_folder_path(LOGS_DIR, logs_id)
        
        timestamp = perf_counter()
        
        slice_name = os.path.join(self.upload_dir, f"{logs_id}.txt")
        self.change_slice_status(logs_id, "Formatting slice...")
        logs = logs_fix.trim_logs(slice_name)
        logs = b'\n'.join(logs)
        self.change_slice_status(logs_id, "Saving slice...")
        logs = zlib.compress(logs, level=7)
        file_functions.bytes_write(logs_name, logs)
        self.change_slice_status(logs_id, "Done!", slice_done=True)

        self.add_logger_msg(f"{logs_id} | Slice done", timestamp)

    def main(self):
        self.slice_logs()

        if not self.slices:
            self.change_status(FULL_DONE_NONE_FOUND, 1)
            return

        if self.only_slices:
            self.change_status(FULL_DONE, 1)
            return

        self.change_status(SAVING_SLICES)
        for logs_id in self.slices:
            self.finish_slice(logs_id)
        
        self.change_status(SEMI_DONE)
        for logs_id in self.slices:
            logs_archive.save_raw_logs(logs_id, self.upload_dir, self.forced)

        self.change_status(TOP_UPDATE)
        try:
            for logs_id in self.slices:
                logs_top.make_report_top(logs_id)
            logs_top_server.add_new_reports_wrap(self.slices)
        except Exception:
            LOGGER_UPLOADS.exception(f"{self.upload_dir} | NewUpload top update")
            self.change_status(TOP_ERROR, 1)
            return
        
        self.change_status(FULL_DONE, 1)

    def already_uploaded(self):
        if self.forced or not self.file_data:
            return False
        
        logs_list = self.file_data.get('logs_list')
        if not logs_list:
            return False
        
        for logs_id in logs_list:
            _slice = UPLOADED_LOGS.get(logs_id)
            if _slice and _slice.get("done") and slice_fully_processed(logs_id):
                self.slices[logs_id] = _slice
            else:
                return False

        self.change_status(ALREADY_DONE, 1)
        self.finish()
        return True

    def extract_archive(self):
        archive_path = self.upload_data.get("archive")
        if not archive_path:
            self.change_status(ARCHIVE_ID_ERROR, 1)
            self.add_logger_msg(f"{archive_path} {ARCHIVE_ID_ERROR}")
            return

        file_id = logs_archive.get_archive_id(archive_path)
        if file_id is None:
            self.change_status(ARCHIVE_ID_ERROR, 1)
            self.add_logger_msg(f"{archive_path} {ARCHIVE_ID_ERROR}")
            return

        self.file_data = UPLOADED_FILES.get(file_id)
        if self.already_uploaded():
            self.add_logger_msg(f"{archive_path} already uploaded")
            return
        
        self.change_status("Extracting...")
        archive_data = logs_archive.new_archive(archive_path, self.upload_dir)
        if not archive_data:
            self.change_status(ARCHIVE_ERROR, 1)
            self.add_logger_msg(f"{archive_path} {ARCHIVE_ERROR}", is_error=True)
            return
        
        self.upload_data["extracted"] = archive_data["extracted"]
        return archive_data

    def run(self):
        if self.upload_data is None:
            self.add_logger_msg("self.upload_data is None", is_error=True)
            return
        
        extracted_file = self.upload_data.get("extracted")
        if extracted_file:
            print('extracted')
            archive_data = get_extracted_file_info(extracted_file)
        else:
            print('run new file')
            archive_data = self.extract_archive()
            if not archive_data:
                return
        
        self.file_data = archive_data
        self.year = archive_data["year"]
        self.extracted_file = self.upload_data["extracted"]
        self.mtime = os.path.getmtime(self.extracted_file)
        
        if self.already_uploaded():
            return
        
        timestamp = perf_counter()

        try:
            self.main()
        
        except Exception:
            LOGGER_UPLOADS.exception(f"{self.upload_dir} | NewUpload run")
            self.status_dict['slices'] = {}
            self.change_status(LOGS_ERROR, 1)
        
        finally:
            self.add_logger_msg("Done", timestamp)
            self.finish()
            
    def finish(self):
        try:
            save_upload_cache(self.file_data, self.slices)
        except Exception:
            LOGGER_UPLOADS.exception(f"{self.upload_dir} | NewUpload finish")

        if self.keep_temp_folder:
            return

        if "uploads" not in self.upload_dir:
            self.add_logger_msg("NewUpload 'uploads' not in self.upload_dir", is_error=True)
            return

        try:
            old = self.upload_data.get("archive") or self.upload_data.get("extracted")
            sep = '/' if '/' in old else '\\'
            _, ip, date = self.upload_dir.rsplit(sep, 2)
            basename = os.path.basename(old)
            new = os.path.join(UPLOADED_DIR, f"{ip}--{date}--{basename}")
            os.rename(old, new)
            shutil.rmtree(self.upload_dir, ignore_errors=True)
        except Exception:
            LOGGER_UPLOADS.exception(f"{self.upload_dir} | NewUpload cleaning")


class File:
    # helper class for Flask.File type hints
    def __init__(self, current_path) -> None:
        self.current_path = current_path
        self.filename: str = os.path.basename(current_path)
        self.name, self.ext = self.filename.rsplit('.', 1)
    
    def save(self, new_path):
        shutil.copyfile(self.current_path, new_path)

def format_filename(file_name):
    if not file_name:
        return "archive.7z"

    *words, ext = re.findall('([A-Za-z0-9]+)', file_name)
    return f"{'_'.join(words)}.{ext}"

def new_upload_folder(ip='localhost'):
    new_upload_dir_ip = file_functions.new_folder_path(UPLOADS_DIR, ip)
    timestamp = constants.get_now().strftime("%y-%m-%d--%H-%M-%S")
    new_upload_dir = file_functions.new_folder_path(new_upload_dir_ip, timestamp)
    return new_upload_dir

def main(file: File, ip='localhost', server=None, forced=False):
    new_upload_dir = new_upload_folder(ip)
    file_name = format_filename(file.filename)
    full_file_path = os.path.join(new_upload_dir, file_name)
    file.save(full_file_path)
    upload_data = {
        "upload_dir": new_upload_dir,
        "archive": full_file_path,
        "server": server,
        "ip": ip,
    }
    return NewUpload(upload_data, forced=forced)

class FileSave:
    def __init__(self) -> None:
        self.date = 0
        self.chunks = []
        self.upload_thread = None
        self.current_chunk = 0
        self.started = perf_counter()
    
    def done(self, request):
        j: dict[str, str]
        IP = request.remote_addr
        new_upload_dir = new_upload_folder(IP)

        data = getattr(request, "data", None)
        if data:
            j = json.loads(data)
        else:
            j = {}

        filename = format_filename(j.get("filename"))
        full_file_path = os.path.join(new_upload_dir, filename)

        with open(full_file_path, 'wb') as f:
            f.write(b''.join(self.chunks))
        
        upload_data = {
            "upload_dir": new_upload_dir,
            "archive": full_file_path,
            "server": j.get('server'),
            "ip": IP,
        }

        LOGGER_UPLOADS.info(f"{constants.get_ms_str(self.started)} | {new_upload_dir} | {len(self.chunks):>3} | {self.current_chunk:>3}")
        
        self.upload_thread = NewUpload(upload_data)
        self.upload_thread.start()

    def add_chunk(self, chunk, chunkN, date):
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
        _main_thread = main(new_file)
    
    if _main_thread is not None:
        _main_thread.start()
        _main_thread.join()
        input("\nDONE!\nPRESS ANY BUTTON OR CLOSE...")


if __name__ == "__main__":
    __main()
