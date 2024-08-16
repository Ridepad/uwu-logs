from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Union

from pydantic import BaseModel, field_validator

from api_top_db_v2 import TopDBCached
from c_bosses import ALL_FIGHT_NAMES
from c_path import Directories
from c_player_classes import SPECS_DICT
from c_server_phase import Encounter
from h_debug import running_time
from h_server_fix import server_cnv


API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "boss": "The Lich King",
        "mode": "25H",
        "dps": {
            "Safiyah": "12345.6",
            "Nomadra": "12345.6",
        },
        "specs": {
            "Safiyah": "Shadow Priest",
            "Nomadra": "Balance Druid",
        },
    },
]

class RaidRankValidation(BaseModel):
    server: str
    boss: str
    mode: str
    dps: dict[str, Union[str, float]]
    specs: dict[str, Union[str, int]]
    
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

    @field_validator('dps')
    @classmethod
    def dps_to_numbers(cls, dps: dict[str, Union[str, float]]):
        return {
            name: float(dps)
            for name, dps in dps.items()
        }

    @field_validator('specs')
    @classmethod
    def specs_to_int(cls, specs: dict[str, Union[int, str]]):
        z: dict[str, int] = {}
        for name, spec_i in specs.items():
            if spec_i in SPECS_DICT:
                z[name] = SPECS_DICT[spec_i].index
            elif type(spec_i) == int:
                z[name] = spec_i
            elif spec_i.isdigit():
                z[name] = int(spec_i)
            else:
                raise ValueError(f"{name} has wrong spec")
        return z


class RaidRank(TopDBCached):
    cache: defaultdict[str, dict[str, dict[int, list[float]]]] = defaultdict(dict)
    access: defaultdict[str, datetime] = defaultdict(datetime.now)
    m_time: defaultdict[str, float] = defaultdict(float)
    cooldown = timedelta(minutes=15)

    def __init__(self, model: RaidRankValidation) -> None:
        super().__init__(model.server)
        self.model = model
        self.encounter = Encounter(model.boss, model.mode)
        self.table_name = self.encounter.table_name

    @running_time
    def points(self):
        dps = self.model.dps
        specs = self.model.specs
        return {
            player_name: self._format_rank(specs[player_name], player_dps)
            for player_name, player_dps in dps.items()
            if player_name in specs
        }

    def _format_rank(self, spec_i: int, dps: float):
        spec_data = self._spec_data(spec_i)
        
        total_raids = len(spec_data)
        if not total_raids or not spec_data[-1]:
            return {
                "rank": 1,
                "percentile": 100.0,
                "from_spec_top1": 100.0,
                "total_raids_for_spec": 1,
            }
        
        dps = dps + 0.01
        rank_reversed = bisect_right(spec_data, dps)
        rank = total_raids - rank_reversed + 1
        percentile = rank_reversed / total_raids * 100
        percentile = round(percentile, 2)
        perc_from_top1 = dps / spec_data[-1] * 100
        perc_from_top1 = round(perc_from_top1, 1)
        return {
            "rank": rank,
            "percentile": percentile,
            "from_spec_top1": perc_from_top1,
            "total_raids_for_spec": total_raids,
        }

    def _cache(self):
        if self.db_was_updated():
            server_data = self.cache[self.server] = {}
        else:
            server_data = self.cache[self.server]
        
        if self.table_name not in server_data:
            server_data[self.table_name] = {}
        
        return server_data[self.table_name]
    
    def _renew_data(self, spec_index: int) -> list[float]:
        query = self.encounter.query_dps_spec(spec_index)
        return sorted(x for x, in self.cursor.execute(query))
    
    def _spec_data(self, spec_index: int) -> list[float]:
        _data = self._cache()
        if spec_index not in _data:
            _data[spec_index] = self._renew_data(spec_index)
        return _data[spec_index]


def _test1():
    conf = API_EXAMPLES[0]
    q = RaidRankValidation(**conf)
    z = RaidRank(q)
    for x, y in z.points().items():
        print(x)
        print(y)

if __name__ == "__main__":
    _test1()
