
import gzip
import json

from constants import (
    LOGS_DIR, PATH_DIR,
    bytes_read, bytes_write, get_folders_filter, json_read, json_write, new_folder_path, running_time)

TOP = new_folder_path(PATH_DIR, 'top')

import os

pathjoin = os.path.join

TOP_FILE = 'top.json'
THREADS = []

def new_request(q):
    print(q)
    server = q.get("server", "Lordaeron")
    server_folder = new_folder_path(TOP, server)
    fname = f"{q.get('boss')} {q.get('diff')}.gzip"
    p = pathjoin(server_folder,fname)
    return bytes_read(p)

@running_time
def make_gzip(data, level=5):
    return gzip.compress(data, compresslevel=level)

@running_time
def make_json_bytes(data):
    return json.dumps(data, separators=(',', ':'), ).encode()

@running_time
def _sort(data: dict):
    return sorted(data.values(), key=lambda x: x['ud'], reverse=True)

def add_to_d(top: dict, data: list[dict[str, str]]):
    for item in data:
        report_id = item['r'].rsplit('--', 3)[0]
        player_id = f"{report_id}-{item['i']}"
        cached_report = top.get(player_id)
        if not cached_report or cached_report['ud'] < item['ud']:
            top[player_id] = item

def main_make(server="Icecrown"):
    server_folder = new_folder_path(TOP, server)

    TOP_D: dict[str, dict[str, dict]] = {}

    folders = get_folders_filter(server)
    for folder in folders:
        print(folder)
        __folder = pathjoin(LOGS_DIR, folder)
        top = pathjoin(__folder, TOP_FILE)
        j = json_read(top)
        for boss_name, diffs in j.items():
            for diff, data in diffs.items():
                boss_f_n = f"{boss_name} {diff}"
                d_b = TOP_D.setdefault(boss_f_n, {})
                add_to_d(d_b, data)

    for boss_f_n, data in TOP_D.items():
        data = list(data.values())
        data = make_json_bytes(data)
        data_gzip = make_gzip(data, 5)
        bpath = pathjoin(server_folder, f"{boss_f_n}.gzip")
        bytes_write(bpath, data_gzip)


if __name__ == "__main__":
    main_make()
