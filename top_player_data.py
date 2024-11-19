
from datetime import timedelta

from api_top_db_v2 import TopDBCached
from c_player_classes import CLASSES_LIST
from c_server_phase import get_server_phase
from h_debug import running_time


class PlayerInfo:
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
            f"Name: {self.name:12}",
            f"Class: {CLASSES_LIST[self.class_i]:12}",
            f"Spec: {self.spec}",
        ))


class PlayerData(dict[str, PlayerInfo]):
    def __missing__(self, guid):
        v = self[guid] = PlayerInfo(guid, f"Unknown-{guid}", 0)
        return v

    def has_latest_info(self, guid, name, spec):
        _current = self.get(guid)
        return _current and _current.name == name and _current.spec == spec

    def add_new_data(self, boss_rows: tuple[str]):
        for _, guid, name, spec in boss_rows:
            if self.has_latest_info(guid, name, spec):
                player = self.get(guid)
            else:
                player = PlayerInfo(guid, name, spec)

            self[guid] = self[name] = player


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
        query = '\nUNION\n'.join((
            encounter.query_players_data()
            for encounter in self.phase.ALL_BOSSES
        ))
        rows = self.cursor.execute(query)
        players = PlayerData()
        players.add_new_data(rows)
        return players


def test1():
    test_players = [
        ("0238FF1", "Zaha"),
        ("0479745", "Stefaka"),
    ]
    # q = PlayerDataServer("Icecrown")
    q = PlayerDataServer("Lordaeron")
    for player_guid, player_name in test_players:
        p = q.player_info(player_guid)
        print(p)
        print(p == q.player_info(player_name))


if __name__ == "__main__":
    test1()
