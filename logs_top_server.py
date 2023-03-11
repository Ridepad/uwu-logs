import gzip
import json
import os
from collections import defaultdict

import file_functions
from constants import LOGS_DIR, TOP_DIR, running_time, get_report_name_info

TOP_FILE = 'top.json'

def new_request(request: dict):
    server = request.get("server")
    if not server:
        return b''
    
    server_folder = file_functions.new_folder_path(TOP_DIR, server)
    fname = f"{request.get('boss')} {request.get('diff')}.gzip"
    p = os.path.join(server_folder, fname)
    return file_functions.bytes_read(p)

def get_server_top_folder(server):
    return file_functions.new_folder_path(TOP_DIR, server)

def get_report_server(report_name):
    return get_report_name_info(report_name)["server"]

def get_player_id(item: dict[str, str]):
    report_name = item['r']
    player_guid = item['i']
    report_date = get_report_name_info(report_name)["date"]
    return f"{report_date}-{player_guid}"

def get_boss_top(server_folder: str, boss_f_n: str):
    top_path = os.path.join(server_folder, boss_f_n)
    f = file_functions.bytes_read(top_path, ext="gzip")
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

def data_gen(report_name: str):
    report_folder = os.path.join(LOGS_DIR, report_name)
    top_file = os.path.join(report_folder, TOP_FILE)
    TOP: dict[str, dict[str, list[dict]]] = file_functions.json_read(top_file)
    for boss_name, diffs in TOP.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            yield boss_f_n, data

def update_top(top: dict, data: list[dict[str, str]]):
    modified = False
    for item in data:
        player_id = get_player_id(item)
        cached_report = top.get(player_id)
        if not cached_report or cached_report['ud'] < item['ud']:
            modified = True
            top[player_id] = item
    return modified

def __make_top(reports):
    top: dict[str, dict[str, dict]] = {}
    for report_name in reports:
        for boss_f_n, data in data_gen(report_name):
            d_b = top.setdefault(boss_f_n, {})
            update_top(d_b, data)
    return top

def make_from_zero(server):
    reports = file_functions.get_folders_filter(server)
    TOP_D = __make_top(reports)
    save_tops(TOP_D, server)


def group_reports(reports: list[str]):
    grouped_reports = defaultdict(list)
    for report_name in reports:
        server = get_report_server(report_name)
        grouped_reports[server].append(report_name)
    return grouped_reports

def add_new_reports(server: str, reports: list[str]):
    print()
    print(server)

    new_reports = [report for report in reports if server in report]
    TOP_D = __make_top(new_reports)

    modified = False
    new_top = {}
    server_folder = file_functions.new_folder_path(TOP_DIR, server)
    for boss_f_n, data in TOP_D.items():
        print(boss_f_n)
        cached_top = get_boss_top(server_folder, boss_f_n)
        new_top[boss_f_n] = cached_top
        new_list = data.values()
        _modified = update_top(cached_top, new_list)
        if _modified:
            modified = True

    if modified:
        save_tops(new_top, server)

@running_time
def add_new_reports_wrap(reports: list[str]):
    for server, server_reports in group_reports(reports).items():
        add_new_reports(server, server_reports)


def get_boss_top_wrap(top, boss_f_n, server_folder):
    if boss_f_n in top:
        return top[boss_f_n]
    _top = top[boss_f_n] = get_boss_top(server_folder, boss_f_n)
    return _top

def remove_report(top, boss_data):
    modified = False
    for item in boss_data:
        player_id = get_player_id(item)
        if player_id in top:
            modified = True
            del top[player_id]
    return modified

@running_time
def delete_reports(server: str, reports: list[str]):
    print()
    print()
    print(server)

    modified = False
    TOP: dict[str, dict[str, dict]] = {}
    SERVER_FOLDER = get_server_top_folder(server)
    
    for report_name in reports:
        print()
        print(report_name)
        for boss_f_n, data in data_gen(report_name):
            print(boss_f_n)
            _top = get_boss_top_wrap(TOP, boss_f_n, SERVER_FOLDER)
            _modified = remove_report(_top, data)
            if _modified:
                modified = True

    if modified:
        save_tops(TOP, server)

def delete_reports_wrap(reports: list[str]):
    for server, server_reports in group_reports(reports).items():
        delete_reports(server, server_reports)


def modify_report(report_name: str, remove=False):
    modified = False
    TOP_D: dict[str, dict[str, dict]] = {}
    REPORT_SERVER = get_report_server(report_name)
    SERVER_FOLDER = get_server_top_folder(REPORT_SERVER)
    modify_function = remove_report if remove else update_top
    for boss_f_n, boss_data in data_gen(report_name):
        _top = TOP_D[boss_f_n] = get_boss_top(SERVER_FOLDER, boss_f_n)
        _modified = modify_function(_top, boss_data)
        if _modified:
            modified = True
    
    if modified:
        save_tops(TOP_D, REPORT_SERVER)
