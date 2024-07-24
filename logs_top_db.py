import gzip
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import groupby, islice
from pathlib import Path
from typing import TypedDict
from bisect import bisect

import numpy

from h_debug import running_time
from h_other import get_report_name_info, sort_dict_by_value

from logs_top_statistics import convert_boss_data

PATH = Path(__file__).parent
TOP_DIR_PATH = PATH.joinpath("top")

PAGE_LIMIT = 1000
QUERY_LIMIT = 10000

LORDAERON = "Lordaeron"
ICECROWN = "Icecrown"

COLUMN_PLAYER_RAID_ID = "player_raid_id"
COLUMN_REPORT_ID = "report_id"
COLUMN_TIMESTAMP = "timestamp"
COLUMN_DURATION = "duration"
COLUMN_GUID = "guid"
COLUMN_NAME = "name"
COLUMN_SPEC = "spec"
COLUMN_USEFUL_DPS = "useful_dps"
COLUMN_USEFUL_AMOUNT = "useful_amount"
COLUMN_TOTAL_DPS = "total_dps"
COLUMN_TOTAL_AMOUNT = "total_amount"
COLUMN_AURAS = "auras"
COLUMN_FORMATTED_STRING = "z"
COLUMN_NAMES = {
    "head-useful-dps": COLUMN_USEFUL_DPS,
    "head-useful-amount": COLUMN_USEFUL_AMOUNT,
    "head-total-dps": COLUMN_TOTAL_DPS,
    "head-total-amount": COLUMN_TOTAL_AMOUNT,
    "head-duration": COLUMN_DURATION,
    "head-date": COLUMN_TIMESTAMP,
    # "head-name": COLUMN_NAME,
}

COLUMNS_ORDER = [
    f"{COLUMN_PLAYER_RAID_ID} PRIMARY KEY",
    COLUMN_REPORT_ID,
    COLUMN_TIMESTAMP,
    COLUMN_DURATION,
    COLUMN_GUID,
    COLUMN_NAME,
    COLUMN_SPEC,
    COLUMN_USEFUL_DPS,
    COLUMN_USEFUL_AMOUNT,
    COLUMN_TOTAL_DPS,
    COLUMN_TOTAL_AMOUNT,
    COLUMN_AURAS,
    COLUMN_FORMATTED_STRING,
]
COLUMNS_STR = ','.join(COLUMNS_ORDER)
COLUMNS_PARSE_STR = ",".join(["?"]*len(COLUMNS_ORDER))

SORT_REVERSED = [
    COLUMN_NAME,
    COLUMN_DURATION,
]
SORT_GROUPPED = [
    COLUMN_USEFUL_DPS,
    COLUMN_USEFUL_AMOUNT,
    COLUMN_TOTAL_DPS,
    COLUMN_TOTAL_AMOUNT,
    COLUMN_NAME,
]

BOSSES_ICC = [
    "Lord Marrowgar",
    "Lady Deathwhisper",
    "Deathbringer Saurfang",
    "Festergut",
    "Rotface",
    "Professor Putricide",
    "Blood Prince Council",
    "Blood-Queen Lana'thel",
    "Sindragosa",
    "The Lich King",
]

BOSSES_OTHER = [
    ("Toravon the Ice Watcher", "25N"),
    ("Halion", "25H"),
    ("Anub'arak", "25H"),
    ("Valithria Dreamwalker", "25H"),
]

DEFAULT_SPEC = [3, 1, 2, 2, 3, 3, 2, 1, 2, 2]

HEAL_SPEC = [7, 17, 21, 22, 31]
SPEC_DAMAGE = {1, 2, 3, 5, 6, 9, 10, 13, 14, 19, 23, 25, 26, 29, 30, 33, 34, 35, 37, 38}

DTYPES = [
    ('pr', int),
    ('dps', float),
    ('dur', float),
    ('report', str, 32),
]

def server_list():
    return sorted(
        file_name.stem
        for file_name in TOP_DIR_PATH.iterdir()
        if file_name.suffix == ".db"
    )

def new_db_connection(path: Path):
    return sqlite3.connect(path)

def get_top_db_path(server):
    return TOP_DIR_PATH.joinpath(f"{server}.db")

def new_db_connection_top(server: str, new=False):
    db_path = get_top_db_path(server)
    if not new and not db_path.is_file():
        return
    return new_db_connection(db_path)

def get_db_data(db: sqlite3.Cursor, query: str):
    if not db or not query:
        return None
    try:
        return db.execute(query)
    except sqlite3.OperationalError:
        pass
    return None

def query_top_db(server: str, query: str):
    db = new_db_connection_top(server)
    return get_db_data(db, query)

def query_stats(table_name):
    return f"""
    SELECT {COLUMN_USEFUL_DPS}, {COLUMN_SPEC}
    FROM [{table_name}]
    """
def query_points(table_name):
    return f"""
    SELECT {COLUMN_SPEC}, {COLUMN_USEFUL_DPS}, {COLUMN_GUID}, {COLUMN_REPORT_ID}, {COLUMN_DURATION}
    FROM [{table_name}]
    """
def query_player(table_name):
    return f"""
    SELECT {COLUMN_TIMESTAMP}, {COLUMN_NAME}, {COLUMN_GUID}, {COLUMN_SPEC}
    FROM [{table_name}]
    """
def query_dps_player_id(table_name, player_raid_id):
    return f"""
    SELECT {COLUMN_USEFUL_DPS}
    FROM [{table_name}]
    WHERE {COLUMN_PLAYER_RAID_ID}='{player_raid_id}'
    """
def query_top1_spec(table_name, spec):
    return f"""
    SELECT MAX({COLUMN_USEFUL_DPS})
    FROM [{table_name}]
    WHERE {COLUMN_SPEC}={spec}
    """
def query_dps_spec(table_name, spec):
    return f"""
    SELECT {COLUMN_USEFUL_DPS}
    FROM [{table_name}]
    WHERE {COLUMN_SPEC}={spec}
    """

def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return -1

def get_table_name(server: str, boss: str, mode: str):
    return f"{server}.{boss}.{mode}"

def get_table_name(boss: str, mode: str):
    return f"{boss}.{mode}"

def index_name(idx_id, table_name):
    return f"idx.{idx_id}.{table_name}"

def get_player_id(item: dict[str, str]):
    report_name = item['r']
    player_guid = item['i'][-7:]
    report_date = get_report_name_info(report_name)["date"]
    return f"{report_date}-{player_guid}"

def _dps(entry):
    return round(entry["u"] / entry["t"], 2)

def points_relative_calc(points, points_top1):
    return int(points / points_top1 * 10000)


class Cache:
    cache: defaultdict[str, dict]
    access: defaultdict[str, datetime]
    m_time: defaultdict[str, float]
    server: str

    cooldown = timedelta(seconds=15)

    def db_is_old(self):
        if self.on_cooldown():
            return True

        db_path = get_top_db_path(self.server)
        if not db_path.is_file():
            return False
        _mtime = int(db_path.stat().st_mtime)

        db_mtime = self.m_time[self.server]
        if not db_mtime:
            self.m_time[self.server] = _mtime
            return True

        if _mtime == db_mtime:
            return True
        
        self.m_time[self.server] = _mtime
        self.cache.pop(self.server, None)
        return False
    
    def on_cooldown(self):
        last_check = self.access[self.server]
        now = datetime.now()
        if last_check > now:
            return True
        
        self.access[self.server] = now + self.cooldown
        return False

    @property
    def cursor(self):
        try:
            return self.__cursor
        except AttributeError:
            pass
        self.__cursor = new_db_connection_top(self.server)
        return self.__cursor


def format_rank(spec_data, dps):
    total_raids = len(spec_data)
    if not total_raids or not spec_data[-1]:
        return {
            "rank": 1,
            "percentile": 100.0,
            "from_top1": 100.0,
            "total_raids": 1,
        }
    
    dps = dps + 0.01
    rank_reversed = bisect(spec_data, dps)
    rank = total_raids - rank_reversed + 1
    percentile = rank_reversed / total_raids * 100
    percentile = round(percentile, 2)
    perc_from_top1 = dps / spec_data[-1] * 100
    perc_from_top1 = round(perc_from_top1, 1)
    return {
        "rank": rank,
        "percentile": percentile,
        "from_top1": perc_from_top1,
        "total_raids": total_raids,
    }

class RaidRank(Cache):
    cache: defaultdict[str, dict] = defaultdict(dict)
    access: defaultdict[str, datetime] = defaultdict(datetime.now)
    m_time: defaultdict[str, float] = defaultdict(float)
    cooldown = timedelta(minutes=15)

    def __init__(self, server, boss, mode) -> None:
        self.server = server.replace(" ", "-")
        self.table_name = get_table_name(boss, mode)

    def _get_data(self):
        _cache = self.cache[self.server]
        if self.table_name in _cache and self.db_is_old():
            return _cache[self.table_name]
                
        _cache[self.table_name] = {}
        return _cache[self.table_name]

    def _get_spec_data(self, spec_index: int) -> list[float]:
        if not self.cursor:
            return []
        q = query_dps_spec(self.table_name, spec_index)
        return sorted(x for x, in self.cursor.execute(q))
    
    def get_spec_data(self, spec_index: int) -> list[float]:
        _data = self._get_data()
        if spec_index in _data:
            return _data[spec_index]
        try:
            _data[spec_index] = self._get_spec_data(spec_index)
        except sqlite3.OperationalError:
            _data[spec_index] = []
        return _data[spec_index]

    def format_rank_wrap(self, spec, dps):
        return format_rank(self.get_spec_data(spec), dps)

    @running_time
    def get_rank_wrap(self, players_dps: dict[str, float], players_spec: dict[str, int]):
        return {
            guid: self.format_rank_wrap(players_spec[guid], dps)
            for guid, dps in players_dps.items()
            if guid in players_spec
        }

@running_time
def gzip_compress(data: bytes):
    return gzip.compress(data, 1)

@running_time
def list_to_json(data: list):
    if not data:
        return b'[]'

    data[0] = b"[" + data[0]
    data[-1] = data[-1] + b"]"
    return b','.join(data)

@running_time
def db_q_to_list(cursor: sqlite3.Cursor, limit: bool=True):
    try:
        first = cursor.fetchone()
    except (AttributeError, StopIteration):
        return []
    
    if not first:
        return []

    limit = PAGE_LIMIT if limit else QUERY_LIMIT
    limit -= 1

    if len(first) == 1:
        data = [v for v, in islice(cursor, limit)]
        data.insert(0, first[0])
        return data
    
    first_dps, first_guid = first
    s = {
        first_guid: first_dps,
    }
    for z, guid in cursor:
        if len(s) > limit:
            break
        if guid in s:
            continue
        s[guid] = z
    
    return list(s.values())

def spec_db_query(class_i, spec_i):
    class_i = to_int(class_i)
    spec_i = to_int(spec_i)
    if class_i == -1:
        spec_q = ""
    elif class_i is None:
        spec_q = "WHERE spec=23"
    elif spec_i is None or spec_i == -1:
        spec_q = f"WHERE spec between {class_i*4} and {class_i*4+3}"
    else:
        spec_q = f"WHERE spec={class_i*4+spec_i}"
    return spec_q

def build_query_string(table_name, spec_q, sort_by_q, best_only=True):
    order = "ASC" if sort_by_q in SORT_REVERSED else "DESC"
    if best_only and sort_by_q in SORT_GROUPPED:
        select_q = f"{COLUMN_FORMATTED_STRING}, guid"
    else:
        select_q = COLUMN_FORMATTED_STRING

    return f'''
    SELECT {select_q}
    FROM [{table_name}]
    {spec_q}
    ORDER BY {sort_by_q} {order}
    '''

def query_from_kwargs(**kwargs):
    boss = kwargs.get("boss")
    mode = kwargs.get("mode")
    table_name = get_table_name(boss, mode)

    class_i = kwargs.get("class_i")
    spec_i = kwargs.get("spec_i")
    spec_q = spec_db_query(class_i, spec_i)
    
    sort_by_q = COLUMN_NAMES.get(kwargs.get("sort_by"), COLUMN_USEFUL_DPS)
    best_only = kwargs.get("best_only")
    
    return build_query_string(
        table_name,
        spec_q,
        sort_by_q,
        best_only=best_only,
    )


class TopReturn(TypedDict):
    data: bytes
    length: int
    length_compressed: int

class Top(Cache):
    cache: defaultdict[str, dict] = defaultdict(dict)
    access: defaultdict[str, datetime] = defaultdict(datetime.now)
    m_time: defaultdict[str, float] = defaultdict(float)

    def __init__(self, **kwargs) -> None:
        self.server = kwargs.get("server", "")
        self.server = self.server.replace(" ", "-")
        self.limit = bool(kwargs.get("limit"))
        self.query = query_from_kwargs(**kwargs)
        self.class_ = _to_int(kwargs.get("class_i"))
        
        _spec = _to_int(kwargs.get("spec_i"))
        if _spec not in range(1,4):
            _spec = DEFAULT_SPEC[self.class_]
        self.spec = self.class_ * 4 + _spec

    def _compress(self, data: bytes):
        compressed = gzip_compress(data)
        return {
            "data": compressed,
            "length": len(data),
            "length_compressed": len(compressed),
            "limit": self.limit,
        }

    def get_data(self) -> TopReturn:
        _server = self.cache[self.server]
        if self.query in _server:
            same_limit = (not _server[self.query]["limit"]) or self.limit
            if same_limit and self.db_is_old():
                return _server[self.query]


        db_data = query_top_db(self.server, self.query)
        data = db_q_to_list(db_data, self.limit)
        data = list_to_json(data)
        data = self._compress(data)
        _server[self.query] = data
        return data

    @running_time
    def parse_top_points(self):
        _server = self.cache[self.server]
        if self.spec in _server:
            if self.db_is_old():
                return _server[self.spec]
        
        guids = PlayerData(self.server).get_guids()
        player_points = PlayerPoints(self.server, None, self.spec).get_combined_boss_data()
        points_top1 = player_points[next(iter(player_points))]
        a = [
            [
                points_relative_calc(points, points_top1),
                int(points),
                guids.get(guid, guid),
            ]
            for guid, points in player_points.items()
        ]
        j = json.dumps(a, separators=(",", ":"))
        d = self._compress(j.encode())
        _server[self.spec] = d
        return d


def convert_dps_spec(b_dps: dict, n_raids: int):
    if not b_dps:
        return {}

    b_dps_n = numpy.fromiter(b_dps.values(), dtype=DTYPES)

    dps_r1 = max(b_dps_n['dps'])
    if dps_r1 == 0:
        return {}
    
    n_players = min(10000, len(b_dps))
    n_raids = min(10000, n_raids)
    
    pos_players_t = numpy.arange(n_players)

    p_dps = b_dps_n['dps'] * 10000 / dps_r1
    p_raids = 10000 - b_dps_n['pr'] * 10000 / n_raids
    p_players = 10000 - pos_players_t * 10000 / n_players

    p_max = numpy.row_stack((p_players, p_dps, p_raids)).max(axis=0)

    pos_players_t += 1
    pos_r = b_dps_n['pr'] + 1

    z = zip(
        b_dps,
        b_dps_n['dps'],
        p_max,
        p_dps,
        p_raids,
        p_players,
        # map(int, pos_r),
        # map(int, pos_players_t),
        pos_r,
        pos_players_t,
        b_dps_n['dur'],
        b_dps_n['report'],
    )


    d: dict[str, dict] = {}
    for guid, dps, _p_max, _p_dps, _p_raid, _p_player, _r_raids, _r_player, dur, report in z:
        d[guid] = {
            "dps_max": dps,
            "points": _p_max,
            "points_dps": _p_dps,
            "points_rank_raids": _p_raid,
            "points_rank_players": _p_player,
            "rank_raids": _r_raids,
            "rank_players": _r_player,
            "dur_min": dur,
            "report": report,
        }

    # 30% faster but no keys
    # d = {}
    # for guid, v in zip(b_dps, z):
    #     d[guid] = v

    return d

# @running_time
def convert_dps(q: list):
    if not q:
        return {}
    
    q = sorted(q, reverse=1)

    converted_dps: dict[str, dict[str, dict]] = {}
    for spec_g, w in groupby(q, lambda x: x[0]):
        # if spec_g not in SPEC_DAMAGE:
        #     continue
        
        i = 0
        _best = {}
        raids = defaultdict(int)
        for i, (_, _udps, _guid, _report, _dur) in enumerate(w):
            raids[_guid] += 1
            if _guid in _best:
                continue
            _best[_guid] = (
                i,
                _udps,
                _dur,
                _report,
            )
        z = convert_dps_spec(_best, i+1)
        for guid, _d in z.items():
            _d["raids"] = raids[guid]
        r1 = next(iter(_best.values()))[1]
        z["total"] = {
            "n_raids": i+1,
            "n_players": len(_best),
            "dps_r1": r1,
        }

        converted_dps[spec_g] = z   

    return converted_dps

def convert_dps_wrap(db, boss: str, mode: str="25H"):
    table_name = get_table_name(boss, mode)
    query = query_points(table_name)
    rows = get_db_data(db, query)
    if rows is None:
        return
    rows = rows.fetchall()
    return convert_dps(rows)


class PlayerData(Cache):
    cache: defaultdict[str, dict] = defaultdict(dict)
    access: defaultdict[str, datetime] = defaultdict(datetime.now)
    m_time: defaultdict[str, float] = defaultdict(float)
    cooldown = timedelta(minutes=15)
    
    def __init__(self, server: str) -> None:
        self.server = server.replace(" ", "-")

    def get_guid_class(self, name):
        return self._get_data().get("names", {}).get(name)

    def _get_data(self):
        if self.server in self.cache:
            if self.db_is_old():
                return self.cache[self.server]
                
        self.cache[self.server] = self.renew_player_data()
        return self.cache[self.server]
    
    @running_time
    def get_guids(self):
        return self._get_data().get("guids", {})

    @running_time
    def renew_player_data(self):
        table_name = get_table_name("Deathbringer Saurfang", "25H")
        query = query_player(table_name)
        try:
            data = self.cursor.execute(query)
        except Exception:
            return {
                "names": {},
                "guids": {},
            }

        data = sorted(data, key=lambda x: x[0])
        
        d: dict[str, dict] = {}
        g: dict[str, str] = {}
        for  _, name, guid, spec in data:
            g[guid] = name
            d[name] = {
                "guid": guid,
                "class": spec // 4,
            }
        return {
            "names": d,
            "guids": g,
        }

class PlayerPoints(Cache):
    cache: defaultdict[str, dict] = defaultdict(dict)
    access: defaultdict[str, datetime] = defaultdict(datetime.now)
    m_time: defaultdict[str, float] = defaultdict(float)
    cooldown = timedelta(minutes=5)

    def __init__(self, server: str, guid: str, spec: int) -> None:
        self.server = server.replace(" ", "-")
        self.guid = guid
        self.spec = spec

    # @running_time
    def _get_boss_data(self, boss: str, mode: str="25H") -> dict[str, dict[str, dict]]:
        _server = self.cache[self.server]

        table_name = get_table_name(boss, mode)
        if table_name in _server:
            return _server[table_name]
        
        _server[table_name] = convert_dps_wrap(self.cursor, boss, mode)
        return _server[table_name]

    def get_boss_data(self, boss: str, mode: str="25H"):
        return self._get_boss_data(boss, mode).get(self.spec, {})
    
    def get_boss_data_with_total(self, boss, mode="25H"):
        data = self.get_boss_data(boss, mode)
        d = data.get(self.guid, {})
        if d:
            d |= data["total"]
        return d
    
    def get_boss_data_all(self):
        boss_data = {}
        for boss in BOSSES_ICC:
            boss_data[boss] = self.get_boss_data_with_total(boss)
        for boss, mode in BOSSES_OTHER:
            boss_data[boss] = self.get_boss_data_with_total(boss, mode)
        return boss_data

    def _get_combined_boss_data(self):
        z = defaultdict(int)
        for boss in BOSSES_ICC:
            spec_data = self.get_boss_data(boss)
            for _guid, v in spec_data.items():
                try:
                    z[_guid] += v["points"]
                except KeyError:
                    pass
        return sort_dict_by_value(z)

    # @running_time
    def get_combined_boss_data(self) -> dict[str, float]:
        _server = self.cache[self.server]
        if self.spec in _server:
            return _server[self.spec]
        _server[self.spec] = self._get_combined_boss_data()
        return _server[self.spec]

    def _get_player_data(self):
        all_points = self.get_combined_boss_data()
        if self.guid not in all_points:
            return {}
        
        guids = list(all_points)
        points_top1 = all_points[guids[0]]
        rank = guids.index(self.guid) + 1
        points_relative = points_relative_calc(all_points[self.guid], points_top1)
        return {
            "overall_rank": rank,
            "overall_points": points_relative,
            "bosses": self.get_boss_data_all(),
        }

    def get_player_data(self):
        if self.server in self.cache:
            self.db_is_old()
        
        return self._get_player_data()


@running_time
def parse_player(server, name, spec=None):
    player_data = PlayerData(server).get_guid_class(name)
    if not player_data:
        return

    _class = player_data["class"]
    if spec is None:
        spec = DEFAULT_SPEC[_class]
    spec_i = _class*4 + spec

    guid = player_data["guid"]
    rd = {
        "name": name,
        "class": _class,
        "server": server,
    } | PlayerPoints(server, guid, spec_i).get_player_data()

    return json.dumps(rd, default=int)


class PveStats(Cache):
    cache = defaultdict(dict)
    access: defaultdict[str, datetime] = defaultdict(datetime.now)
    m_time: defaultdict[str, float] = defaultdict(float)
    cooldown = timedelta(hours=1)

    def __init__(self, server: str) -> None:
        self.server = server.replace(" ", "-")

    def get_data(self, boss, mode):
        _stats = self.cache[self.server]
        
        table_name = get_table_name(boss, mode)
        if table_name in _stats:
            if self.db_is_old():
                return _stats[table_name]
        
        _stats[table_name] = self.parse_stats(table_name)
        return _stats[table_name]

    def parse_stats(self, table_name):
        query = query_stats(table_name)
        cursor = query_top_db(self.server, query)
        if not cursor:
            return '{}'

        data = defaultdict(list)
        for v, spec in cursor:
            data[spec].append(v)
        data = convert_boss_data(data)

        return json.dumps(data)


def db_row_format_auras(auras):
    if not auras:
        return ""
    return "#" + "#".join(["/".join(map(str, x)) for x in auras])

def new_db_row(data: dict):
    _name_info = get_report_name_info(data["r"])
    date_str = f"{_name_info['date']}--{_name_info['time']}"
    data["r"] = f"{date_str}--{_name_info['author']}"
    _datetime = datetime.strptime(date_str, "%y-%m-%d--%H-%M")
    timestamp = int(_datetime.timestamp())
    if data["t"] < 0 or data["t"] > 9999:
        data["t"] = 9999
    udps = round(data["u"] / data["t"], 2)
    tdps = round(data["d"] / data["t"], 2)
    player_raid_id = get_player_id(data)
    auras = db_row_format_auras(data["a"])
    z = json.dumps(list(data.values()), separators=(",", ":")).encode()
    return [
        player_raid_id,
        data["r"],
        timestamp,
        data["t"],
        data["i"],
        data["n"],
        data["s"],
        udps,
        data["u"],
        tdps,
        data["d"],
        auras,
        z,
    ]

@running_time
def db_top_create_table(db: sqlite3.Connection, table_name, drop=False):
    try:
        if drop:
            db.execute(f"DROP TABLE [{table_name}]")
    except sqlite3.OperationalError:
        pass
    db.execute(f"CREATE TABLE IF NOT EXISTS [{table_name}] ({COLUMNS_STR})")

@running_time
def db_top_add_new_rows(db: sqlite3.Connection, table_name: str, rows):
    db.executemany(f"REPLACE INTO [{table_name}] VALUES({COLUMNS_PARSE_STR})", rows)

def drop_index(db: sqlite3.Connection, idx_name):
    try:
        db.execute(f"DROP INDEX [{idx_name}]")
    except sqlite3.OperationalError:
        pass

# @running_time
def create_index(db: sqlite3.Connection, idx_name: str, table_name, columns: str):
    db.execute(f"""
    CREATE INDEX [{idx_name}]
    ON [{table_name}] ({columns});
    """)

@running_time
def db_top_add_indexes(db, table_name):
    for idx_id in [
        COLUMN_USEFUL_DPS,
        COLUMN_TOTAL_DPS,
        COLUMN_USEFUL_AMOUNT,
        COLUMN_TOTAL_AMOUNT,
        COLUMN_GUID,
        COLUMN_DURATION,
        COLUMN_SPEC,
        COLUMN_TIMESTAMP,
    ]:
        idx_name = index_name(idx_id, table_name)
        drop_index(db, idx_name)
        create_index(db, idx_name, table_name, idx_id)
    
    for idx_tuple in (
        (COLUMN_SPEC, COLUMN_USEFUL_DPS, COLUMN_GUID),
    ):
        idx_id = "_".join(idx_tuple)
        idx_name = index_name(idx_id, table_name)
        _columns = ",".join(idx_tuple)
        create_index(db, idx_name, table_name, _columns)
        
    return None


@running_time
def add_new_entries(db: sqlite3.Connection, table_name: str, data: list[dict]):
    if not data:
        return
    
    try:
        db.execute(f"CREATE TABLE [{table_name}] ({COLUMNS_STR})")
        new_table = True
    except sqlite3.OperationalError:
        new_table = False

    db_top_add_new_rows(db, table_name, map(new_db_row, data))

    if new_table:
        db_top_add_indexes(db, table_name)

    return None

def squash_top(new_data: list[dict]):
    top = {}
    for new in new_data:
        player_id = get_player_id(new)
        cached = top.get(player_id)
        if not cached or _dps(new) > _dps(cached):
            top[player_id] = new
    return top

def only_better(db: sqlite3.Connection, table_name: str, combined_data: dict[str, dict]):
    to_insert = []
    for _id, new_entry in combined_data.items():
        q = query_dps_player_id(table_name, _id)
        current = db.execute(q).fetchone()
        if current is None or _dps(new_entry) > current[0]:
            to_insert.append(new_entry)
    return to_insert

def add_new_entries_wrap(server, data: dict[str, list]):
    with new_db_connection_top(server, new=True) as db:
        for table_name, data_list in data.items():
            combined_data = squash_top(data_list)
            
            try:
                to_insert = only_better(db, table_name, combined_data)
            except sqlite3.OperationalError:
                to_insert = combined_data.values()
            
            add_new_entries(db, table_name, to_insert)


@running_time
def read_gzip_top(boss_path: Path):
    return boss_path.read_bytes()

@running_time
def load_gzip_top(b: bytes):
    return json.loads(gzip.decompress(b))

def convert_gzip_to_db_rows(boss_path: Path):
    _bytes = read_gzip_top(boss_path)
    _json = load_gzip_top(_bytes)
    return map(new_db_row, _json)

@running_time
def convert_gzip_to_db_table(server, boss, mode):
    print(boss)
    table_name = get_table_name(boss, mode)

    boss_path = TOP_DIR_PATH.joinpath(server, f"{boss} {mode}.gzip")
    rows = convert_gzip_to_db_rows(boss_path)

    with new_db_connection_top(server, new=True) as db:
        db_top_create_table(db, table_name, True)
        db_top_add_new_rows(db, table_name, rows)
        db_top_add_indexes(db, table_name)

def convert_old_top():
    for server_folder in TOP_DIR_PATH.iterdir():
        if not server_folder.is_dir():
            continue
        server = server_folder.stem
        print()
        print(server)
        for boss_file in server_folder.iterdir():
            if boss_file.suffix != ".gzip":
                continue
            boss, mode = boss_file.stem.rsplit(" ", 1)
            print(boss_file)
            convert_gzip_to_db_table(server, boss, mode)


def __test_add_new_entries(server, boss, mode):
    boss_path = TOP_DIR_PATH.joinpath(server, f"{boss} {mode}.gzip")
    j = read_gzip_top(boss_path)
    j = load_gzip_top(j)
    j = {get_player_id(i):i for i in j}
    
    with new_db_connection_top(server, new=True) as db:
        table_name = get_table_name(boss, mode)
        add_new_entries(db, table_name, j)

def __test_add_new_entries_wrap():
    for server_folder in TOP_DIR_PATH.iterdir():
        if not server_folder.is_dir():
            continue
        server = server_folder.stem
        print()
        print(server)
        if server not in [LORDAERON,]:
            continue
        for boss_file in server_folder.iterdir():
            if boss_file.suffix != ".gzip":
                continue
            boss, mode = boss_file.stem.rsplit(" ", 1)
            print(boss_file)
            __test_add_new_entries(server, boss, mode)
        

def __test_auras():
    server = LORDAERON
    mode = "25H"
    boss = "Rotface"
    table_name = get_table_name(server, boss, mode)
    query = f"""
    SELECT *
    FROM [{table_name}]
    WHERE spec=23 AND auras LIKE '%2825/%'
    """
    for x in query_top_db(server, query):
        print(x)
    
    return None


def __test_delete():
    _healers = ",".join(map(str, HEAL_SPEC))
    server = LORDAERON
    mode = "25H"
    boss = "Valithria Dreamwalker"
    table_name = get_table_name(server, boss, mode)
    q = f"""DELETE FROM [{table_name}] WHERE {COLUMN_SPEC} NOT IN ({_healers})"""
    with new_db_connection_top(server) as db:
        db.execute(q)


def main():
    # convert_old_top()
    pd = PlayerData("Icecrown")
    q = pd.renew_player_data()
    for x, y in q["guids"].items():
        print(x, y)
    # __test_add_new_entries_wrap()
    # p = PointsBySpec(LORDAERON, None, None)
    # print(p.cursor)
    # p = PointsBySpec(ICECROWN, None, None)
    # print(p.cursor)
    # server = LORDAERON
    # d = get_boss_data(server)
    # pkl_w(server, d)
    # pkl_r(server)
    # pickle.dump()
    # server = LORDAERON
    # boss_data = get_boss_data(server)
    # boss_data = get_boss_data(server)
    # boss_data = get_boss_data(server)
    # j = jsondump(boss_data)
    # j = jsondump(boss_data)
    # print(len(j))
    # TOP_PATH.joinpath(f"{server}.json").write_text(j)
    # _, guid = find_class_guid(new_db_connection(), "Apakalipsis", S_ICECROWN, "25H")
    # _, guid = find_class_guid(new_db_connection(), "Safiyah", S_LORDAERON, "25H")
    # print(guid)
    #     db.execute("ALTER TABLE [Lordaeron.Toravon the Ice Watcher.25H] RENAME TO [Lordaeron.Toravon the Ice Watcher.25N]")
    # with new_db_connection() as db:
    # __tst3()
    # z = query_from_kwargs(**{"server":LORDAERON,"boss":"The Lich King","mode":"25H","best_only":1,"class_i":"5","spec_i":"3"})
    # z = query_top_db(z)
    # z = db_q_to_list(z, 1000)
    # print(parse_player())
    # print(parse_player("Aarre", LORDAERON, "25H"))
    # print(parse_player("Safiyah", LORDAERON, "25H"))
    # print(parse_player("Meownya", LORDAERON, "25H"))
    # print(parse_player("Nomadra", LORDAERON, "25H", 1))
    # print(parse_player("Nomadra", LORDAERON, "25H", 2))
    # print(parse_player("Nomadra", LORDAERON, "25H", 3))
    # _a = parse_request(boss= "asdas")
    # print(_a)
    # test_auras()
    # make_db()
    # parse_request(boss="Rotface", server=LORDAERON, mode="25H")

if __name__ == "__main__":
    main()
