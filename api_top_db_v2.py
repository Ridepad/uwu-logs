import json
import gzip
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypedDict

from c_path import Directories, PathExt, StrEnum
from h_debug import running_time, Loggers
from h_other import get_report_name_info


class Columns(StrEnum):
    PLAYER_RAID_ID = "player_raid_id"
    REPORT_ID = "report_id"
    TIMESTAMP = "timestamp"
    DURATION = "duration"
    GUID = "guid"
    NAME = "name"
    SPEC = "spec"
    USEFUL_DPS = "useful_dps"
    USEFUL_AMOUNT = "useful_amount"
    TOTAL_DPS = "total_dps"
    TOTAL_AMOUNT = "total_amount"
    AURAS = "auras"
    FORMATTED_STRING = "z"

HEADERS_TO_COLUMNS_NAMES = {
    "head-useful-dps": Columns.USEFUL_DPS,
    "head-useful-amount": Columns.USEFUL_AMOUNT,
    "head-total-dps": Columns.TOTAL_DPS,
    "head-total-amount": Columns.TOTAL_AMOUNT,
    "head-duration": Columns.DURATION,
    "head-date": Columns.PLAYER_RAID_ID,
    # "head-date": Columns.TIMESTAMP,
    # "head-name": Columns.NAME,
}

SORT_REVERSED = [
    Columns.NAME,
    Columns.DURATION,
]
SORT_GROUPPED = [
    Columns.USEFUL_DPS,
    Columns.USEFUL_AMOUNT,
    Columns.TOTAL_DPS,
    Columns.TOTAL_AMOUNT,
    Columns.NAME,
]

LIMITS = [10, 100, 1000, 10000, 50000]
LIMITS_JOINED = list(map(str, LIMITS))


class TopDataCompressed:
    def __init__(self, data: bytes) -> None:
        compressed = gzip.compress(data, 1)
        self.data = compressed
        self.size = len(data)
        self.size_compressed = len(compressed)


class TopDict(TypedDict):
    r: str
    t: int
    i: int
    n: str
    u: int
    d: int
    s: int
    a: list[int]


@dataclass
class DB_Index:
    __slots__ = "id", "table_name", "columns"
    id: str
    table_name: str
    columns: str

    @property
    def name(self):
        return self.index_name(self.table_name, self.id)

    @property
    def query(self):
        return f"""
        CREATE INDEX [{self.name}]
        ON [{self.table_name}] ({self.columns});
        """
    
    @staticmethod
    def index_name(table_name, idx_id):
        return f"idx.{table_name}.{idx_id}"


def get_player_id(data: TopDict):
    report_name = data['r']
    player_guid = data['i'][-7:]
    report_date = get_report_name_info(report_name)["date"]
    return f"{report_date}-{player_guid}"

def db_row_format_auras(auras):
    if not auras:
        return ""
    return "#" + "#".join((
        "/".join(map(str, x))
        for x in auras
    ))

def new_db_row(data: TopDict):
    _name_info = get_report_name_info(data["r"])
    date_str = f"{_name_info['date']}--{_name_info['time']}"
    data["r"] = f"{date_str}--{_name_info['author']}"
    _datetime = datetime.strptime(date_str, "%y-%m-%d--%H-%M")
    timestamp = int(_datetime.timestamp())
    duration = data["t"]
    if duration < 0 or duration > 9999:
        duration = 9999
    udps = round(data["u"] / duration, 2)
    tdps = round(data["d"] / duration, 2)
    player_raid_id = get_player_id(data)
    auras = db_row_format_auras(data["a"])
    json_string = json.dumps(list(data.values()), separators=(",", ":")).encode()
    return [
        player_raid_id,
        data["r"],
        timestamp,
        duration,
        data["i"],
        data["n"],
        data["s"],
        udps,
        data["u"],
        tdps,
        data["d"],
        auras,
        json_string,
    ]


class Cursors(dict[str, sqlite3.Connection]):
    def __missing__(self, path: PathExt):
        Loggers.top.debug(f">>> DB OPEN | {path}")
        v = self[path] = sqlite3.connect(path)
        return v

class DB:
    COLUMNS_ORDERED: list[str] = []
    COLUMNS_TABLE_CREATE: list[str] = []
    INDEX_SINGLE: list[str] = []
    INDEX_COMPOSITE: list[str] = []
    
    cursors = Cursors()

    def __init__(self, path: PathExt, new=False, without_row_id=False) -> None:
        if not new and not path.is_file():
            raise FileNotFoundError

        self.path = path
        self.without_row_id = without_row_id

        # top_points.Points.Lordaeron
        self.object_id = f"{self.__class__.__module__}.{self.__class__.__name__}.{path.stem}"
        
        self.COLUMNS_ORDERED_STR = ','.join(self.COLUMNS_ORDERED)
        self.COLUMNS_PARSE_STR = ",".join(["?"]*len(self.COLUMNS_ORDERED))
        self.COLUMNS_TABLE_CREATE_STR = ','.join(self.COLUMNS_TABLE_CREATE)

    @property
    def cursor(self):
        try:
            return self._cursor
        except AttributeError:
            self._cursor = self.cursors[self.path]
            return self._cursor
    
    @staticmethod
    def get_table_name(boss: str, mode: str):
        return f"{boss}.{mode}"

    def new_table(self, table_name: str, drop=False):
        if drop and table_name in self.tables_names():
            self.cursor.execute(f"DROP TABLE [{table_name}]")

        query = f"CREATE TABLE [{table_name}] ({self.COLUMNS_TABLE_CREATE_STR})"
        if self.without_row_id:
            query = f"{query} WITHOUT ROWID" 
        
        try:
            with self.cursor as c:
                c.execute(query)
            return True
        except sqlite3.OperationalError:
            return False
    
    @running_time
    def add_new_rows(self, table_name: str, rows):
        query = f"""
        REPLACE INTO [{table_name}]
        VALUES({self.COLUMNS_PARSE_STR})
        """
        with self.cursor as c:
            c.executemany(query, rows)


    def tables_info_list(self):
        query = "SELECT * FROM sqlite_schema WHERE type='table'"
        return self.cursor.execute(query).fetchall()

    def tables_names(self):
        return [
            row[1]
            for row in self.tables_info_list()
        ]

    def indexes_info_list(self, table_name: str):
        query = f"PRAGMA index_list([{table_name}])"
        return self.cursor.execute(query).fetchall()

    def indexes_names(self, table_name: str):
        return [
            row[1]
            for row in self.indexes_info_list(table_name)
        ]

    @running_time
    def add_indexes(self, table_name: str):
        _indexes: list[DB_Index] = []
        for idx_id in self.INDEX_SINGLE:
            _indexes.append(DB_Index(id=idx_id, table_name=table_name, columns=idx_id))
        
        for idx_tuple in self.INDEX_COMPOSITE:
            idx_id = "-".join(idx_tuple)
            _columns = ",".join(idx_tuple)
            _indexes.append(DB_Index(id=idx_id, table_name=table_name, columns=_columns))

        if not _indexes:
            return

        current_indexes = self.indexes_names(table_name)
        with self.cursor as c:
            for index in _indexes:
                if index.name in current_indexes:
                    c.execute(f"DROP INDEX [{index.name}]")
                self.cursor.execute(index.query)
        
        return None


def _dps(entry: TopDict):
    return round(entry["u"] / entry["t"], 2)

class TopDB(DB):
    COLUMNS_ORDERED = list(Columns.__members__.values())
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]
    INDEX_SINGLE = [
        Columns.USEFUL_DPS,
        Columns.TOTAL_DPS,
        Columns.USEFUL_AMOUNT,
        Columns.TOTAL_AMOUNT,
        Columns.GUID,
        Columns.DURATION,
        Columns.SPEC,
        # Columns.TIMESTAMP,
    ]
    INDEX_COMPOSITE = [
        (Columns.SPEC, Columns.USEFUL_DPS, Columns.GUID),
    ]

    def __init__(self, server: str, new=False, directory=Directories.top) -> None:
        db_path = directory / f"{server}.db"
        super().__init__(
            db_path,
            new=new,
            without_row_id=True,
        )
        self.server = server
        self.object_id = f"{self.__class__.__module__}.{self.__class__.__name__}.{server}"

    def add_new_entries_wrap(self, data: dict[str, list[TopDict]]):
        for table_name, data_list in data.items():
            combined_data = self.squash_top(data_list)
            
            try:
                to_insert = self._only_better(table_name, combined_data)
            except sqlite3.OperationalError:
                to_insert = combined_data.values()
            
            self._add_new_top_data(table_name, to_insert)

    @staticmethod
    def squash_top(new_data: list[TopDict]):
        top: dict[str, TopDict] = {}
        for new in new_data:
            player_id = get_player_id(new)
            cached = top.get(player_id)
            if not cached or _dps(new) > _dps(cached):
                top[player_id] = new
        return top

    @running_time
    def _add_new_top_data(self, table_name: str, data: list[TopDict]):
        if not data:
            return
        
        new_table_created = self.new_table(table_name)

        rows = map(new_db_row, data)
        self.add_new_rows(table_name, rows)

        if new_table_created:
            self.add_indexes(table_name)
    
    def _only_better(self, table_name: str, combined_data: dict[str, dict]):
        to_insert = []
        for _id, new_entry in combined_data.items():
            query = self.query_dps_player_raid_id(table_name, _id)
            row = self.cursor.execute(query).fetchone()
            if row is None or _dps(new_entry) > row[0]:
                to_insert.append(new_entry)
        return to_insert
    
    @staticmethod
    def query_dps_player_raid_id(table_name, player_raid_id):
        return f"""
        SELECT {Columns.USEFUL_DPS}
        FROM [{table_name}]
        WHERE {Columns.PLAYER_RAID_ID}='{player_raid_id}'
        """

class Cache(DB):
    access = defaultdict(datetime.now)
    m_time = defaultdict(float)
    cooldown = timedelta(seconds=15)

    def db_was_updated(self):
        if self.on_cooldown():
            # Loggers.top.debug(f"=== {self.object_id:40} | {mtime_cached:10} | {mtime_current:10} | Cooldown")
            return False
        
        mtime_current = int(self.path.mtime)
        mtime_cached = self.m_time[self.object_id]

        if mtime_current == mtime_cached:
            Loggers.top.debug(f"=== {self.object_id:40} | {mtime_cached:10} | {mtime_current:10} | Same")
            return False
        
        Loggers.top.debug(f"+++ {self.object_id:40} | {mtime_cached:10} | {mtime_current:10} | Updated")
        self.m_time[self.object_id] = mtime_current
        return True
    
    def on_cooldown(self):
        last_check = self.access[self.object_id]
        now = datetime.now()
        if last_check > now:
            return True
        
        self.access[self.object_id] = now + self.cooldown
        return False


class TopDBCached(TopDB, Cache):
    pass


class ConvertTop(TopDB):
    def change_db_to_without_row_id(self):
        tables = self.tables_names()
        tables_with_errors = []
        for table_name in tables:
            try:
                self.convert_table_to_without_row_id(table_name)
                self.add_indexes(table_name)
            except Exception:
                tables_with_errors.append(table_name)
    
        if not tables_with_errors:
            return
        
        for table_name in tables_with_errors:
            print(table_name)

    @running_time
    def convert_table_to_without_row_id(self, table_name):
        with self.cursor as c:
            print()
            print(table_name)
            queries = self._query_new_table_without_row_id(table_name)
            for current_query in queries:
                print(current_query)
                c.execute(current_query)
    
    def _query_new_table_without_row_id(self, table_name):
        TMP_TABLE = "temp_table_for_without_row_id"
        return [
        "PRAGMA foreign_keys = 0;",

        f"""CREATE TABLE {TMP_TABLE} AS
        SELECT *
        FROM [{table_name}];""",

        f"""DROP TABLE [{table_name}];""",

        f"""CREATE TABLE [{table_name}] ({self.COLUMNS_TABLE_CREATE_STR})
        WITHOUT ROWID;""",

        f"""INSERT INTO [{table_name}] ({self.COLUMNS_ORDERED_STR})
        SELECT {self.COLUMNS_ORDERED_STR}
        FROM {TMP_TABLE};""",

        f"""DROP TABLE {TMP_TABLE};""",

        "PRAGMA foreign_keys = 1;",
        ]


def convert_all_tops_to_v5():
    for x in Directories.top.iterdir():
        if not x.is_file():
            continue
        if x.suffix != ".db":
            continue
        server = x.stem
        print("="*100)
        print(server)
        ConvertTop(server).change_db_to_without_row_id()

def main():
    q = DB.get_table_name("Rotface", "25H")
    print(q)


if __name__ == "__main__":
    main()
