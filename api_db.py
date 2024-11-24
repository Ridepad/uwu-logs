import gzip
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from c_path import PathExt
from h_debug import Loggers, running_time


LIMITS = [10, 100, 1000, 10000, 50000]
LIMITS_JOINED = list(map(str, LIMITS))
LOGGER = Loggers.top


class DataCompressed:
    __slots__ = "data", "size", "size_compressed"
    def __init__(self, data: bytes) -> None:
        self.data = gzip.compress(data, 1)
        self.size = len(data)
        self.size_compressed = len(self.data)


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
    def query_create(self):
        return "\n".join((
            f"CREATE INDEX [{self.name}]",
            f" ON [{self.table_name}] ({self.columns})",
        ))
    
    @property
    def query_drop(self):
        return f"DROP INDEX [{self.name}]"
    
    @staticmethod
    def index_name(table_name, idx_id):
        return f"idx.{table_name}.{idx_id}"


class Cursors(dict[str, sqlite3.Connection]):
    def __missing__(self, path: PathExt):
        LOGGER.debug(f">>> DB OPEN | {path}")
        v = self[path] = sqlite3.connect(path)
        return v


class Table:
    COLUMNS_ORDERED: list[str] = []
    COLUMNS_TABLE_CREATE: list[str] = []
    INDEX_SINGLE: list[str] = []
    INDEX_COMPOSITE: list[str] = []
    without_row_id = False

    def __init__(
        self,
        name: str,
    ):
        self.name = name
        self.COLUMNS_ORDERED_STR = ','.join(self.COLUMNS_ORDERED)
        self.COLUMNS_PARSE_STR = ",".join(["?"]*len(self.COLUMNS_ORDERED))
        self.COLUMNS_TABLE_CREATE_STR = ','.join(self.COLUMNS_TABLE_CREATE)

    def query_create(self):
        return "\n".join((
            f"CREATE TABLE [{self.name}]",
            f"({self.COLUMNS_TABLE_CREATE_STR})",
            "WITHOUT ROWID" if self.without_row_id else "",
        ))
    
    def query_replace_rows(self):
        return "\n".join((
            f"REPLACE INTO [{self.name}]",
            f"VALUES({self.COLUMNS_PARSE_STR})",
        ))

    def query_rename(self, new_name: str):
        return f"ALTER TABLE [{self.name}] RENAME TO [{new_name}]"

    def gen_indexes(self):
        for idx_id in self.INDEX_SINGLE:
            yield DB_Index(id=idx_id, table_name=self.name, columns=idx_id)
        
        for idx_tuple in self.INDEX_COMPOSITE:
            idx_id = "-".join(idx_tuple)
            _columns = ",".join(idx_tuple)
            yield DB_Index(id=idx_id, table_name=self.name, columns=_columns)


class TableMetadata(Table):
    without_row_id = True
    COLUMNS_ORDERED = [
        "key",
        "value",
    ]
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]
    def __init__(self):
        super().__init__("_metadata")
    

class DB:
    cursors = Cursors()

    def __init__(self, path: PathExt, new=False, without_row_id=False) -> None:
        if not new and not path.is_file():
            raise FileNotFoundError

        self.path = path
        self.without_row_id = without_row_id
        
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

    def rename_table(self, table: Table, new_name: str):
        q = table.query_rename(new_name)
        with self.cursor as c:
            c.execute(q)

    def new_table(self, table: Table, drop=False):
        if table.name in self.tables_names():
            if drop:
                self.cursor.execute(f"DROP TABLE [{table.name}]")
            else:
                return False

        query = table.query_create()
        try:
            with self.cursor as c:
                c.execute(query)
            return True
        except sqlite3.OperationalError:
            return False
    
    def _add_rows(self, table: Table, rows: list):
        if not rows:
            return

        query = table.query_replace_rows()
        with self.cursor as c:
            c.executemany(query, rows)
    
    def add_new_rows(self, table: Table, rows: list[str]):
        try:
            self._add_rows(table, rows)
        except sqlite3.OperationalError: # no such table
            new_table_created = self.new_table(table)

            self._add_rows(table, rows)

            if new_table_created:
                self.add_indexes(table)

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
    def add_indexes(self, table: Table):
        _indexes = table.gen_indexes()

        current_indexes = self.indexes_names(table.name)
        with self.cursor as c:
            for index in _indexes:
                if index.name in current_indexes:
                    c.execute(index.query_drop)
                c.execute(index.query_create)
        
        return None
    
    def change_metadata(self, **kwargs):
        print(kwargs)
        table = TableMetadata()
        rows = list(kwargs.items())
        self.add_new_rows(table, rows)



class Cache(DB):
    access = defaultdict(datetime.now)
    m_time = defaultdict(float)
    cooldown = timedelta(seconds=15)

    def __init__(self, path, new=False, without_row_id=False):
        super().__init__(path, new, without_row_id)

        # top_points.Points.Lordaeron
        self.object_id = ".".join((
            self.__class__.__module__,
            self.__class__.__name__,
            path.stem,
        ))

    def db_was_updated(self):
        if self.on_cooldown():
            # LOGGER.debug(f"{mtime_cached:10} | {mtime_current:10} | {'. Cooldown':10} | {self.object_id:40}")
            return False
        
        mtime_current = int(self.path.mtime)
        mtime_cached = self.m_time[self.object_id]

        if mtime_current == mtime_cached:
            LOGGER.debug(f"{mtime_cached:10} | {mtime_current:10} | {'= Same':10} | {self.object_id:40}")
            return False
        
        LOGGER.debug(f"{mtime_cached:10} | {mtime_current:10} | {'+ Updated':10} | {self.object_id:40}")
        self.m_time[self.object_id] = mtime_current
        return True
    
    def on_cooldown(self):
        last_check = self.access[self.object_id]
        now = datetime.now()
        if last_check > now:
            return True
        
        self.access[self.object_id] = now + self.cooldown
        return False


def main():
    q = DB.get_table_name("Rotface", "25H")
    print(q)


if __name__ == "__main__":
    main()
