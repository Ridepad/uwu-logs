import json
import sqlite3
from datetime import datetime
from typing import TypedDict

from api_db import DB, Table, Cache
from c_path import Directories, StrEnum
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


class TopDict(TypedDict):
    r: str
    t: int
    i: int
    n: str
    u: int
    d: int
    s: int
    a: list[int]

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


class TableTop(Table):
    without_row_id = True
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

    def query_dps_player_raid_id(self, player_raid_id):
        return f"""
        SELECT {Columns.USEFUL_DPS}
        FROM [{self.name}]
        WHERE {Columns.PLAYER_RAID_ID}='{player_raid_id}'
        """
        

def _dps(entry: TopDict):
    return round(entry["u"] / entry["t"], 2)

class TopDB(DB):
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
            
            table = TableTop(table_name)
            try:
                to_insert = self._only_better(table, combined_data)
            except sqlite3.OperationalError:
                to_insert = combined_data.values()
            
            rows = list(map(new_db_row, to_insert))
            self.add_new_rows(table, rows)

    @staticmethod
    def squash_top(new_data: list[TopDict]):
        top: dict[str, TopDict] = {}
        for new in new_data:
            player_id = get_player_id(new)
            cached = top.get(player_id)
            if not cached or _dps(new) > _dps(cached):
                top[player_id] = new
        return top
    
    def _only_better(self, table: TableTop, combined_data: dict[str, dict]):
        to_insert = []
        for _id, new_entry in combined_data.items():
            query = table.query_dps_player_raid_id(_id)
            row = self.cursor.execute(query).fetchone()
            if row is None or _dps(new_entry) > row[0]:
                to_insert.append(new_entry)
        return to_insert

class TopDBCached(TopDB, Cache):
    pass


def main():
    q = DB.get_table_name("Rotface", "25H")
    print(q)


if __name__ == "__main__":
    main()
