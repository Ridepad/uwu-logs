import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Union

from pydantic import BaseModel, field_validator

from api_top_db_v2 import (
    TopDB,
    TopDBCached,
    TopDataCompressed,
)
from c_path import Directories
from c_server_phase import get_server_phase
from h_debug import running_time
from h_other import sort_dict_by_value
from h_server_fix import server_cnv
from top_player_data import PlayerDataServer


API_EXAMPLES = [
    {
        "server": "Lordaeron",
        "class_i": "5",
        "spec_i": "3",
    },
]



###############################################
# rank   100 # = 9901 = 10000-(  100-    1)*1.0
# rank   200 # = 9811 =  9901-(  200-  100)*0.9
# rank   300 # = 9731 =  9811-(  300-  200)*0.8
# rank   400 # = 9661 =  9731-(  400-  300)*0.7
# rank   500 # = 9601 =  9661-(  500-  400)*0.6
# rank  1000 # = 9351 =  9601-( 1000-  500)*0.5
# rank  2000 # = 8951 =  9351-( 2000- 1000)*0.4
# rank 10000 # = 6551 =  8951-(10000- 2000)*0.3
# rank 75000 # =   51 =  6551-(75000-10000)*0.1
################################################
# delta(rank_n) = (upper_rank_threshold - rank_n) * upper_rank_decrease
# points_upper_rank_threshold = points_lower_rank_threshold - delta(lower_rank_threshold)
# points(rank_n) = points_upper_threshold + delta(rank_n)

RANKS_PENALTY = (
    (  100, 0.0001),
    (  200, 0.00009),
    (  300, 0.00008),
    (  400, 0.00007),
    (  500, 0.00006),
    ( 1000, 0.00005),
    ( 2000, 0.00004),
    (10000, 0.00003),
    (75000, 0.00001),
    (10**9, 0.0),
)

class RankFormula:
    __slots__ = "points", "rank_threshold", "per_rank"

    def __init__(self) -> None:
        self.points = 1.0
        self.rank_threshold = 1
        self.per_rank = 0.0

    @staticmethod
    def __new_threshold(rank):
        points_threshold = 1.0
        previous_rank_threshold = 1
        for next_rank_threshold, per_rank in RANKS_PENALTY:
            points_threshold = points_threshold + previous_rank_threshold * per_rank
            if rank < next_rank_threshold:
                return points_threshold, next_rank_threshold, per_rank
            points_threshold = points_threshold - next_rank_threshold*per_rank
            previous_rank_threshold = next_rank_threshold
        
        return 0.0, 10**9, 0.0

    def __call__(self, rank):
        if rank > self.rank_threshold:
            self.points, self.rank_threshold, self.per_rank = self.__new_threshold(rank)
        return self.points - rank * self.per_rank




@dataclass
class Player:
    __slots__ = "player_rank", "raid_rank", "dps", "player_raid_id", "raids"
    player_rank: int
    raid_rank: int
    dps: float
    player_raid_id: str
    raids: int

    def as_dict(self):
        return {
            "raid_id": self.player_raid_id,
            "rank_raids": self.raid_rank,
            "rank_players": self.player_rank,
            "dps_max": self.dps,
            "raids": self.raids,
        }


@dataclass
class PlayerPoints:
    __slots__ = "player_rank", "raid_rank", "dps"
    player_rank: int
    raid_rank: int
    dps: float

    def __iter__(self):
        yield self.player_rank
        yield self.raid_rank
        yield self.dps

    def as_dict(self):
        return {
            "points": max(self) * 10000,
            "points_dps": self.dps * 10000,
            "points_rank_players": self.player_rank * 10000,
            "points_rank_raids": self.raid_rank * 10000,
        }


class BossDataBySpec(TopDB):
    def __init__(self, server: str, db_query: str) -> None:
        super().__init__(server)
        self.db_query = db_query

    @property
    def raids_amount(self):
        try:
            return self.__raids_amount
        except AttributeError:
            self._renew_data_from_db()
            return self.__raids_amount

    @property
    def players(self):
        try:
            return self.__players
        except AttributeError:
            self._renew_data_from_db()
            return self.__players

    @property
    def default_values(self):
        try:
            return self.__default_values
        except AttributeError:
            pass
        
        rank_1 = next(iter(self.players.values()))
        self.__default_values = {
            "spec_total_players": len(self.players),
            "spec_total_raids": self.raids_amount,
            "spec_r1_dps": rank_1.dps,
        }
        return self.__default_values
    
    @property
    def points(self) -> dict[str, PlayerPoints]:
        try:
            return self.__points
        except AttributeError:
            pass
        
        if not self.players:
            self.__points = {}
            return self.__points

        top1dps = next(iter(self.players.values())).dps
        
        # number_of_players = len(self.players)
        # number_of_raids = self.__raids_amount
        
        number_of_players = min(10000, len(self.players))
        players_1_less = max(1, number_of_players - 1)
        # print('>>>> number_of_players', number_of_players, players_1_less)
        # players_1_more = number_of_players + 1

        number_of_raids = self.raids_amount
        # ratio = self.__raids_amount / len(self.players) / 2
        # number_of_raids = min(int(10000*ratio), self.__raids_amount)
        # number_of_raids = min(10000, self.__raids_amount)
        raids_1_less = max(1, number_of_raids - 1)
        # raids_1_more = number_of_raids + 1
        if self.raids_amount < 10000:
            raid_rank = lambda rank: (number_of_raids - rank) / raids_1_less
        else:
            raid_rank = RankFormula()
        
        self.__points = {
            guid: PlayerPoints(
                (number_of_players - player.player_rank) / players_1_less,
                raid_rank(player.raid_rank),
                # (number_of_raids - player.raid_rank) / raids_1_less,
                # players_1_more / (number_of_players + player.player_rank),
                # raids_1_more / (number_of_raids + player.raid_rank),
                player.dps / top1dps,
            )
            for guid, player in self.players.items()
        }

        return self.__points

    def player_data(self, guid):
        try:
            return self._player_data(guid)
        except KeyError:
            return {}

    def _player_data(self, guid):
        player = self.players[guid]
        player_points = self.points[guid]
        
        d = {}
        d.update(player.as_dict())
        d.update(player_points.as_dict())
        d.update(self.default_values)
        return d
    
    # @running_time
    def _renew_data_from_db(self):
        try:
            dps_data = self.cursor.execute(self.db_query)
        except Exception:
            dps_data = [] 

        PLAYERS: dict[str, Player] = {}
        current_raid_rank = 0
        current_player_rank = 0
        for current_raid_rank, (player_raid_id, dps) in enumerate(dps_data, 1):
            guid = player_raid_id[-7:]
            if guid in PLAYERS:
                PLAYERS[guid].raids += 1
                continue
            
            current_player_rank += 1
            PLAYERS[guid] = Player(
                current_player_rank,
                current_raid_rank,
                dps,
                player_raid_id,
                1,
            )
        
        self.__players = PLAYERS
        self.__raids_amount = current_raid_rank


class ServerSpecData(dict[str, BossDataBySpec]):
    def __init__(self, server, spec) -> None:
        self.phase = get_server_phase(server)
        for encounter in self.phase.ALL_BOSSES:
            db_query = encounter.query_dps(spec)
            self[encounter.table_name] = BossDataBySpec(server, db_query)
    
    @property
    def total_points(self):
        try:
            return self.__total_points
        except AttributeError:
            self.__total_points = self._calc_total_points()
            return self.__total_points
    
    @property
    def points_rank_1(self):
        try:
            return self.__points_rank_1
        except AttributeError:
            if self.total_points:
                self.__points_rank_1 = next(iter(self.total_points.values()))
            else:
                self.__points_rank_1 = 1.0
            return self.__points_rank_1
        
    def get_player_rank(self, guid: str):
        rank = 0
        for rank, _guid in enumerate(self.total_points, 1):
            if _guid == guid:
                return rank
        return rank
    
    def get_player_overall_points(self, guid: str):
        _total = self.total_points.get(guid) or 0
        return _total / self.points_rank_1 * 10000

    @running_time
    def _calc_total_points(self) -> dict[str, float]:
        z = defaultdict(int)
        for encounter in self.phase.FOR_POINTS:
            boss_data = self[encounter.table_name]
            for player_guid, player_points in boss_data.points.items():
                z[player_guid] += max(player_points)
        for guid, v in z.items():
            z[guid] = v * 10000
        return sort_dict_by_value(z)


class PointsServer(TopDBCached):
    cache: dict[str, dict[int, ServerSpecData]] = defaultdict(dict)
    
    def get_spec_data(self, spec_i):
        if spec_i not in range(40):
            raise ValueError("Wrong spec index")
        
        server_data = self.cache[self.server]
        if self.db_was_updated():
            server_data = self.cache[self.server] = {}
        
        if spec_i not in server_data:
            server_data[spec_i] = ServerSpecData(self.server, spec_i)
        
        return server_data[spec_i]














class PointsValidation(BaseModel):
    server: str
    class_i: int
    spec_i: int

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

    @field_validator('class_i')
    @classmethod
    def validate_class_i(cls, class_i: Union[str, int]):
        class_i = int(class_i)
        if class_i not in range(10):
            raise ValueError("[class_i] value must be from 0 to 9")
        return class_i

    @field_validator('spec_i')
    @classmethod
    def validate_spec_i(cls, spec_i: Union[str, int]):
        spec_i = int(spec_i)
        if spec_i not in {1, 2, 3}:
            raise ValueError("[spec_i] value must be from [1, 2, 3]")
        return spec_i


class Points(TopDBCached):
    cache: defaultdict[str, dict[int, TopDataCompressed]] = defaultdict(dict)

    def __init__(self, model: PointsValidation) -> None:
        super().__init__(model.server)
        self.spec_i = model.class_i * 4 + model.spec_i
    
    @running_time
    def parse_top_points(self):
        server_data = self.cache[self.server]
        if self.db_was_updated():
            server_data = self.cache[self.server] = {}
        
        if self.spec_i not in server_data:
            server_data[self.spec_i] = self._new_compressed_data()
            
        return server_data[self.spec_i]
    
    def _new_compressed_data(self):
        a = self._make_top()
        j = json.dumps(a, separators=(",", ":"))
        return TopDataCompressed(j.encode())

    def _make_top(self):
        player_data = PlayerDataServer(self.server)
        spec_data = PointsServer(self.server).get_spec_data(self.spec_i)
        player_points = spec_data.total_points
        points_rank_1 = spec_data.points_rank_1
        return [
            [
                player_data.name(guid),
                round(points / points_rank_1 * 100, 3),
                int(points),
            ]
            for guid, points in player_points.items()
        ]


def _test1():
    conf = API_EXAMPLES[0]
    q = PointsValidation(**conf)
    z = Points(q)
    for x in z._make_top()[:5]:
        print(x)

if __name__ == "__main__":
    _test1()
