import os
from typing import Dict
import _main
import json

from constants import running_time

def __do(logs_name: str, _all_players: Dict[str, Dict[str, str]] = {}):
    date = logs_name.split('--')[0]
    report = _main.THE_LOGS(logs_name)
    _players = report.get_players_guids()
    for guid, player_name in _players.items():
        _all_players.setdefault(guid, {}).setdefault(player_name, date)

@running_time
def __do_all():
    _all_players: Dict[str, Dict[str, str]] = {}
    
    folders = next(os.walk('./LogsDir/'))[1]
    for logs_name in folders:
        __do(logs_name, _all_players)
    
    with open("ULTIMATE_PLAYERS.json", 'w') as f:
        json.dump(_all_players, f, indent=2)

if __name__ == '__main__':
    __do_all()