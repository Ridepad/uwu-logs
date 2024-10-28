import json
from collections import defaultdict

from pydantic import BaseModel, field_validator

from api_db import (
    Cache,
    DB,
    DataCompressed,
    Table,
)
from c_path import Directories, StrEnum
from h_debug import running_time
from h_server_fix import server_cnv


API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "raid": "Icecrown Citadel",
        "mode": "25H",
    },
]


class Columns(StrEnum):
    REPORT_ID = "report_id"
    TOTAL_LENGTH = "total_length"
    SEGMENTS_SUM = "segments_sum"
    GUILD = "guild"
    FACTION = "faction"

HEADERS_TO_COLUMNS_NAMES = {
    "head-speedrun-total-length": Columns.TOTAL_LENGTH,
    "head-speedrun-segments-sum": Columns.SEGMENTS_SUM,
}


class TableSpeedrun(Table):
    COLUMNS_ORDERED = list(Columns.__members__.values())
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]

    def query_get(self, sort_by="DESC"):
        return f'''
        SELECT *
        FROM [{self.name}]
        ORDER BY {sort_by}
        '''


def new_db_row(s: str):
    total_length, segments_sum, report_id = s.split('--', 2)
    report_id = report_id.rsplit("--", 1)[0]
    total_length = float(total_length)
    segments_sum = float(segments_sum)
    return report_id, total_length, segments_sum

class SpeedrunDB(DB):
    def __init__(self, server: str, new=False) -> None:
        path = Directories.speedrun / f"{server}.db"
        super().__init__(
            path,
            new=new,
            without_row_id=True,
        )
        self.server = server

    def add_new_data(self, table_name: str, data: list[str]):
        table = TableSpeedrun(table_name)
        rows = list(map(new_db_row, data))
        self.add_new_rows(table, rows)
    
class SpeedrunValidation(BaseModel):
    server: str
    raid: str
    mode: str = "25H"
    sort_by: str = Columns.TOTAL_LENGTH

    model_config = {
        "json_schema_extra": {
            "examples": API_EXAMPLES,
        }
    }

    @field_validator('server')
    @classmethod
    def validate_server(cls, server: str):
        server = server_cnv(server)
        servers = sorted((
            file.stem
            for file in Directories.speedrun.files
            if file.suffix == ".db"
        ))
        if server not in servers:
            _list = ', '.join(servers)
            raise ValueError(f"[server] value must be from [{_list}]")
        return server

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, mode: str):
        mode = mode.upper()
        modes = ["10N", "10H", "25N", "25H"]
        if mode not in modes:
            _list = ', '.join(modes)
            raise ValueError(f"[boss] value value must be from [{_list}]")
        return mode
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, sort_by: str):
        try:
            return HEADERS_TO_COLUMNS_NAMES[sort_by]
        except KeyError:
            _list = ", ".join(HEADERS_TO_COLUMNS_NAMES)
            raise ValueError(f"[sort_by] value must be from [{_list}]")


class Speedrun(SpeedrunDB, Cache):
    cache: defaultdict[str, dict[str, DataCompressed]] = defaultdict(dict)

    def __init__(self, model: SpeedrunValidation) -> None:
        super().__init__(model.server)
        self.json_query = model.model_dump_json()
        
        sort_by = model.sort_by
        table_name = self.get_table_name(model.raid, model.mode)
        table = TableSpeedrun(table_name)
        self.query = table.query_get(sort_by)
    
    @running_time
    def data(self):
        server_data = self.cache[self.json_query]
        if self.db_was_updated():
            server_data.clear()
        
        if self.json_query not in server_data:
            server_data[self.json_query] = self._new_compressed_data()
            
        return server_data[self.json_query]
    
    def _new_compressed_data(self):
        a = self._new_data()
        j = json.dumps(a, separators=(",", ":"), default=list)
        jb = j.encode()
        return DataCompressed(jb)
    
    def _new_data(self):
        return self.cursor.execute(self.query)


def test1():
    sv = SpeedrunValidation(**API_EXAMPLES[0])
    data = Speedrun(sv)._new_data()
    for x in data:
        print(x)

if __name__ == "__main__":
    test1()
