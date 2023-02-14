import gzip
import json
import os
from collections import defaultdict

import file_functions
from constants import LOGS_DIR, TOP_DIR, running_time

TOP_FILE = 'top.json'

def new_request(request: dict):
    server = request.get("server")
    if not server:
        return b''
    
    server_folder = file_functions.new_folder_path(TOP_DIR, server)
    fname = f"{request.get('boss')} {request.get('diff')}.gzip"
    p = os.path.join(server_folder, fname)
    return file_functions.bytes_read(p)

def get_player_id(item: dict[str, str]):
    report_id = item['r']
    player_guid = item['i']
    report_date = report_id.split('--', 1)[0]
    return f"{report_date}-{player_guid}"

def gzip_read(path):
    f = file_functions.bytes_read(path, ext="gzip")
    if not f:
        return {}
    g = gzip.decompress(f)
    data = json.loads(g)
    return {get_player_id(item): item for item in data}

@running_time
def save_tops(top: dict, server):
    print("\nSaving top for", server)
    server_folder = file_functions.new_folder_path(TOP_DIR, server)
    for boss_f_n, data in top.items():
        print(boss_f_n)
        data = list(data.values())
        data = json.dumps(data, separators=(',', ':'), ).encode()
        data = gzip.compress(data, compresslevel=5)
        bpath = os.path.join(server_folder, f"{boss_f_n}.gzip")
        file_functions.bytes_write(bpath, data)

def data_gen(report_id: str):
    report_folder = os.path.join(LOGS_DIR, report_id)
    top_file = os.path.join(report_folder, TOP_FILE)
    TOP: dict[str, dict[str, list[dict]]] = file_functions.json_read(top_file)
    for boss_name, diffs in TOP.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            yield boss_f_n, data

def update_top(top: dict, data: list[dict[str, str]], forced=False):
    changed = False
    for item in data:
        player_id = get_player_id(item)
        cached_report = top.get(player_id)
        if forced or not cached_report or cached_report['ud'] < item['ud']:
            changed = True
            top[player_id] = item
    return changed

def __make_top(reports):
    top: dict[str, dict[str, dict]] = {}
    for report_id in reports:
        for boss_f_n, data in data_gen(report_id):
            d_b = top.setdefault(boss_f_n, {})
            update_top(d_b, data)
    return top

def make_from_zero(server):
    reports = file_functions.get_folders_filter(server)
    TOP_D = __make_top(reports)
    save_tops(TOP_D, server)

def add_new_reports(server: str, reports: list[str]):
    new_reports = [report for report in reports if server in report]
    TOP_D = __make_top(new_reports)

    changed = False
    new_top = {}
    server_folder = file_functions.new_folder_path(TOP_DIR, server)
    for boss_f_n, data in TOP_D.items():
        print(boss_f_n)
        top_path = os.path.join(server_folder, boss_f_n)
        cached_top = gzip_read(top_path)
        new_top[boss_f_n] = cached_top
        new_list = data.values()
        if update_top(cached_top, new_list):
            changed = True

    if changed:
        save_tops(new_top, server)

def add_new_reports_wrap(reports: list[str]):
    grouped_reports = defaultdict(list)
    for report in reports:
        server = report.rsplit('--', 1)[-1]
        grouped_reports[server].append(report)
        
    for server, reports in grouped_reports.items():
        print()
        print(server)
        add_new_reports(server, reports)



@running_time
def add_new_single(report_id: str, forced=False):
    changed = False
    TOP_D: dict[str, dict[str, dict]] = {}
    REPORT_SERVER = report_id.rsplit('--', 1)[-1]
    SERVER_FOLDER = file_functions.new_folder_path(TOP_DIR, REPORT_SERVER)
    for boss_f_n, data in data_gen(report_id):
        top_path = os.path.join(SERVER_FOLDER, boss_f_n)
        _top = TOP_D[boss_f_n] = gzip_read(top_path)
        changed = update_top(_top, data, forced)
    
    if changed:
        save_tops(TOP_D, REPORT_SERVER)

@running_time
def delete_single(report_id: str):
    changed = False
    TOP_D: dict[str, dict[str, dict]] = {}
    REPORT_SERVER = report_id.rsplit('--', 1)[-1]
    SERVER_FOLDER = file_functions.new_folder_path(TOP_DIR, REPORT_SERVER)
    for boss_f_n, data in data_gen(report_id):
        top_path = os.path.join(SERVER_FOLDER, boss_f_n)
        _top = TOP_D[boss_f_n] = gzip_read(top_path)
        for item in data:
            player_id = get_player_id(item)
            if player_id in _top:
                changed = True
                del _top[player_id]
    
    if changed:
        save_tops(TOP_D, REPORT_SERVER)


def __test():
    # make_from_zero("Lordaeron")
    # add_new_single("21-10-20--19-42--Xtan--Lordaeron", forced=True)
    delete_single("21-10-20--19-42--Xtan--Lordaeron")

if __name__ == "__main__":
    __test()
