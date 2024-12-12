from collections import defaultdict
from itertools import islice
from typing import Union

from pydantic import BaseModel, field_validator

from api_db import (
    DB,
    DataCompressed,
    LIMITS,
    LIMITS_JOINED,
)
from api_top_db_v2 import (
    Columns,
    TopDBCached,
    HEADERS_TO_COLUMNS_NAMES,
    SORT_REVERSED,
)
from c_bosses import ALL_FIGHT_NAMES
from c_path import Directories
from h_debug import running_time


API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "boss": "The Lich King",
        "mode": "25H",
        "class_i": 5,
        "spec_i": 3,
        "limit": LIMITS[0],
    },
]

EXT_DATA = {
    "10060": "Power Infusion",
    "19753": "Divine Intervention",
    "49016": "Hysteria",
    "57933": "Tricks of the Trade",
}
EXT_IDS = tuple(EXT_DATA)

def has_external(auras: str):
    for id in EXT_IDS:
        if id in auras:
            return True
    return False

def spec_db_query(class_i: int, spec_i: int):
    if class_i == -1:
        spec_q = ""
    elif spec_i == -1:
        spec_q = f"WHERE {Columns.SPEC} between {class_i*4} and {class_i*4+3}"
    else:
        spec_i = class_i * 4 + spec_i
        spec_q = f"WHERE {Columns.SPEC}={spec_i}"
    return spec_q

class TopValidation(BaseModel):
    server: str
    boss: str
    mode: str
    class_i: int
    spec_i: int
    sort_by: str = Columns.USEFUL_DPS
    limit: int = LIMITS[1]
    best_only: bool = True
    externals: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": API_EXAMPLES,
        }
    }

    def build_query_string(self, filter_raid_ids: str=None):
        table_name = DB.get_table_name(self.boss, self.mode)
        select_q = self._query_select()
        order = "ASC" if self.sort_by in SORT_REVERSED else "DESC"
        if filter_raid_ids:
            where_q = f"WHERE {Columns.PLAYER_RAID_ID} IN ({filter_raid_ids})"
        else:
            where_q = spec_db_query(self.class_i, self.spec_i)

        return '\n'.join((
            f"SELECT {select_q}",
            f"FROM [{table_name}]",
            where_q,
            f"ORDER BY {self.sort_by} {order}",
        ))
    
    def _query_select(self):
        if self.best_only:
            return f"{Columns.FORMATTED_STRING}, guid"
        return Columns.FORMATTED_STRING
    
    def query_auras(self):
        table_name = DB.get_table_name(self.boss, self.mode)
        where = spec_db_query(self.class_i, self.spec_i)
        return "\n".join((
            f"SELECT {Columns.PLAYER_RAID_ID}, {Columns.AURAS}",
            f"FROM [{table_name}]",
            where,
        ))

    @field_validator("server")
    @classmethod
    def validate_server(cls, server: str):
        servers = Directories.top.files_stems()
        if server not in servers:
            _list = ", ".join(servers)
            raise ValueError(f"[server] value value must be from [{_list}]")
        return server

    @field_validator("boss")
    @classmethod
    def validate_boss(cls, boss: str):
        if boss not in ALL_FIGHT_NAMES:
            _list = ", ".join(ALL_FIGHT_NAMES)
            raise ValueError(f"[boss] value value must be from [{_list}]")
        return boss

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, mode: str):
        mode = mode.upper()
        modes = ["10N", "10H", "25N", "25H"]
        if mode not in modes:
            _list = ", ".join(modes)
            raise ValueError(f"[boss] value value must be from [{_list}]")
        return mode

    @field_validator("class_i")
    @classmethod
    def validate_class_i(cls, class_i: Union[str, int]):
        class_i = int(class_i)
        if class_i not in range(-1, 10):
            raise ValueError("[class_i] value must be from -1 to 9")
        return class_i

    @field_validator("spec_i")
    @classmethod
    def validate_spec_i(cls, spec_i: Union[str, int]):
        spec_i = int(spec_i)
        if spec_i not in {-1, 1, 2, 3}:
            raise ValueError("[spec_i] value must be from [-1, 1, 2, 3]")
        return spec_i

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, sort_by: str):
        try:
            return HEADERS_TO_COLUMNS_NAMES[sort_by]
        except KeyError:
            _list = ", ".join(HEADERS_TO_COLUMNS_NAMES)
            raise ValueError(f"[sort_by] value value must be from [{_list}]")

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, limit: Union[str, int]):
        limit = int(limit)
        if limit not in LIMITS:
            raise ValueError(f"[limit] value value must be from [{LIMITS_JOINED}]")
        return limit


class Top(TopDBCached):
    cache: defaultdict[str, dict[int, DataCompressed]] = defaultdict(dict)

    def __init__(self, model: TopValidation) -> None:
        super().__init__(model.server)

        self.model = model
        self.json_query = model.model_dump_json()
        self.limit = model.limit
        self.best_only = model.best_only
        self.table_name = self.get_table_name(model.boss, model.mode)
    
    @property
    def db_query(self):
        filter_raid_ids = None
        if not self.model.externals:
            filter_raid_ids = self._raid_ids_no_ext()
        return self.model.build_query_string(filter_raid_ids)

    def get_data(self):
        if self.db_was_updated():
            self.cache[self.server].clear()
        
        server_data = self.cache[self.server]
        if self.json_query not in server_data:
            server_data[self.json_query] = self._renew_data()
            
        return server_data[self.json_query]

    @running_time
    def _renew_data(self):
        try:
            db_json_strings = self._db_json_strings()
        except Exception: # sqlite3.OperationalError
            db_json_strings = []
        _json = self._combine_json(db_json_strings)
        return DataCompressed(_json)
    
    def _db_json_strings(self):
        if self.best_only:
            return self._best()
        return self._all()

    @staticmethod
    def _combine_json(data: list[bytes]):
        if not data:
            return b'[]'

        data[0] = b"[" + data[0]
        data[-1] = data[-1] + b"]"
        return b','.join(data)

    def _best(self) -> list[bytes]:
        rows_generator = self.cursor.execute(self.db_query)

        s = {}
        for json_text, guid in rows_generator:
            if guid in s:
                continue
            s[guid] = json_text
            if len(s) >= self.limit:
                break
        
        return list(s.values())

    def _all(self) -> list[bytes]:
        rows_generator = self.cursor.execute(self.db_query)
        return [v for v, in islice(rows_generator, self.limit)]

    def _raid_ids_no_ext(self):
        query = self.model.query_auras()
        raid_ids = (
            raid_id
            for raid_id, auras in self.cursor.execute(query)
            if not has_external(auras)
        )
        return ','.join(f'"{x}"' for x in raid_ids)


def _test1():
    conf = API_EXAMPLES[0]
    q = TopValidation(**conf)
    z = Top(q)
    for x in z._db_json_strings():
        print(x)

if __name__ == "__main__":
    _test1()
