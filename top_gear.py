import gzip
import json
from datetime import datetime

from api_db import DB, Table
from c_path import Directories, PathExt, StrEnum
from h_debug import Loggers, running_time

LOGGER_GEAR_PARSER = Loggers.gear
NO_DATA = (0, gzip.compress(b"{}"))

def is_same_as_last_recorded(player_profile: dict, new_profile: dict):
    old_profiles = list(player_profile.values())
    if not old_profiles:
        return False
    
    last_profile = old_profiles[-1]
    if not isinstance(last_profile, dict):
        last_profile = player_profile.get(last_profile)
    
    return new_profile == last_profile

def add_new_gear_set(player_profile: dict, new_profile: dict):
    timestamp_now = int(datetime.now().timestamp())
    for timestamp, profile in player_profile.items():
        if profile == new_profile:
            player_profile[timestamp_now] = timestamp
            return

    player_profile[timestamp_now] = new_profile


class Columns(StrEnum):
    NAME = "name"
    LAST_MODIFIED = "last_modified"
    DATA = "data"


class CharGear:
    def __init__(
        self,
        name: str,
        server: str,
        last_modified: int,
        data: bytes,
    ) -> None:
        self.name = name
        self.server = server
        self.last_modified = last_modified
        self.data = data
        self.size = len(data)
        self.size_compressed = self.size

    @property
    def gear_dict(self) -> dict:
        try:
            return self._gear_dict
        except AttributeError:
            pass

        json_bytes = gzip.decompress(self.data)
        self._gear_dict = json.loads(json_bytes)
        return self._gear_dict

    def gear_id(self):
        return f"{self.server}--{hash(self.name)}--{self.last_modified}"
    
    def add_new_gear_snippet(self, new_profile: dict):
        if not new_profile:
            LOGGER_GEAR_PARSER.debug(f"{self.name:12} | parse_profile | not new_profile")
            return
        
        if self.is_same_as_last_recorded(new_profile):
            LOGGER_GEAR_PARSER.debug(f"{self.name:12} | parse_profile | same as before")
            return
        
        timestamp_now = int(datetime.now().timestamp())
        for timestamp, profile in self.gear_dict.items():
            if profile == new_profile:
                self.gear_dict[timestamp_now] = timestamp
                return

        self.gear_dict[timestamp_now] = new_profile
        return True
    
    def is_same_as_last_recorded(self, new_profile: dict):
        try:
            last_profile = next(reversed(self.gear_dict.values()))
        except StopIteration:
            return False
        
        if not isinstance(last_profile, dict):
            last_profile = self.gear_dict.get(last_profile)
        
        return new_profile == last_profile


class TableGear(Table):
    without_row_id = True
    COLUMNS_ORDERED = list(Columns.__members__.values())
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]
    def __init__(self, name: str="main"):
        super().__init__(name)

    def player_query(self, player_name: str):
        return "\n".join((
            f"SELECT {Columns.LAST_MODIFIED}, {Columns.DATA}",
            f"FROM [{self.name}]",
            f"WHERE {Columns.NAME}='{player_name}'",
        ))


class GearDB(DB):
    def __init__(self, server: str, new=False) -> None:
        path = Directories.gear / f"{server}.db"
        super().__init__(path, new, without_row_id=True)
        self.server = server
        self.table = TableGear(server)

    def get_player_data(self, player_name: str):
        query = self.table.player_query(player_name)
        try:
            LAST_MODIFIED, DATA = self.cursor.execute(query).fetchone()
        except TypeError:
            LAST_MODIFIED, DATA = NO_DATA
        except Exception:
            LOGGER_GEAR_PARSER.exception(f"{player_name:12} | get_player_data")
            LAST_MODIFIED, DATA = NO_DATA

        return CharGear(
            name=player_name,
            server=self.server,
            last_modified=LAST_MODIFIED,
            data=DATA,
        )

    @running_time
    def get_player_data_dict(self, player_name: str):
        character = self.get_player_data(player_name)
        return character.gear_dict

    def update_player(self, player_name: str, new_profile: dict):
        if not new_profile:
            LOGGER_GEAR_PARSER.debug(f"{player_name:12} | parse_profile | not new_profile")
            return
        
        player_profile = self.get_player_data_dict(player_name)
        if is_same_as_last_recorded(player_profile, new_profile):
            LOGGER_GEAR_PARSER.debug(f"{player_name:12} | parse_profile | same as before")
            return

        add_new_gear_set(player_profile, new_profile)

        rows = (
            new_db_row(player_name, player_profile),
        )
        self.add_new_rows(self.table, rows)
        LOGGER_GEAR_PARSER.debug(f"{player_name:12} | parse_profile | added")
        return True


def new_db_row(name: str, data: dict):
    if not data:
        LOGGER_GEAR_PARSER.debug(f"{name:12} | new_db_row | not new_profile")
        return
    
    jd = json.dumps(data, separators=(',', ':'))
    jdb = jd.encode()
    jdbgzip = gzip.compress(jdb)
    return name, int(next(reversed(data))), jdbgzip

def new_db_row_wrap_file(fpath: PathExt):
    data = fpath.read_bytes()
    try:
        data_dict = json.loads(data)
    except Exception:
        return
    return new_db_row(fpath.stem, data_dict)

def test1():
    server = "Lordaeron"
    db = GearDB(server)
    # z = db.get_player_data_dict("Nomadra")
    z = db.get_player_data_dict("Nyaffliction")
    print(z.keys())
    # server = "Icecrown"
    # db = GearDB(server)
    # z = db.get_player_data_dict("Deydraenna")
    # print(z)

def test2():
    f = PathExt(r"F:\Python\uwulogs\temp\Nyaffliction.json")
    fj = f.json()

    d = list(fj.values())[-1]

    db = GearDB("Lordaeron")
    s = db.update_player("Nyaffliction", d)
    print(s)

if __name__ == "__main__":
    # _convert()
    test2()
    test1()
