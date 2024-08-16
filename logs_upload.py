import json
import re
import subprocess
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from os import utime
from shutil import disk_usage
from time import perf_counter, sleep

import api_7z
import h_server_fix
import logs_fix

from constants import (
    DEFAULT_SERVER_NAME,
    LOGS_CUT_NAME,
    SERVERS,
)
from c_bosses import convert_to_fight_name
from c_path import Directories, PathExt
from h_debug import Loggers, get_ms_str, running_time
from h_datetime import to_dt_bytes_closure

LOGGER_UPLOADS = Loggers.uploads

BIG_GAP = timedelta(hours=14)
SMALL_GAP = timedelta(minutes=3)
BUGGED_NAMES = {"nil", "Unknown"}
DATE_FORMAT = "%y-%m-%d--%H-%M-%S"
NIL_GUID = b"0x0000000000000000"
NPCS = {b"0xF13", b"0xF15"}

ARCHIVE_ID_ERROR = "Bad archive.  Don't change extension manually, create archives from 0."
ARCHIVE_ERROR = "Error extracting logs file.  Try to rename logs file and create archive again."
UPLOAD_GONE = "Uploaded file disappeared. Try to upload again."
LOGS_ERROR = "Error parsing logs."
LOGS_ERROR_NO_SPACE = "Error parsing logs.  No disk space left on the server.  Try again in 1 hour."
LOGS_ERROR_NO_TXT = "Error parsing logs.  No .txt files found in archive."
TOP_ERROR = "Done!  Select 1 of the reports below.  Top update encountered an error."
ALREADY_DONE = "File has been uploaded already!  Select 1 of the reports below."
ALREADY_DONE_NONE_FOUND = "File has been uploaded already!  No boss segments were found!  Don't forget to use /combatlog"
FULL_DONE = "Done!  Select 1 of the reports below."
FULL_DONE_PARTIAL = "Done!  Select 1 of the reports below.  Some of the raids were already uploaded.  Delete logs file to keep it fresh!"
FULL_DONE_NONE_FOUND = "Done!  No boss segments were found!  Don't forget to use /combatlog"
START_SLICING = "Determinating log slices..."
SAVING_SLICES = "Saving log slices..."
SEMI_DONE = "Finishing caching..."


def raw_exists(raid_id):
    pending = Directories.pending_archive / f"{raid_id}.txt"
    if pending.is_file():
        return True
    
    archive_path = Directories.archives / f"{raid_id}.7z"
    archive = api_7z.SevenZipArchive(archive_path)
    if archive.archive_id:
        return True
    
    backup_archive_path = archive_path.backup_path()
    backup_archive = api_7z.SevenZipArchive(backup_archive_path)
    if backup_archive.archive_id:
        return True
    
    return False

def slice_exists(p: PathExt):
    return p.is_file() and p.stat().st_size > 2048
    
def is_fully_processed(raid_id: str):
    logs_name = Directories.logs / raid_id / LOGS_CUT_NAME
    _slice_exists = slice_exists(logs_name)
    if not _slice_exists:
        logs_name_backup = logs_name.backup_path()
        _slice_exists = slice_exists(logs_name_backup)
    return _slice_exists and raw_exists(raid_id)


def nuke_folder_contents(directory: PathExt, suffix: str=None):
    for file in directory.files:
        if suffix and file.suffix != suffix:
            continue
        file.unlink()
    
def nuke_folder(directory: PathExt, suffix: str=None):
    nuke_folder_contents(directory, suffix)
    directory.rmdir()

def remove_prev_raid_upload(raid_id: str):
    pending = Directories.pending_archive / f"{raid_id}.txt"
    archive_path = Directories.archives / f"{raid_id}.7z"
    archive_path_backup = archive_path.backup_path()
    for file in {
        pending,
        archive_path,
        archive_path_backup,
    }:
        try:
            file.unlink()
            print(">>> Removed file:", file)
        except:
            pass

    raid_dir = Directories.logs / raid_id
    raid_dir_backup = raid_dir.backup_path()
    for dir in {
        raid_dir,
        raid_dir_backup,
    }:
        try:
            nuke_folder(dir)
            print(">>> Removed directory:", dir)
        except:
            pass


@dataclass
class LogsSliceInfo:
    players: set[str] = field(default_factory=lambda: set())
    bosses: list[str] = field(default_factory=lambda: [])
    duration: float = 0.0
    id: str = None
    status: str = "In progress"
    done: int = 0

    def to_dict(self):
        d = self.__dict__
        d["players"] = sorted(d["players"])
        return d

class LogsSlice(list[bytes]):
    def __init__(self, server: str=None, year: int=None) -> None:
        self.to_dt = to_dt_bytes_closure(year)
        self.server = server if server else "Unknown"
        self.__last_line = None
        self.__slice_info = LogsSliceInfo()

    def __str__(self) -> str:
        duration = self.info.duration
        if self:
            dt_ts = datetime.fromtimestamp(duration, timezone.utc)
            durstr = datetime.strftime(dt_ts, "%H:%M:%S")
        else:
            durstr = "Too short"
        bosses = self.info.bosses
        players = self.info.players
        return '\n'.join((
            '/// LogsSlice:',
            f"> {len(self):>12,} | {durstr:>8} | {self.id}",
            f">  BOSSES: {len(bosses):>3} | {sorted(bosses)[:5]}",
            f"> PLAYERS: {len(players):>3} | {sorted(players)[:10]}",
        ))

    @property
    def duration(self):
        try:
            return (self.to_dt(self[-1]) - self.to_dt(self[0])).total_seconds()
        except (IndexError, TypeError, ValueError):
            return 0.0

    @property
    def id(self):
        return self.info.id

    @property
    def info(self):
        if not self:
            if self.__last_line:
                self.__last_line = None
                self.__slice_info = LogsSliceInfo()
            return self.__slice_info
        if self[-1] == self.__last_line:
            return self.__slice_info

        self._set_slice_info()
        return self.__slice_info

    def get_last_line_dt(self):
        if not self:
            return None
        _dt = self.to_dt(self[-1])
        _dt = self._fix_dt(_dt)
        return _dt
    
    def is_fully_processed(self):
        return is_fully_processed(self.id)

    def trim_invalid_lines(self, reverse=False):
        index = -1 if reverse else 0
        for _ in range(5):
            line = self[index]
            try:
                return self.to_dt(line)
            except (TypeError, ValueError):
                self.pop(index)
        
    def trim_invalid_lines_wrap(self):
        self.trim_invalid_lines()
        self.trim_invalid_lines(reverse=True)

    def _set_slice_info(self):
        units = self._get_units()
        
        bosses = self._filter_fights(units["all_units"])
        _players = self._filter_players(units["all_units"])
        _names_gen = (units["player_names"][guid] for guid in _players)
        players = set(map(self._format_name, _names_gen))
        
        self.__last_line = self[-1]
        self.__slice_info = LogsSliceInfo(
            players=players,
            bosses=bosses,
            duration=self.duration,
            id=self._raid_id(),
        )
    
    @staticmethod
    def _fix_dt(dt: datetime):
        if dt > dt.now() + BIG_GAP:
            dt = dt.replace(year=dt.year-1)
        return dt
    
    def _get_logs_author_info(self):
        for line in self:
            if b"SPELL_CAST_FAILED" not in line:
                continue
            if line.count(b'  ') > 1:
                continue
            line = line.decode()
            guid, name = line.split(',', 3)[1:3]
            name = name.replace('"', '')
            if name not in BUGGED_NAMES:
                return guid, name
        
        for line in self[:1_000]:
            if b"0x0" not in line:
                continue
            if b"nil" in line:
                continue
            line = line.decode()
            guid = line.split(',', 2)[1]
            return guid, "Unknown"
        
        return "", "Unknown"

    def _get_units(self):
        entities: defaultdict[bytes, int] = defaultdict(int)
        names = {}

        _skip = len(self) // 5000 + 1
        # might be a problem
        _skip = max(_skip, 10)
        for line in self[::_skip]:
            try:
                guid, name = line.split(b',', 6)[4:6]
            except ValueError:
                continue
            
            entities[guid] += 1
            if guid not in names:
                names[guid] = name
            
        return {
            "player_names": names,
            "all_units": entities,
        }

    @staticmethod
    def _format_name(name: bytes):
        return name.decode().replace('"', '')

    def _filter_fights(self, units: dict[bytes, int]):
        bosses: list[str] = []

        for guid, c in units.items():
            if c < 10:
                continue
            if guid[:5] not in NPCS:
                continue
            _fight_name = convert_to_fight_name(guid[6:-6].decode())
            if _fight_name and _fight_name not in bosses:
                bosses.append(_fight_name)

        return bosses

    def _filter_players(self, units: dict[bytes, int]):
        players: set[bytes] = set()

        for guid, c in units.items():
            if c < 10:
                continue
            if guid[:3] == b"0x0" and guid != NIL_GUID:
                players.add(guid)
        return players
    
    def _raid_id(self):
        self.trim_invalid_lines_wrap()
        _dt = self.to_dt(self[0])
        _dt = self._fix_dt(_dt)
        date = _dt.strftime("%y-%m-%d--%H-%M")

        guid, name = self._get_logs_author_info()
        server = SERVERS.get(guid[:4], self.server)
        return f'{date}--{name}--{server}'


class CacheLineInt(dict[bytes, int]):
    def __missing__(self, key: bytes):
        value = self[key] = int(key.replace(b':', b''))
        return value

class LogsSeparator:
    def __init__(self, server: str=None, timestamp: float=None) -> None:
        self.year = datetime.fromtimestamp(timestamp).year
        self.to_dt = to_dt_bytes_closure(self.year)
        self.server = server if server else "Unknown"

        self.slice_cache: dict[str, dict] = {}

        self.cache_int = CacheLineInt()
        self.current_segment = self._new_slice()
        self.last_segment = self._new_slice()

    def _new_slice(self):
        return LogsSlice(self.server, self.year)

    def get_timedelta(self, now, before):
        return self.to_dt(now) - self.to_dt(before)
    
    def is_big_gap(self):
        if not self.last_segment:
            return True
        
        segments_tdelta = self.get_timedelta(self.current_segment[0], self.last_segment[-1])
        LOGGER_UPLOADS.debug(f'is_big_gap {segments_tdelta}')
        return segments_tdelta > BIG_GAP

    def is_different_raid(self):
        players_last = self.last_segment.info.players
        players_current = self.current_segment.info.players
        max_len = max(len(players_last), len(players_current))
        overlap = len(players_last & players_current)
        if len(self.current_segment) < 1000:
            min_overlap = max_len // 5
        else:
            min_overlap = max_len // 2
        LOGGER_UPLOADS.debug(f'/// is_different_raid | {min_overlap:>2} {overlap:>2} | {min_overlap > overlap}')
        return min_overlap > overlap

    def new_segment(self):
        segment = None
        if self.is_different_raid() or self.is_big_gap():
            segment = self.last_segment
            self.last_segment = self.current_segment
        else:
            self.last_segment.extend(self.current_segment)
        self.current_segment = self._new_slice()
        return segment

    def generate_segments(self, lines: list[bytes]):
        NULL_BYTE = b'\x00'
        for line in lines:
            try:
                if line[-1] == NULL_BYTE:
                    continue
                i = line.index(b'.')
                timestamp = self.cache_int[line[i-8:i]]
            except (IndexError, ValueError):
                continue

            # prevents if check every loop iteration
            try:
                _delta = timestamp - last_timestamp
            except UnboundLocalError:
                _delta = 0
            

            if _delta > 100 or _delta < 0:
                try:
                    _dt_now = self.to_dt(line)
                except (TypeError, ValueError):
                    continue
                
                try:
                    _dt_last = self.to_dt(last_line)
                except (TypeError, ValueError):
                    _dt_last = self.current_segment.trim_invalid_lines(reverse=True)
                
                if abs(_dt_now - _dt_last) > SMALL_GAP:
                    yield self.new_segment()

            self.current_segment.append(line)
            last_timestamp = timestamp
            last_line = line

        yield self.new_segment()
        yield self.last_segment


def get_now_timestamp():
    return datetime.now().strftime(DATE_FORMAT)

def new_upload_folder(ip: str="localhost", timestamp: str=None):
    if not ip or not isinstance(ip, str):
        ip = "localhost"
    if not timestamp:
        timestamp = get_now_timestamp()
    
    return Directories.uploads.new_child(ip).new_child(timestamp)

class UploadData:
    def __init__(
        self,
        ip: str=None,
        server: str=None,
        timezone: str=None,
    ) -> None:
        self.ip = ip or "0.0.0.0"
        self.server = h_server_fix.server_cnv(server)
        self.timezone = timezone

        self.timestamp = get_now_timestamp()
        self.directory = new_upload_folder(ip, self.timestamp)

class LogsArchiveStatus(api_7z.SevenZipArchiveInfo):
    def __init__(
        self,
        archive_path: PathExt,
        upload_data: UploadData=None,
    ) -> None:
        super().__init__(archive_path)
        self.upload_data = upload_data or UploadData()

        self.slices: dict[str, LogsSliceInfo] = {}
        self.done = 0
        self.status = 'Starting...'
        self.changed = False

    def slices_to_dict(self):
        return {
            k: v.to_dict()
            for k, v in self.slices.items()
        }

    @property
    def slices_dict(self):
        try:
            if self.changed:
                self.changed = False
                self.__slices_json = self.slices_to_dict()
            return self.__slices_json
        except AttributeError:
            self.__slices_json = self.prev_info.get("slices", {})
            return self.__slices_json

    @property
    def status_dict(self):
        return {
            'done': self.done,
            'status': self.status,
            "slices": self.slices_dict,
        }

    @property
    def server(self):
        try:
            return self.__server
        except AttributeError:
            self.__server = self._get_server()
            return self.__server
    
    @property
    def prev_info(self):
        try:
            return self.__prev_info
        except AttributeError:
            self.__prev_info = self._get_prev_info()
            return self.__prev_info

    @property
    def timezone(self):
        _timezone = self.upload_data.timezone
        if not _timezone:
            _timezone = self.prev_info.get("timezone")
        if not _timezone:
            _timezone = "UTC"
        return _timezone

    def change_main_status(self, msg, all_done=0):
        self.status = msg
        self.done = int(all_done)
    
    def change_slice_status(
        self,
        status_message: str,
        raid_id: str,
        pc: float=None,
        slice_done: bool=False,
    ):
        slice = self.slices[raid_id]
        slice.status = status_message
        slice.done = int(slice_done)
        self.add_logger_msg(status_message, raid_id, pc=pc)
        self.changed = True
    
    def add_logger_msg(
        self,
        msg: str,
        raid_id: str=None,
        pc: float=None,
        is_error: bool=False,
    ):
        if pc is None:
            pc = perf_counter()
        if raid_id:
            msg = f"{msg:20} | {raid_id}"
        msg = f"{get_ms_str(pc)} | {self.upload_data.ip:>15} | {msg}"
        
        if is_error:
            LOGGER_UPLOADS.error(msg)
        else:
            LOGGER_UPLOADS.debug(msg)
    
    def _get_server(self):
        server = self.upload_data.server
        if not server or server in SERVERS.values():
            server = DEFAULT_SERVER_NAME
        
        # print("/// NEW SERVER1:", server)
        old_server = self.prev_info.get("server")
        # print("/// OLD SERVER1:", old_server)
        if old_server and old_server != DEFAULT_SERVER_NAME:
            server = old_server
        # print("/// NEW SERVER2:", server)
        return server

    def _get_prev_info_file(self, archive_id: str):
        year, day, _ = archive_id.split('-', 2)
        sub_dir = f"{year}-{day}"
        archive_id_short = archive_id.rsplit('--', 1)[0]
        possible_files = [
            Directories.info_uploads / archive_id,
            Directories.info_uploads / sub_dir / archive_id,
            Directories.info_uploads / archive_id_short,
            Directories.info_uploads / sub_dir / archive_id_short,
        ]
        for p in possible_files:
            p = p.with_suffix(".json")
            if p.is_file():
                self.add_logger_msg(f"Previous upload data path: {p}")
                return p
        return None

    def _get_prev_info(self):
        archive_id = self.archive_id
        if not archive_id:
            return {}
        p = self._get_prev_info_file(archive_id)
        if not p:
            return {}
        j: dict = json.loads(p.read_text())
        return j
    

class LogsArchiveParser(LogsArchiveStatus):
    def __init__(
        self,
        archive_path: PathExt,
        upload_data: UploadData=None,
        forced=False,
        only_slices=False,
        keep_temp_folder=False,
    ) -> None:
        super().__init__(archive_path, upload_data)

        self.forced = forced
        self.only_slices = only_slices
        self.keep_temp_folder = keep_temp_folder
        self.keep_temp_folder = True

        self.has_duplicates = False
        self.has_error = False
        self.finished = False
        self.mod_time_delta = None
        
        self._7z_pipe: subprocess.Popen = None
    
    def pipe_gen(self, file_line: api_7z.SevenZipLine):
        file_name = file_line.file_name
        if "*" in file_name:
            file_name = f'"{file_name}"'
        cmd_list = [self.path, 'e', self.archive_path, "-so", "--", file_name]
        self._7z_pipe = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
        stdout = self._7z_pipe.stdout
        line = stdout.readline(5000)
        while line:
            yield line
            line = stdout.readline(5000)
    
    def adjust_mod_time(self, file_line: api_7z.SevenZipLine, segment: LogsSlice):
        _mod_time_delta = file_line.datetime - segment.get_last_line_dt()
        if not self.mod_time_delta or self.mod_time_delta > _mod_time_delta:
            self.mod_time_delta = _mod_time_delta
            LOGGER_UPLOADS.debug(f">>> NEW MOD TIME | {_mod_time_delta}")

    def parse_txt_files(self):
        full_pc = perf_counter()
        all_text_files = self.get_all_files_with_suffix(".txt")
        if not all_text_files:
            raise FileNotFoundError("No text file present in archive")

        self.current_segment_pc = perf_counter()
        for file_line in all_text_files:
            # print(file_line)
            lines = self.pipe_gen(file_line)
            separator = LogsSeparator(server=self.server, timestamp=file_line.timestamp)
            for segment in separator.generate_segments(lines):
                if not segment:
                    continue
                
                self.save_segment(segment, file_line.timestamp)
                self.adjust_mod_time(file_line, segment)
                self.current_segment_pc = perf_counter()

        self.add_logger_msg("Done slicing", pc=full_pc)

    def save_raw_txt(self, logs_slice: LogsSlice, timestamp: float):
        raid_id = logs_slice.id
        self.change_slice_status("Saving", raid_id)

        pc = perf_counter()
        
        temp_slice_path = self.upload_data.directory / f"{raid_id}.txt"
        with open(temp_slice_path, 'wb') as file:
            file.writelines(logs_slice)
        
        utime(temp_slice_path, (timestamp, timestamp))
        
        self.change_slice_status("Saved raw", raid_id, pc=pc)

    def save_zstd(self, logs_slice: LogsSlice):
        raid_id = logs_slice.id
        self.change_slice_status("Formatting", raid_id)
        
        pc = perf_counter()
        
        slice_folder = Directories.logs.new_child(raid_id)
        slice_path = slice_folder / LOGS_CUT_NAME

        temp_slice_path = self.upload_data.directory / f"{raid_id}.txt"
        
        data = b'\n'.join(logs_fix.normalize_read_from_file(temp_slice_path))
        slice_path.zstd_write(data)

        self.change_slice_status("Saved zstd", raid_id, pc=pc)

    def save_segment(self, logs_slice: LogsSlice, timestamp: float):
        # print(logs_slice)

        if not logs_slice or not logs_slice.info.bosses:
            return
        
        raid_id = logs_slice.id
        self.slices[raid_id] = logs_slice.info
        self.change_slice_status("Sliced", raid_id, pc=self.current_segment_pc)

        if not self.forced and logs_slice.is_fully_processed():
            self.has_duplicates = True
            self.change_slice_status("Exists", raid_id, slice_done=True)
            return
    
        try:
            self.save_raw_txt(logs_slice, timestamp)
            self.save_zstd(logs_slice)
            self.change_slice_status("Done", raid_id, slice_done=True)
        except Exception:
            LOGGER_UPLOADS.exception(f"save_segment {raid_id}")
            self.change_slice_status("Error", raid_id)
            raise


class LogsArchive(LogsArchiveParser):
    @property
    def thread(self):
        try:
            return self.__thread
        except AttributeError:
            self.__thread = threading.Thread(target=self.main)
            return self.__thread
    
    def start_processing(self):
        self.thread.start()

    def main(self):
        try:
            self.proccess_archive()
        except FileNotFoundError:
            LOGGER_UPLOADS.exception("main FileNotFoundError")
            self.finish(LOGS_ERROR_NO_TXT, is_error=True)
        except OSError:
            self.finish(LOGS_ERROR_NO_SPACE, is_error=True)
        except Exception:
            LOGGER_UPLOADS.exception("main other exception")
        finally:
            if not self.finished:
                self.finish(LOGS_ERROR, is_error=True)
    
    def proccess_archive(self):
        self.pc_main = perf_counter()
        if self.is_fully_proccessed():
            return

        if self.uncompressed_size > disk_usage(__file__).free:
            raise OSError("Not enough disk space")

        self.change_main_status(START_SLICING)

        self.parse_txt_files()
        
        if self.has_duplicates:
            self.finish(FULL_DONE_PARTIAL)
        elif not self.slices:
            self.finish(FULL_DONE_NONE_FOUND)
        else:
            self.finish(FULL_DONE)

    def finish(self, msg: str, is_error=False):
        self.finished = True
        self.has_error = is_error
        
        self.change_main_status(msg, int(not is_error))
        self.add_logger_msg(msg, pc=self.pc_main, is_error=is_error)
        
        self.write_file_info()
        self.remove_prev_uploaded()
        self.move_sliced_logs()
        self.move_uploaded_archive_wrap()
        self.remove_temp_upload_folder()

    def release_archive_file(self):
        _archive_is_still_open = (
            isinstance(self._7z_pipe, subprocess.Popen)
            and self._7z_pipe.returncode != 0
        )
        if not _archive_is_still_open:
            return
        
        self._7z_pipe.kill()
        LOGGER_UPLOADS.debug(f"kill {self._7z_pipe}")
        self._7z_pipe.wait()
        LOGGER_UPLOADS.debug(f"wait {self._7z_pipe}")
        
    def move_uploaded_archive_wrap(self):
        self.release_archive_file()
        
        # wait for unlock on error
        for i in range(1, 11):
            try:
                self.move_uploaded_archive()
                break
            except FileNotFoundError:
                LOGGER_UPLOADS.warning("> MOVED 7z already")
                break
            except (PermissionError, OSError):
                LOGGER_UPLOADS.exception(f"! ATTEMPT {i} | ERROR MOVING 7z oserror")
                sleep(0.25)
            except Exception:
                LOGGER_UPLOADS.exception("! ERROR MOVING 7z other")
                break

    def _move_raid_slice(self, raid_id):
        pc = perf_counter()
        raw_path_current = self.upload_data.directory / f"{raid_id}.txt"
        if not raw_path_current.is_file():
            print(">>> not raw_path_current.is_file", raid_id)
            return
        
        if not self.forced and raw_exists(raid_id):
            print(">>> not self.forced and raw_exists(raid_id)", raid_id)
            self.add_logger_msg("Raw exists", raid_id, pc=pc)
            return
        
        raw_path_new = Directories.pending_archive / f"{raid_id}.txt"
        if raw_path_new.is_file():
            raw_path_new.unlink()
        raw_path_current.rename(raw_path_new)
        self.add_logger_msg("Raw moved", raid_id, pc=pc)
        
        raw_path_tz = Directories.pending_archive / f"{raid_id}.timezone"
        raw_path_tz.write_text(self.timezone)
        self.add_logger_msg("Timezone", raid_id, pc=pc)

    def move_sliced_logs(self):
        if self.has_error:
            nuke_folder_contents(self.upload_data.directory, suffix=".txt")
            return
        
        for raid_id in self.slices:
            self._move_raid_slice(raid_id)

    def move_uploaded_archive(self):
        if self.archive_path.parent != self.upload_data.directory:
            return
        
        if self.has_error:
            _dir = Directories.todo
        else:
            _dir = Directories.uploaded
        ip = self.upload_data.ip
        timestamp = self.upload_data.timestamp
        name = self.archive_path.name
        _file_id = f"{ip}--{timestamp}--{name}"
        new_archive_name = _dir / _file_id
        self.archive_path.rename(new_archive_name)

    def remove_temp_upload_folder(self):
        if self.keep_temp_folder:
            return
        try:
            nuke_folder_contents(self.upload_data.directory)
            self.upload_data.directory.rmdir()
            self.upload_data.directory.parent.rmdir()
        except Exception:
            pass
    
    def _add_to_prev_list(self, key: str, value: str):
        _list = self.prev_info.get(key) or []
        _list.append(str(value))
        return _list

    def make_file_info(self):
        _mod_time = self.prev_info.get("mod_time") or self.mod_time_delta
        _ips = self._add_to_prev_list("ips", self.upload_data.ip)
        _timestamps = self._add_to_prev_list("timestamps", self.upload_data.timestamp)
        _archives = self._add_to_prev_list("archives", self.archive_path)
        file_info = {
            "ip": self.prev_info.get("ip", self.upload_data.ip),
            "timezone": self.timezone,
            "server": self.server,
            "mod_time": str(_mod_time),
            "ips": _ips,
            "timestamps": _timestamps,
            "archives": _archives,
            "slices": self.slices_dict,
        }
        return json.dumps(file_info, indent=2)

    def write_file_info(self):
        _year_day = self.date_str.rsplit('-', 1)[0]
        _dir = Directories.info_uploads.new_child(_year_day)
        new_file_info_file = _dir / f"{self.archive_id}.json"
        
        file_info = self.make_file_info()
        new_file_info_file.write_text(file_info)

    def is_new_server(self):
        if self.server == DEFAULT_SERVER_NAME:
            return False
        
        old_server = self.prev_info.get("server")
        if not old_server or old_server != DEFAULT_SERVER_NAME:
            return False
        
        return self.server != old_server

    def remove_prev_uploaded(self):
        if not self.is_new_server():
            return
        
        prev_server = self.prev_info.get("server")
        for raid_id in self.slices:
            raid_id = raid_id.replace(self.server, prev_server)
            remove_prev_raid_upload(raid_id)

    @running_time
    def is_fully_proccessed(self):
        if self.forced or not self.prev_info:
            LOGGER_UPLOADS.debug(f"/ is_fully_proccessed self.forced or not self.prev_info")
            return False
        
        if self.is_new_server():
            LOGGER_UPLOADS.debug(f"/ is_fully_proccessed self.new_server")
            return False

        if not self.prev_info.get("slices"):
            self.finish(ALREADY_DONE_NONE_FOUND)
            LOGGER_UPLOADS.debug(f"/ is_fully_proccessed not self.prev_info.get('slices')")
            return True
        
        for raid_id in self.prev_info["slices"]:
            if not is_fully_processed(raid_id):
                LOGGER_UPLOADS.debug(f"/ is_fully_proccessed not is_fully_processed {raid_id}")
                return False
        
        self.finish(ALREADY_DONE)
        return True

@dataclass
class UploadChunk:
    data: bytes
    chunk_id: int
    upload_id: int

class NewUpload:
    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.upload_id = 0
        self.chunks: dict[int, bytes] = {}
    
    def add_chunk(self, chunk: UploadChunk):
        if self.upload_id != chunk.upload_id:
            self.chunks.clear()
            self.upload_id = chunk.upload_id

        if not chunk.data:
            return

        self.chunks[chunk.chunk_id] = chunk.data
        return True

    def save_uploaded_file(self, file_data: dict[str, str]):
        chunks_amount_from_client = self._file_data_chunks(file_data)
        amount_chunks_uploaded = len(self.chunks)
        LOGGER_UPLOADS.debug(f"CHUNKS | {chunks_amount_from_client:>4} | {amount_chunks_uploaded:>4}")
        
        if chunks_amount_from_client and chunks_amount_from_client != amount_chunks_uploaded:
            raise ValueError("chunks missing")

        upload_data = UploadData(
            ip=self.ip,
            server=file_data.get("server"),
            timezone=file_data.get("timezone"),
        )
        filename = self._format_filename(file_data.get("filename"))
        archive_save_path = upload_data.directory / filename
        
        sorted_chunks = [
            self.chunks[chunk]
            for chunk in sorted(self.chunks, key=int)
        ]

        try:
            with open(archive_save_path, 'wb') as f:
                for chunk in sorted_chunks:
                    f.write(chunk)
        finally:
            self.chunks.clear()
     
        return LogsArchive(archive_save_path, upload_data=upload_data)

    def _correct_chunks(self, file_data):
        chunks_amount_from_client = self._file_data_chunks(file_data)
        amount_chunks_uploaded = len(self.chunks)
        last_chunk = max(self.chunks, key=int)
        same_chunks = amount_chunks_uploaded == last_chunk
        if chunks_amount_from_client:
            same_chunks = same_chunks == chunks_amount_from_client
        
        debug = " | ".join((
            f"{chunks_amount_from_client:>4}",
            f"{amount_chunks_uploaded:>4}",
            f"{last_chunk:>4}",
        ))
        LOGGER_UPLOADS.debug(f"CHUNKS | {debug}")
        
        return same_chunks
    
    @staticmethod
    def _file_data_chunks(j: dict[str, str]):
        try:
            return int(j.get("chunks"))
        except (TypeError, ValueError):
            return 0
    
    @staticmethod
    def _format_filename(file_name):
        if not file_name:
            return "archive.7z"

        *words, ext = re.findall('([A-Za-z0-9]+)', file_name)
        return f"{'_'.join(words)}.{ext}"
