from collections import defaultdict

from c_path import Directories, FileNames
from h_debug import running_time, setup_logger
from h_other import get_report_name_info
from h_datetime import (
    MONTHS,
    get_now,
    to_dt_year_precise,
)

TYPES = (str, bool, type(None))

def cache_wrap(func: 'function'):
    def cache_inner(self: Logs, s, f, *args, **kwargs):
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE[func.__name__]
        for arg in args:
            if not isinstance(arg, TYPES):
                break
            cached_data = cached_data[arg]
            
        if slice_ID in cached_data:
            return cached_data[slice_ID]
        
        data = func(self, s, f, *args, **kwargs)
        cached_data[slice_ID] = data
        return data

    return cache_inner


class Logs:
    def __init__(self, logs_name: str, copy_from_backup: bool=True) -> None:
        self.NAME = logs_name
        self.copy_from_backup = copy_from_backup

        self.year = int(logs_name[:2]) + 2000

        self.last_access = get_now()

        self.CACHE = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    @property
    def FORMATTED_NAME(self):
        try:
            return self.__FORMATTED_NAME
        except AttributeError:
            pass

        report_name_info = get_report_name_info(self.NAME)
        time = report_name_info['time'].replace('-', ':')
        year, month, day = report_name_info['date'].split("-")
        month = MONTHS[int(month)-1][:3]
        date = f"{day} {month} {year}"
        author = report_name_info['author']
        self.__FORMATTED_NAME = f"{date}, {time} - {author}"
        return self.__FORMATTED_NAME
        
    @property
    def LOGS(self):
        try:
            return self.__LOGS
        except AttributeError:
            self.__LOGS = self._open_logs()
            return self.__LOGS

    @property
    def LOGGER(self):
        try:
            return self.__LOGGER
        except AttributeError:
            log_file = self.relative_path('log.log')
            self.__LOGGER = setup_logger(f"{self.NAME}_logger", log_file)
            return self.__LOGGER

    @property
    def path(self):
        try:
            return self.__path
        except AttributeError:
            pass
        
        report_dir = Directories.logs / self.NAME
        if not report_dir.is_dir():
            report_dir = report_dir.backup_path()
            if not report_dir.is_dir():
                raise FileNotFoundError
        
        self.__path = report_dir
        return self.__path

    def relative_path(self, s: str):
        return self.path / s

    def get_timedelta(self, last, now):
        return to_dt_year_precise(now, self.year) - to_dt_year_precise(last, self.year)
    
    def get_timedelta_seconds(self, last, now):
        return self.get_timedelta(last, now).total_seconds()

    @staticmethod
    def duration_to_string(t: float):
        milliseconds = t % 1 * 1000
        if milliseconds < 1:
            milliseconds = milliseconds * 1000
        
        t = int(t)
        hours = t // 3600
        minutes = t // 60 % 60
        seconds = t % 60
        return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0>3.0f}"

    # @cache_wrap
    def get_slice_duration(self, s: int=None, f: int=None):
        if s is None:
            s = 0
        if f is None:
            f = 0
        first_line = self.LOGS[s]
        last_line = self.LOGS[f-1]
        return self.get_timedelta_seconds(first_line, last_line)

    def get_fight_duration_total(self, segments):
        return sum(self.get_slice_duration(s, f) for s, f in segments)

    @running_time
    def _open_logs(self):
        if self.copy_from_backup and self.path.parent != Directories.logs:
            print(">>>>>>>>>> COPYING FROM BACKUP")
            report_dir = Directories.logs / self.NAME
            report_dir.copy_from_backup()
            self.__path = report_dir
        
        return self.relative_path(FileNames.logs_cut).zstd_read().splitlines()
