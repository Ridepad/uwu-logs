from collections import defaultdict
from datetime import timedelta

import numpy
from pydantic import BaseModel, field_validator

from api_top_db_v2 import TopDBCached
from c_bosses import ALL_FIGHT_NAMES
from c_server_phase import Encounter
from c_path import Directories
from c_player_classes import SPECS_LIST
from h_debug import running_time
from h_server_fix import server_cnv


IGNORED_SPECS = set([*range(0, 40, 4), 7, 17, 18, 21, 22, 31, 39])
SPECS_DATA_NOT_IGNORED = [
    spec_data
    for spec_data in SPECS_LIST
    if spec_data.index not in IGNORED_SPECS
]
API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "boss": "The Lich King",
        "mode": "25H",
    },
]

def n_greater_than(data: numpy.ndarray, value: float):
    return int((data > value).sum())

def get_percentile(data, percentile):
    if percentile == 100:
        dps = max(data)
        raids = 1
    elif percentile == 0:
        dps = 0
        raids = len(data)
    else:
        dps = numpy.percentile(data, percentile)
        dps = round(dps, 2)
        raids = n_greater_than(data, dps)
    
    return {
        "dps": dps,
        "raids": raids,
    }

@running_time
def convert_boss_data(data: dict[int, list[float]]):
    BOSS_DATA = {}
    for spec_index, values in data.items():
        if spec_index in IGNORED_SPECS:
            continue
        if len(values) < 5:
            continue
        
        data_s = numpy.fromiter(values, dtype=numpy.float64)
        spec_html = SPECS_LIST[spec_index].html_name
        BOSS_DATA[spec_html] = {
            "top100": get_percentile(data_s, 100),
            "top99": get_percentile(data_s, 99),
            "top95": get_percentile(data_s, 95),
            "top90": get_percentile(data_s, 90),
            "top75": get_percentile(data_s, 75),
            "top50": get_percentile(data_s, 50),
            "top10": get_percentile(data_s, 10),
            "all": get_percentile(data_s, 0),
        }
    return BOSS_DATA


class PveStatsValidation(BaseModel):
    server: str
    boss: str
    mode: str

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
            raise ValueError(f"[server] value value must be from [{_list}]")
        return server

    @field_validator('boss')
    @classmethod
    def validate_boss(cls, boss: str):
        if boss not in ALL_FIGHT_NAMES:
            _list = ', '.join(ALL_FIGHT_NAMES)
            raise ValueError(f"[boss] value value must be from [{_list}]")
        return boss

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, mode: str):
        mode = mode.upper()
        modes = ["10N", "10H", "25N", "25H"]
        if mode not in modes:
            _list = ', '.join(modes)
            raise ValueError(f"[boss] value value must be from [{_list}]")
        return mode

class PveStats(TopDBCached):
    cache = defaultdict(dict)
    cooldown = timedelta(minutes=10)

    def __init__(self, model: PveStatsValidation) -> None:
        super().__init__(model.server)
        self.encounter = Encounter(model.boss, model.mode)
        self.table_name = self.encounter.table_name

    def get_data(self):
        server_data = self.cache[self.server]
        if self.db_was_updated():
            server_data = self.cache[self.server] = {}
        
        if self.table_name not in server_data:
            server_data[self.table_name] = self._renew_data()

        return server_data[self.table_name]

    def _renew_data(self):
        query = self.encounter.query_stats()
        rows_generator = self.cursor.execute(query)

        data = defaultdict(list)
        for spec, dps in rows_generator:
            data[spec].append(dps)

        return convert_boss_data(data)

def _test1():
    conf = API_EXAMPLES[0]
    q = PveStatsValidation(**conf)
    z = PveStats(q)
    for x, y in z.get_data().items():
        print(x)
        print(y)

if __name__ == "__main__":
    _test1()
