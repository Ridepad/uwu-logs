
import gzip
import json
import os

from constants import (
    LOGS_DIR, TOP_DIR,
    bytes_read, bytes_write, get_folders_filter, json_read, new_folder_path, running_time)

TOP_FILE = 'top.json'

def new_request(q: dict):
    server = q.get("server")
    if not server:
        return b''
    
    server_folder = new_folder_path(TOP_DIR, server)
    fname = f"{q.get('boss')} {q.get('diff')}.gzip"
    p = os.path.join(server_folder, fname)
    return bytes_read(p)

# @running_time
def make_gzip(data, level=5):
    return gzip.compress(data, compresslevel=level)

# @running_time
def make_json_bytes(data):
    return json.dumps(data, separators=(',', ':'), ).encode()

@running_time
def _sort(data: dict):
    return sorted(data.values(), key=lambda x: x['ud'], reverse=True)

@running_time
def save_tops(top: dict, server):
    server_folder = new_folder_path(TOP_DIR, server)
    for boss_f_n, data in top.items():
        data = list(data.values())
        data = make_json_bytes(data)
        data_gzip = make_gzip(data, 5)
        bpath = os.path.join(server_folder, f"{boss_f_n}.gzip")
        bytes_write(bpath, data_gzip)

def get_player_id(item: dict[str, str]):
    report_id = item['r'].rsplit('--', 3)[0]
    return f"{report_id}-{item['i']}"

def add_to_d(top: dict, data: list[dict[str, str]], forced=False):
    for item in data:
        player_id = get_player_id(item)
        cached_report = top.get(player_id)
        if forced or not cached_report or cached_report['ud'] < item['ud']:
            top[player_id] = item

def top_add(top: dict[str, dict[str, dict]], report_id):
    report_folder = os.path.join(LOGS_DIR, report_id)
    top_file = os.path.join(report_folder, TOP_FILE)
    j = json_read(top_file)
    for boss_name, diffs in j.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            d_b = top.setdefault(boss_f_n, {})
            add_to_d(d_b, data)

def main_make_from_zero(server):
    reports = get_folders_filter(server)

    TOP_D: dict[str, dict[str, dict]] = {}
    for folder in reports:
        print(folder)
        top_add(TOP_D, folder)

    save_tops(TOP_D, server)

def gzip_read(path):
    f = bytes_read(path, ext="gzip")
    if not f:
        return {}
    g = gzip.decompress(f)
    data = json.loads(g)
    return {get_player_id(item): item for item in data}

def main_add_new_reports(server: str, reports: list[str]):
    TOP_D: dict[str, dict[str, dict]] = {}
    new_reports = [report for report in reports if server in report]
    for report in new_reports:
        top_add(TOP_D, report)
    # print(TOP_D['Sindragosa 25H'])

    new_top = {}
    
    server_folder = new_folder_path(TOP_DIR, server)
    for boss_f_n, data in TOP_D.items():
        top_path = os.path.join(server_folder, boss_f_n)
        cached_top = gzip_read(top_path)
        new_top[boss_f_n] = cached_top
        new_list = data.values()
        add_to_d(cached_top, new_list)

    save_tops(new_top, server)

def main_add_new_reports_wrap(reports: list[str]):
    grouped_reports = {}
    for report in reports:
        server = report.rsplit('--', 1)[-1]
        grouped_reports.setdefault(server, []).append(report)
        
    for server, reports in grouped_reports.items():
        main_add_new_reports(server, reports)


@running_time
def main_top_add_new(report_id: str, forced=False):
    TOP_D: dict[str, dict[str, dict]] = {}
    server = report_id.rsplit('--', 1)[-1]
    server_folder = new_folder_path(TOP_DIR, server)
    
    report_folder = os.path.join(LOGS_DIR, report_id)
    top_file = os.path.join(report_folder, TOP_FILE)
    j = json_read(top_file)
    for boss_name, diffs in j.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            print(boss_f_n)
            top_path = os.path.join(server_folder, boss_f_n)
            d_b = TOP_D[boss_f_n] = gzip_read(top_path)
            add_to_d(d_b, data, forced)

    save_tops(TOP_D, server)

@running_time
def main_top_delete(report_id: str):
    TOP_D: dict[str, dict[str, dict]] = {}
    server = report_id.rsplit('--', 1)[-1]
    server_folder = new_folder_path(TOP_DIR, server)
    
    report_folder = os.path.join(LOGS_DIR, report_id)
    top_file = os.path.join(report_folder, TOP_FILE)
    j = json_read(top_file)
    for boss_name, diffs in j.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            print(boss_f_n)
            top_path = os.path.join(server_folder, boss_f_n)
            _top = TOP_D[boss_f_n] = gzip_read(top_path)
            for item in data:
                player_id = get_player_id(item)
                if player_id in _top:
                    del _top[player_id]

    save_tops(TOP_D, server)


if __name__ == "__main__":
    # _reports = {
    #     "22-08-13--19-57--Sherbet--Lordaeron":"Done!",
    #     "22-08-13--20-33--Veriet--Lordaeron":"Done!",
    #     "22-08-13--23-02--Sherbet--Lordaeron": "123",
    # }
    # main_add_new_reports_wrap(_reports)
    # main_top_add_new("22-08-05--19-43--Jenbrezul--Lordaeron")
    # main_make_from_zero("Lordaeron")
    main_top_add_new("21-11-22--20-25--Snowinice--Icecrown", forced=True)
    main_top_add_new("21-11-29--19-45--Snowstriker--Icecrown", forced=True)
    main_top_delete("21-10-20--19-42--Xtan--Lordaeron")
    # main_top_delete("21-11-22--20-25--Snowinice--Icecrown")
    # main_top_delete("21-11-29--19-45--Snowstriker--Icecrown")
    # main_make("Icecrown")
