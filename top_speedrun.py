
from collections import defaultdict
import json
from pydantic import BaseModel, field_validator
from api_top_db_v2 import (
    DB,
    Cache,
    TopDataCompressed,
)
from c_path import Directories, StrEnum
from h_debug import running_time
from h_server_fix import server_cnv


API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "raid": "Icecrown Citadel",
    },
]


class ColumnsSpeedrun(StrEnum):
    REPORT_ID = "report_id"
    TOTAL_LENGTH = "total_length"
    SEGMENTS_SUM = "segments_sum"

HEADERS_TO_COLUMNS_NAMES = {
    "head-speedrun-total-length": ColumnsSpeedrun.TOTAL_LENGTH,
    "head-speedrun-segments-sum": ColumnsSpeedrun.SEGMENTS_SUM,
}

def new_db_row(s: str):
    total_length, segments_sum, report_id = s.split('--', 2)
    report_id = report_id.rsplit("--", 1)[0]
    total_length = float(total_length)
    segments_sum = float(segments_sum)
    return report_id, total_length, segments_sum

class SpeedrunDB(DB):
    COLUMNS_ORDERED = list(ColumnsSpeedrun.__members__.values())
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]

    def __init__(self, new=False) -> None:
        path = Directories.main / "speedrun.db"
        super().__init__(path, new)

    def add_new_data(self, table_name: str, data: list):
        if not data:
            return
        
        new_table_created = self.new_table(table_name)

        rows = map(new_db_row, data)
        self.add_new_rows(table_name, rows)

        if new_table_created:
            self.add_indexes(table_name)


class SpeedrunValidation(BaseModel):
    server: str
    raid: str
    sort_by: str = SpeedrunDB.COLUMNS_ORDERED[1]

    model_config = {
        "json_schema_extra": {
            "examples": API_EXAMPLES,
        }
    }

    @field_validator('server')
    @classmethod
    def validate_server(cls, server: str):
        server = server_cnv(server)
        servers = Directories.top.files_stems()
        if server not in servers:
            _list = ', '.join(servers)
            raise ValueError(f"[server] value must be from [{_list}]")
        return server
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, sort_by: str):
        try:
            return HEADERS_TO_COLUMNS_NAMES[sort_by]
        except KeyError:
            _list = ", ".join(HEADERS_TO_COLUMNS_NAMES)
            raise ValueError(f"[sort_by] value must be from [{_list}]")


    def build_query_string(self):
        table_name = DB.get_table_name(self.server, self.raid)
        return f'''
        SELECT *
        FROM [{table_name}]
        ORDER BY {self.sort_by}
        '''


class Speedrun(SpeedrunDB, Cache):
    cache: defaultdict[str, dict[str, TopDataCompressed]] = defaultdict(dict)

    def __init__(self, model: SpeedrunValidation) -> None:
        super().__init__()
        self.table_name = self.get_table_name(model.server, model.raid)
        self.db_query = model.build_query_string()
        self.json_query = model.model_dump_json()
    
    @running_time
    def data(self):
        if self.db_was_updated():
            self.cache[self.json_query].clear()
        
        server_data = self.cache[self.json_query]
        if self.json_query not in server_data:
            server_data[self.json_query] = self._new_compressed_data()
            
        return server_data[self.json_query]
    
    def _new_compressed_data(self):
        j = json.dumps(self.cursor.execute(self.db_query), default=list)
        return TopDataCompressed(j.encode())


def main():
    server = "Lordaeron"
    raid = "Icecrown Citadel"
    db = SpeedrunDB(new=True)
    speedrun_dir = Directories.main.new_child("speedrun")
    speedrun_txt = speedrun_dir / f"{server}.txt"
    
    data = speedrun_txt.read_text().splitlines()
    table_name = db.get_table_name(server, raid)
    db.add_new_data(table_name, data)


if __name__ == "__main__":
    main()
