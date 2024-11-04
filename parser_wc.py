import time
from collections import defaultdict

import logs_calendar
import logs_main
import top_gear
from api_db import DB, Table
from api_top_db_v2 import (
    TableTop,
    TopDB,
    Columns as ColumnsTop,
)
from api_wow_circle import (
    WCCharactersProfiles,
    WCServer,
)
from c_path import Directories, StrEnum
from h_debug import Loggers
from h_server_fix import SERVERS_WC

LOGGER = Loggers.gear

SERVER_NAME = "WoW-Circle"
BOSSES_ICC = [
    "Lord Marrowgar",
    "Lady Deathwhisper",
    "Deathbringer Saurfang",
    "Festergut",
    "Rotface",
    "Professor Putricide",
    "Blood Prince Council",
    "Blood-Queen Lana'thel",
    "Sindragosa",
    "The Lich King",
]


class Columns(StrEnum):
    REPORT_ID = "report_id"
    SERVER = "server"

class ColumnsPlayers(StrEnum):
    GUID = "guid"
    NAME = "name"


class TableTopExt(TableTop):
    def query_full_row_by_report(self, report_id_no_server: str):
        return f'''
        SELECT *
        FROM [{self.name}]
        WHERE {ColumnsTop.REPORT_ID}='{report_id_no_server}'
        '''

class WCLogsTable(Table):
    without_row_id = True
    COLUMNS_ORDERED = list(Columns)
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]
    def __init__(self, name="main"):
        super().__init__(name)
    
    def query_reports_servers(self, reports: list[str]):
        reports_str = ','.join(f'"{x}"' for x in reports)
        return '\n'.join((
            f"SELECT *",
            f"FROM [{self.name}]",
            f"WHERE {Columns.REPORT_ID} in ({reports_str})",
        ))
    
    def query_reports_ids(self):
        return '\n'.join((
            f"SELECT {Columns.REPORT_ID}",
            f"FROM [{self.name}]",
        ))

class WCLogsPlayersTable(Table):
    without_row_id = True
    COLUMNS_ORDERED = list(ColumnsPlayers)
    COLUMNS_TABLE_CREATE = [
        f"{COLUMNS_ORDERED[0]} PRIMARY KEY",
        *COLUMNS_ORDERED[1:],
    ]
    def __init__(self, name: str):
        super().__init__(name)
    
    def query_players(self, player_guids: list[int]):
        player_guids_str = ','.join(map(str, player_guids))
        return '\n'.join((
            f"SELECT *",
            f"FROM [{self.name}]",
            f"WHERE {ColumnsPlayers.GUID} in ({player_guids_str})",
        ))


class WCLogsDB(DB):
    def __init__(self, new=False):
        dirpath = Directories.db.new_child("custom_server")
        path = dirpath / f"{SERVER_NAME}.db"
        super().__init__(path, new)
        self.main_table = WCLogsTable()

    def get_reports(self, reports: list[str]):
        query = self.main_table.query_reports_servers(reports)
        try:
            return self.cursor.execute(query)
        except Exception:
            return []

    def get_missing_reports(self, reports: set[str]):
        query = self.main_table.query_reports_ids()
        try:
            cached_reports = {
                report_id
                for report_id, in self.cursor.execute(query)
            }
        except Exception:
            cached_reports = set()

        return reports - cached_reports

class WCLogsPlayersDB(WCLogsDB):
    def __init__(self, server: str, new=False):
        super().__init__(new)
        self.server = server
        self.players_table = WCLogsPlayersTable(self.server)

    def get_reports(self, reports: list[str]):
        query = self.main_table.query_reports_servers(reports)
        try:
            return self.cursor.execute(query)
        except Exception:
            return []

    def get_missing_reports(self, reports: set[str]):
        reports = set(reports)
        query = self.main_table.query_reports_ids()
        try:
            cached_reports = {
                report_id
                for report_id, in self.cursor.execute(query)
            }
            return reports - cached_reports
        except Exception:
            return reports

        
    def add_report(self, report_id: str):
        rows = [
            (report_id, self.server),
        ]
        self.add_new_rows(self.main_table, rows)
        
    def get_players(self, players: list[str]) -> dict[int, str]:
        query = self.players_table.query_players(players)
        try:
            data = self.cursor.execute(query)
            return dict(data)
        except Exception:
            return {}
        
    def add_players(self, players: dict[str, str]):
        rows = list(players.items())
        self.add_new_rows(self.players_table, rows)


class ReportPlayers:
    server_cache: defaultdict[str, dict[int, str]]
    def __init__(self, report_id: str, max_items=5):
        self.report_id = report_id
        self.max_items = max_items

    @property
    def players(self):
        try:
            return self._players
        except AttributeError:
            self._players = self._get_names_guids_pairs()
            return self._players

    def get_server(self):
        if not self.players:
            return
        
        server = self.get_server_from_db()
        if not server:
            server = self.get_server_from_api()
        LOGGER.debug(f"{self.report_id:40} | {server}")
        return server
        
    def some_players(self):
        items = list(self.players.items())
        if self.max_items:
            items = items[:self.max_items]
        return dict(items)
            
    def get_players_from_db(self, server: str):
        try:
            return WCLogsPlayersDB(server).get_players(self.players)
        except FileNotFoundError:
            return {}

    def get_server_from_db(self):
        half = len(self.players) // 2
        for server in SERVERS_WC:
            LOGGER.debug(f"> Checking from db {server}")
            overlap = 0
            cached_players = self.get_players_from_db(server)
            for player_guid, player_name in self.players.items():
                cached_name = cached_players.get(player_guid)
                if cached_name != player_name:
                    continue
                overlap += 1
            if overlap > half:
                return server

    def get_server_from_api(self):
        players = self.some_players()
        server = self._get_server_from_api(players)
        if not server:
            LOGGER.warning(f"! Server not found by small request")
            server = self._get_server_from_api(self.players)
        return server

    def _get_server_from_api(self, players):
        half = len(players) // 2
        for server in SERVERS_WC:
            LOGGER.debug(f"> Checking from api {server}")
            overlap = 0
            characters = WCServer(server).get_multi_char_data(players)
            for character in characters:
                if not character.exists:
                    continue
                if character.name != players.get(character.guid):
                    continue
                overlap += 1
            if overlap > half:
                return server

    def _get_names_guids_pairs(self):
        report = logs_main.THE_LOGS(self.report_id)
        guids = report.PLAYERS_GUIDS
        # guids_json = Directories.logs / self.report_id / "PLAYERS_DATA.json"
        # guids: dict[str, str] = guids_json.json_ignore_error()
        return {
            int(guid, 16): name
            for guid, name in guids.items()
        }


class WCParser(ReportPlayers):
    @property
    def server(self):
        try:
            return self._server
        except AttributeError:
            self._server = self._find_server()
            return self._server

    def _find_server(self):
        server = self.get_server()
        if not server:
            return
        db = WCLogsPlayersDB(server, new=True)
        db.add_players(self.players)
        db.add_report(self.report_id)
        return server

    def insert_from_top_db(self):
        db_main = TopDB(SERVER_NAME)
        db = TopDB(self.server, new=True)

        report_id_no_server = self.report_id.rsplit("--", 1)[0]

        for table_name in db_main.tables_names():
            t = TableTopExt(table_name)
            q = t.query_full_row_by_report(report_id_no_server)
            rows = db_main.cursor.execute(q)
            db.add_new_rows(t, rows)


class GearParser:
    def __init__(self, server: str, slice_size: int=50):
        self.server = server
        self.slice_size = slice_size
        self.delay = slice_size // 50 + 1

    def update_gear(self, players: list[int]):
        LOGGER.debug(f"{self.server:15} | update_gear length: {len(players)}")
        players = list(players)
        for i in range(0, len(players), self.slice_size):
            LOGGER.debug(f"{self.server:15} | update_gear {i:>4} | {len(players):>4}")
            players_slice = players[i:i + self.slice_size]
            self._update_gear(players_slice)

            LOGGER.debug(f"Sleeping for {self.delay} sec")
            time.sleep(self.delay)
    
    def _update_gear(self, players: list[int]):
        wc_chars = WCCharactersProfiles(self.server).get_profiles(players)
        LOGGER.debug(f"{self.server:15} | update_gear returned {len(wc_chars):>4} / {len(players):>4}")
    
        profiles_dicts = {}
        for wc_char in wc_chars:
            profiles_dicts[wc_char.char.name] = wc_char.profile()

        db = top_gear.GearDB(self.server, new=True)
        db.update_players_rows(profiles_dicts)

######################
def parse_specific(reports: list[str]):
    players_groupped = defaultdict(dict)
    
    for report_id in reports:
        p = WCParser(report_id)
        if not p.server:
            continue
        p.insert_from_top_db()
        players_groupped[p.server].update(p.players)
    
    for server, players in players_groupped.items():
        GearParser(server).update_gear(players)

def gen_reports():
    df = logs_calendar.read_main_df()
    df_filtered = df[df["server"] == SERVER_NAME]
    z = set(df_filtered.index)
    return z

def parse_new_reports():
    db = WCLogsDB()
    reports = gen_reports()
    reports = db.get_missing_reports(reports)
    print(reports)
    parse_specific(reports)

######################
def players_from_top(server: str, boss_name: str):
    db = TopDB(server)
    q = "\n".join((
        f"SELECT guid",
        f"FROM [{boss_name}.25H]",
    ))
    return {
        int(f"0x{x}", 16)
        for x, in db.cursor.execute(q)
    }

def server_players(server):
    players = set()
    for boss in BOSSES_ICC:
        try:
            players.update(players_from_top(server, boss))
        except Exception:
            pass
    return sorted(players)

def parse_whole_top():
    for server in SERVERS_WC:
        players = server_players(server)
        GearParser(server).update_gear(players)

def argv_get_report_name(flags: list[str]):
    try:
        i = flags.index("-i") + 1
        return flags[i]
    except IndexError:
        raise ValueError("-i flag must be paired with file name string")

def main():
    import sys
    if "-i" in sys.argv:
        reports = [
            argv_get_report_name(sys.argv),
        ]
        parse_specific(reports)
        return
    
    parse_new_reports()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        LOGGER.exception("parcer wc main")
