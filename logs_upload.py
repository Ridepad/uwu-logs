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
import logs_archive
import logs_fix
import logs_top
import logs_top_server
from constants import (
    BOSSES_GUIDS, LOGS_CUT_NAME, LOGS_DIR, PATH_DIR, SERVERS, T_DELTA_5MIN, T_DELTA_30MIN, UPLOAD_LOGGER, UPLOADS_DIR, UPLOADED_DIR,
    bytes_write, get_ms, json_read, json_write, new_folder_path, sort_dict_by_value, to_dt_bytes)


ARCHIVE_ID_ERROR = "Bad archive."
ARCHIVE_ERROR = "Error unziping file."
LOGS_ERROR = "Error parsing logs."
ALREADY_DONE = "File has been uploaded already! Select 1 of the reports below."
FULL_DONE = "Done! Select 1 of the reports below."
SAVING_SLICES = "Saving log slices..."
SEMI_DONE = "Finishing caching..."
TOP_UPDATE = "Updating top..."
BUGGED_NAMES = {"nil", "Unknown"}

UPLOADED_FILES_FILE = os.path.join(PATH_DIR, '_uploaded_files.json')
UPLOADED_FILES: dict[str, dict] = json_read(UPLOADED_FILES_FILE)
UPLOADED_LOGS_FILE = os.path.join(PATH_DIR, '_uploaded_logs.json')
UPLOADED_LOGS: dict[str, dict] = json_read(UPLOADED_LOGS_FILE)
def save_upload_cache(_data, slices):
    u_logs = json_read(UPLOADED_LOGS_FILE)
    u_logs_old = dict(u_logs)
    u_logs.update(slices)   
    if u_logs != u_logs_old:
        json_write(UPLOADED_LOGS_FILE, u_logs)
        UPLOADED_LOGS.update(u_logs)

    new_upload_data = dict(_data)
    new_upload_data['logs_list'] = sorted(slices)
    file_id = _data["file_id"]
    u_files = json_read(UPLOADED_FILES_FILE)
    u_files_old = dict(u_files)
    u_files[file_id] = new_upload_data
    if u_files != u_files_old:
        json_write(UPLOADED_FILES_FILE, u_files)
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

def get_author_guid(logs_slice):
    logs_author_info = get_logs_author_info(logs_slice)
    return logs_author_info and logs_author_info[0]

def _format_name(name: bytes):
    return name.decode().replace('"', '')

def slice_exists(logs_name):
    return os.path.isfile(logs_name) and os.path.getsize(logs_name) > 2048

def slice_fully_processed(logs_id):
    logs_folder = os.path.join(LOGS_DIR, logs_id)
    logs_name = os.path.join(logs_folder, f"{LOGS_CUT_NAME}.zlib")
    return slice_exists(logs_name) and logs_archive.valid_raw_logs(logs_id)

class NewUpload(Thread):
    def __init__(self, upload_data: dict, forced=False) -> None:
        super().__init__()
        self.upload_data = upload_data
        self.upload_dir: str = upload_data["upload_dir"]
        self.server = upload_data.get("server")
        if self.server is None:
            self.server = "Unknown"
        self.forced = forced

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
    
    def to_dt(self, s):
        return to_dt_bytes(s, self.year)

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
        s = defaultdict(int)
        names = {}
        for line in logs_slice[::250]:
            guid, name = line.split(b',', 6)[4:6]
            names[guid] = name
            s[guid] += 1
            # if guid[:5] in {b"0xF13", b"0xF15"}:

        # add players
        s = sort_dict_by_value(s)
        s2 = [guid[6:-6].decode() for guid in s if guid[:5] in {b"0xF13", b"0xF15"}]
        npcs = [BOSSES_GUIDS[guid] for guid in s2 if guid in BOSSES_GUIDS]
        players = [_format_name(names[guid]) for guid in s if guid[:3] == b"0x0"]
        if "nil" in players:
            players.remove("nil")

        _tdelta = self.get_timedelta(logs_slice[-1], logs_slice[0])
        return {
            'players': players[:5],
            'enemies': npcs[:5],
            'duration': _tdelta.seconds,
        }

    def save_slice_cache(self, logs_slice: list):
        if not logs_slice:
            return
        
        logs_id = self.get_logs_id(logs_slice)
        
        _time = get_ms(self.pc)
        UPLOAD_LOGGER.debug(f'{logs_id} | Done in: {_time:>6,} ms | SIZE: {sys.getsizeof(logs_slice):>12,} | LEN: {len(logs_slice):>12,}')

        _slice_info = self.get_slice_info(logs_slice)
        print(_slice_info)
        if not _slice_info.get('enemies'):
            return
        self.slices[logs_id] = _slice_info

        if not self.forced and slice_fully_processed(logs_id):
            self.change_slice_status(logs_id, "Done!", slice_done=True)
            UPLOAD_LOGGER.debug(f'{logs_id} exists!')
            return
        
        if logs_slice[-1][-1] != b'\n':
            del logs_slice[-1]
        
        self.change_slice_status(logs_id, "Standby...")
        _pc = perf_counter()
        slice_name = os.path.join(self.upload_dir, f"{logs_id}.txt")
        data_joined, _ = b''.join(logs_slice), logs_slice.clear()
        bytes_write(slice_name, data_joined)
        os.utime(slice_name, (self.mtime, self.mtime))
        UPLOAD_LOGGER.debug(f'{logs_id} Done in: {get_ms(_pc)} ms')
    
    def save_slice_cache_wrap(self, logs_slice: list):
        self.save_slice_cache(logs_slice)
        logs_slice.clear()
        self.pc = perf_counter()

    def slice_logs(self):
        _last = self.find_start()
        if _last is None:
            return
        
        last_timestamp, last_line = _last
        current_segment = []
        last_segment = []
        last_guid = None

        def __save_segment(current_guid):
            if current_guid == last_guid:
                last_segment.extend(current_segment)
                current_segment.clear()
                self.save_slice_cache_wrap(last_segment)
            else:
                self.save_slice_cache_wrap(last_segment)
                self.save_slice_cache_wrap(current_segment)

        with open(self.extracted_file, 'rb') as f:
            self.pc = perf_counter()
            for line in f:
                try:
                    timestamp = self.to_int(line)
                except Exception:
                    continue
                
                _delta = timestamp - last_timestamp
                if (_delta > 100 or _delta < 0):
                    try:
                        _tdelta = self.get_timedelta(line, last_line)
                    except Exception:
                        continue

                    guid = get_author_guid(current_segment)

                    if _tdelta > T_DELTA_30MIN:
                        __save_segment(guid)
                    elif last_guid is None:
                        if guid is not None or _tdelta < T_DELTA_5MIN:
                            last_segment.extend(current_segment)
                        else:
                            last_segment = current_segment
                        current_segment = []
                    elif guid == last_guid:
                        last_segment.extend(current_segment)
                        current_segment.clear()
                    elif guid is not None:
                        self.save_slice_cache_wrap(last_segment)
                        last_segment = current_segment
                        current_segment = []
                    else:
                        guid = last_guid
                        
                    last_guid = guid

                current_segment.append(line)
                last_timestamp = timestamp
                last_line = line
                
        guid = get_author_guid(current_segment)
        __save_segment(guid)

    def finish_slice(self, logs_id):
        logs_folder = os.path.join(LOGS_DIR, logs_id)
        logs_name = os.path.join(logs_folder, f"{LOGS_CUT_NAME}.zlib")
        if not self.forced and self.slices[logs_id].get('done') and slice_exists(logs_name):
            self.change_slice_status(logs_id, "Done!", slice_done=True)
            return

        if logs_id in logs_folder:
            shutil.rmtree(logs_folder, ignore_errors=True)
        logs_folder = new_folder_path(LOGS_DIR, logs_id)
        
        pc = perf_counter()
        
        slice_name = os.path.join(self.upload_dir, f"{logs_id}.txt")
        self.change_slice_status(logs_id, "Formatting slice...")
        logs = logs_fix.trim_logs(slice_name)
        logs = b'\n'.join(logs)
        self.change_slice_status(logs_id, "Saving slice...")
        logs = zlib.compress(logs, level=7)
        bytes_write(logs_name, logs)
        self.change_slice_status(logs_id, "Done!", slice_done=True)

        UPLOAD_LOGGER.debug(f'{logs_id} done in {get_ms(pc)} ms')

    def main(self):
        self.year = self.file_data["year"]
        self.mtime = os.path.getmtime(self.extracted_file)

        self.slice_logs()

        self.change_status(SAVING_SLICES)
        for logs_id in self.slices:
            self.finish_slice(logs_id)
        
        self.change_status(SEMI_DONE)
        for logs_id in self.slices:
            logs_archive.save_raw_logs(logs_id, self.upload_dir, self.forced)

        self.change_status(TOP_UPDATE)
        for logs_id in self.slices:
            logs_top.make_report_top(logs_id)
        logs_top_server.main_add_new_reports_wrap(self.slices)
        
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
        archive_path = self.upload_data["archive"]
        file_id = logs_archive.get_archive_id(archive_path)
        if file_id is None:
            self.change_status(ARCHIVE_ID_ERROR, 1)
            UPLOAD_LOGGER.error(f"{archive_path} {ARCHIVE_ID_ERROR}")
            return

        self.file_data = UPLOADED_FILES.get(file_id)
        if self.already_uploaded():
            UPLOAD_LOGGER.debug(f"{archive_path} already uploaded")
            return
        
        self.change_status("Extracting...")
        _archive_data = logs_archive.new_archive(archive_path, self.upload_dir)
        if not _archive_data:
            self.change_status(ARCHIVE_ERROR, 1)
            UPLOAD_LOGGER.error(f"{archive_path} {ARCHIVE_ERROR}")
            return
        
        data, extracted_file = _archive_data
        self.file_data = data
        return extracted_file

    def run(self):
        if self.upload_data is None:
            UPLOAD_LOGGER.error(f"{self.upload_dir} self.upload_data is None")
            return
        
        _extracted = self.upload_data["extracted"]
        if _extracted:
            self.file_data = extracted_id_local(_extracted)
        else:
            _extracted = self.extract_archive()
            if not _extracted:
                return
        if self.already_uploaded():
            return
            
        self.extracted_file = _extracted

        st0 = perf_counter()

        try:
            self.main()
        
        except Exception:
            UPLOAD_LOGGER.exception(f"NewUpload run {self.upload_dir}")
            self.change_status(LOGS_ERROR, 1)
        
        finally:
            UPLOAD_LOGGER.debug(f'Done in {get_ms(st0)} ms')
            self.finish()
            
    def finish(self):
        save_upload_cache(self.file_data, self.slices)
        if "uploads" not in self.upload_dir:
            return
        
        old = self.upload_data.get("archive") or self.upload_data.get("extracted")
        _, base1, base2 = self.upload_dir.rsplit('\\', 2)
        basename = os.path.basename(old)
        new = os.path.join(UPLOADED_DIR, f"{base1}--{base2}--{basename}")
        UPLOAD_LOGGER.debug(f'moving old {old}')
        UPLOAD_LOGGER.debug(f'moving new {new}')
        os.rename(old, new)
        shutil.rmtree(self.upload_dir, ignore_errors=True)


class File:
    def __init__(self, current_path) -> None:
        self.current_path = current_path
        self.filename: str = os.path.basename(current_path)
        self.name, self.ext = self.filename.rsplit('.', 1)
    
    def save(self, new_path):
        shutil.copyfile(self.current_path, new_path)


def new_upload_folder(ip='localhost'):
    new_upload_dir_ip = new_folder_path(UPLOADS_DIR, ip)
    timestamp = constants.get_now().strftime("%y-%m-%d--%H-%M-%S")
    new_upload_dir = new_folder_path(new_upload_dir_ip, timestamp)
    return new_upload_dir

def main(file: File, ip='localhost', server=None, forced=False):
    raw_filename = file.filename
    *words, ext = re.findall('([A-Za-z0-9]+)', raw_filename)
    file_name = f"{'_'.join(words)}.{ext}"

    new_upload_dir = new_upload_folder(ip)
    full_file_path = os.path.join(new_upload_dir, file_name)
    file.save(full_file_path)
    upload_data = {
        "upload_dir": new_upload_dir,
        "archive": full_file_path,
        "extracted": "",
        "server": server,
        "ip": ip,
    }
    return NewUpload(upload_data, forced=forced)

def extracted_id_local(logs_path):
    mtime = os.path.getmtime(logs_path)
    _time = int(mtime)
    size = os.path.getsize(logs_path)
    file_id = f"{_time}_{size}"

    data = UPLOADED_FILES.get(file_id)
    if not data:
        mod_time = constants.logs_edit_time(logs_path)
        year = datetime.fromtimestamp(_time).year
        data = {
            "file_id": file_id,
            "mod_time": mod_time,
            "year": year,
            "path": logs_path,
        }
    return data

def main_local_text(logs_path, forced=False):
    upload_data = {
        "upload_dir": new_upload_folder(),
        "archive": "",
        "extracted": logs_path,
        "server": None,
        "ip": "localhost"
    }
    return NewUpload(upload_data, forced=forced)


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
