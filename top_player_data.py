
from collections import defaultdict
from datetime import datetime, timedelta

from api_top_db_v2 import TopDBCached
# from c_player_classes import CLASSES_LIST
from c_player_classes import CLASSES_LIST, SPECS_LIST
from c_server_phase import get_server_phase
from h_debug import running_time


class PlayerInfo:
    # __slots__ = "name", "spec", "class_i"
    __slots__ = "guid", "name", "spec", "class_i"
    def __init__(
        self,
        guid: str,
        name: str,
        spec: int,
        class_i: int=None,
    ) -> None:
        self.guid = guid
        self.name = name
        self.spec = spec
        self.class_i = class_i or spec // 4
    
    def __str__(self) -> str:
        return " | ".join((
            f"GUID: {self.guid}",
            f"Name: {self.name}",
            f"Class: {CLASSES_LIST[self.class_i]}",
            f"Spec: {self.spec}",
        ))


class PlayerData(dict[str, PlayerInfo]):
    def __missing__(self, guid):
        v = self[guid] = PlayerInfo(guid, f"Unknown-{guid}", 0)
        return v

    def has_latest_info(self, guid, name, spec):
        _current = self.get(name)
        return _current and _current.guid == guid and _current.spec == spec

    def add_new_data(self, boss_rows: tuple[str]):
        for guid, name, spec in boss_rows:
            if self.has_latest_info(guid, name, spec):
                continue
            self[guid] = self[name] = PlayerInfo(guid, name, spec)


class PlayerDataServer(TopDBCached):
    cache: dict[str, PlayerData] = {}
    cooldown = timedelta(minutes=15)
    
    def __init__(self, server: str) -> None:
        super().__init__(server)
        self.phase = get_server_phase(server)

    def player_info(self, name_or_guid: str):
        if self.db_was_updated() or self.server not in self.cache:
            self.cache[self.server] = self._renew_data()
        return self.cache[self.server][name_or_guid]

    def name(self, name_or_guid: str):
        return self.player_info(name_or_guid).name

    @running_time
    def _renew_data(self):
        players = PlayerData()
        for encounter in self.phase.BOSSES_GET_GUID_NAME_PAIRS_FROM:
            query = encounter.query_players_data()
            rows = self.cursor.execute(query)
            players.add_new_data(rows)
        return players


def main():
    q = PlayerDataServer("Lordaeron")
    print(q.player_info("Stefaka"))
    print(q.player_info("Safiyah"))
    print(q.player_info("Meownya"))


if __name__ == "__main__":
    main()
