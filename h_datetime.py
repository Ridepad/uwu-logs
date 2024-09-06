import re
from datetime import datetime, timedelta

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

T_DELTA = {
    "2SEC": timedelta(seconds=2),
    "15SEC": timedelta(seconds=15),
    "30SEC": timedelta(seconds=30),
    "1MIN": timedelta(minutes=1),
    "2MIN": timedelta(minutes=2),
    "3MIN": timedelta(minutes=3),
    "5MIN": timedelta(minutes=5),
    "10MIN": timedelta(minutes=10),
    "15MIN": timedelta(minutes=15),
    "20MIN": timedelta(minutes=20),
    "30MIN": timedelta(minutes=30),
    "14H": timedelta(hours=14),
}

def get_now():
    return datetime.now()

CURRENT_YEAR = get_now().year
RE_FIND_ALL = re.compile("(\d+)").findall
RE_TIMESTAMP = re.compile("(\d{1,2}).(\d{1,2}).(\d{2}).(\d{2}).(\d{2}).(\d{3})").findall
RE_FIND_ALL_BYTES = re.compile(b'(\d+)').findall

def to_dt_closure(year=None):
    re_find_all = re.compile('(\d+)').findall
    CURRENT = get_now()
    CURRENT_SHIFT = CURRENT + T_DELTA["14H"]

    if year is None:
        year = CURRENT.year
        def inner(s: str):
            q = list(map(int, re_find_all(s[:18])))
            q[-1] *= 1000
            dt = datetime(year, *q)
            if dt > CURRENT_SHIFT:
                dt = dt.replace(year=year-1)
            return dt
    else:
        def inner(s: str):
            q = list(map(int, re_find_all(s[:18])))
            q[-1] *= 1000
            return datetime(year, *q)
        
    return inner

class ToDatetime:
    def __init__(self, year=None) -> None:
        self.now = get_now()
        if year is None:
            year = self.now.year
        self.year = year
        self.re_findall = RE_FIND_ALL

    @property
    def datetime_shifted(self):
        try:
            self.__datetime_shifted
        except AttributeError:
            self.__datetime_shifted = self.now + T_DELTA["14H"]
            return self.__datetime_shifted

def to_dt_simple(s: str):
    return datetime(CURRENT_YEAR, *map(int, RE_FIND_ALL(s[:18])))

def to_dt_simple_precise(s: str):
    q = list(map(int, RE_FIND_ALL(s[:18])))
    q[-1] *= 1000
    return datetime(CURRENT_YEAR, *q)

def get_delta(current, previous):
    return to_dt_simple(current) - to_dt_simple(previous)

def get_delta_simple_precise(current, previous):
    return to_dt_simple_precise(current) - to_dt_simple_precise(previous)

def to_dt_year(s: str, year: int):
    return datetime(year, *map(int, RE_FIND_ALL(s[:18])))

def to_dt_year_precise(s: str, year: int):
    q = list(map(int, RE_TIMESTAMP(s)[0]))
    q[-1] *= 1000
    return datetime(year, *q)

def to_dt_simple_bytes(s: bytes):
    return datetime(CURRENT_YEAR, *map(int, RE_FIND_ALL_BYTES(s[:18])))

def to_dt_year_bytes(s: bytes, year: int):
    return datetime(year, *map(int, RE_FIND_ALL_BYTES(s[:18])))

def to_dt_bytes_closure(year: int=None):
    if year is None:
        year = get_now().year

    def inner(s: str):
        return datetime(year, *map(int, RE_FIND_ALL_BYTES(s[:18])))
        
    return inner

def to_dt_bytes_year_fix(s, year: int=None):
    if year is None:
        year = get_now().year
    
    dt = datetime(year, *map(int, RE_FIND_ALL_BYTES(s[:18])))
    CURRENT_SHIFTED = get_now() + T_DELTA["14H"]
    if dt > CURRENT_SHIFTED:
        dt = dt.replace(year=year-1)
    return dt

def duration_to_string(t: float):
    milliseconds = t % 1 * 1000
    if milliseconds < 1:
        milliseconds = milliseconds * 1000
    
    t = int(t)
    hours = t // 3600
    minutes = t // 60 % 60
    seconds = t % 60
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0>3.0f}"
