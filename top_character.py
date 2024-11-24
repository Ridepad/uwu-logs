from typing import Union

from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    field_validator,
)

from api_top_db_v2 import TopDB
from c_path import Directories
from h_debug import running_time
from top_player_data import PlayerDataServer
from top_points import PointsServer


API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "name": "Safiyah",
        "spec_i": "3"
    },
]

DEFAULT_SPEC = [3, 1, 2, 2, 3, 3, 2, 1, 2, 2]

class CharacterValidation(BaseModel):
    server: str
    name: str
    spec_i: Union[str, int, None] = Field(default=0, validation_alias=AliasChoices('spec_i', 'spec'))

    model_config = {
        "json_schema_extra": {
            "examples": API_EXAMPLES,
        }
    }

    @field_validator('server')
    @classmethod
    def validate_server(cls, server: str):
        servers = Directories.top.files_stems()
        if server not in servers:
            _list = ', '.join(servers)
            raise ValueError(f"[server] value value must be from [{_list}]")
        return server

    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str):
        return name.strip().lower().title().replace(" ", "")

    @field_validator('spec_i')
    @classmethod
    def validate_spec_i(cls, spec_i: Union[str, int, None]):
        try:
            return int(spec_i)
        except Exception:
            return 0


class Character(TopDB):
    def __init__(self, model: CharacterValidation) -> None:
        super().__init__(model.server)
        
        self.info = PlayerDataServer(model.server).player_info(model.name)
        spec_i = model.spec_i
        if spec_i not in range(1, 4):
            spec_i = DEFAULT_SPEC[self.info.class_i]
        spec_i += self.info.class_i * 4

        self.points_cache = PointsServer(model.server).get_spec_data(spec_i)

    @running_time
    def get_player_data(self):
        return {
            "class_i": self.info.class_i,
            "name": self.info.name,
            "server": self.server,
            "overall_points": self._overall_points(),
            "overall_rank": self._overall_rank(),
            "bosses": self._bosses(),
        }
    
    def _overall_rank(self):
        return self.points_cache.get_player_rank(self.info.guid)

    def _overall_points(self):
        return self.points_cache.get_player_overall_points(self.info.guid)

    def _bosses(self):
        d = {}
        for encounter in self.points_cache.phase.ALL_BOSSES:
            boss_data_by_spec = self.points_cache[encounter.table_name]
            data = boss_data_by_spec.player_data(self.info.guid)
            if data:
                key = data["raid_id"]
                query = encounter.query_row_id_min(key)
                duration, report_id = self.cursor.execute(query).fetchone()
                data["fastest_kill_duration"] = duration
                data["report_id"] = f"{report_id}--{self.server}"
            d[encounter.name] = data

        return d


def _test1():
    from time import perf_counter_ns
    for _ in range(5):
        pc = perf_counter_ns()
        q = CharacterValidation(server="Lordaeron", name="Safiyah", spec_i=3)
        done_ms = (perf_counter_ns() - pc) / 1_000_000
        print(f'{done_ms:>10,.3f}ms | Done')
    print(q)

def _test2():
    conf = API_EXAMPLES[0]
    q = CharacterValidation(**conf)
    z = Character(q)
    for x, y in z.get_player_data().items():
        print(x)
        print(y)

if __name__ == "__main__":
    _test1()
    _test2()
