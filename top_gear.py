from datetime import datetime
import gzip
import json
from api_top_db_v2 import DB
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

    def gear_dict(self):
        json_bytes = gzip.decompress(self.data)
        return json.loads(json_bytes)

    def gear_id(self):
        return f"{self.server}-{self.name}-{self.last_modified}"


class GearDB(DB):
    COLUMNS_ORDERED = list(Columns.__members__.values())
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]

    def __init__(self, server: str, new=False) -> None:
        path = Directories.gear / f"{server}.db"
        super().__init__(path, new, without_row_id=True)
        self.server = server

    def get_player_data(self, player_name: str):
        query = self.player_query(player_name)
        try:
            LAST_MODIFIED, DATA = self.cursor.execute(query).fetchone()
        except Exception as e:
            LOGGER_GEAR_PARSER.exception(f"get_player_data | {player_name:12}")
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
        return character.gear_dict()

    def player_query(self, player_name: str):
        return f"""
        SELECT {Columns.LAST_MODIFIED}, {Columns.DATA}
        FROM [{self.server}]
        WHERE {Columns.NAME}='{player_name}'
        """
    
    def add(self, player_name: str, new_profile: dict):
        if not new_profile:
            LOGGER_GEAR_PARSER.debug(f"parse_profile | {player_name:12} | not new_profile")
            return
        
        player_profile = self.get_player_data_dict(player_name)
        if is_same_as_last_recorded(player_profile, new_profile):
            LOGGER_GEAR_PARSER.debug(f"parse_profile | {player_name:12} | same as before")
            return

        add_new_gear_set(player_profile, new_profile)

        rows = (
            new_db_row(player_name, player_profile),
        )
        self.add_new_data(rows)
        LOGGER_GEAR_PARSER.debug(f"parse_profile | {player_name:12} | added")
        return True

    def add_new_data(self, rows: list):
        if not rows:
            return
        
        table_name = self.server
        new_table_created = self.new_table(table_name)

        self.add_new_rows(table_name, rows)

        if new_table_created:
            self.add_indexes(table_name)


def new_db_row(name: str, data: dict):
    if not data:
        LOGGER_GEAR_PARSER.debug(f"new_db_row | {name:12} | not new_profile")
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

def _convert():
    char_path = Directories.cache / "character"
    for char_path_server in char_path.iterdir():
        if not char_path_server.is_dir():
            continue

        server = char_path_server.stem
        g = (
            new_db_row_wrap_file(file)
            for file in char_path_server.iterdir()
            if file.suffix == ".json"
        )
        g = (x for x in g if x)
        db = GearDB(server, new=True)
        db.add_new_data(g)

def test1():
    server = "Lordaeron"
    db = GearDB(server)
    z = db.get_player_data_dict("Nomadra")
    print(z)
    server = "Icecrown"
    db = GearDB(server)
    z = db.get_player_data_dict("Deydraenna")
    print(z)


if __name__ == "__main__":
    # _convert()
    test1()
