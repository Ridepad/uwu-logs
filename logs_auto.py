'''
This file runs in a cron job on the server.
Example (every minute with a lock):
*/1 * * * * /usr/bin/flock -n /tmp/fcj.lockfile /usr/bin/python3 /home/uwu-logs/logs_auto.py

For testing, run it when needed manually.
'''

import gzip
import json
import os

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter

import pandas

import file_functions
import logs_archive
import logs_calendar
import logs_top
from constants import (
    DEFAULT_SERVER_NAME,
    LOGGER_UPLOADS,
    LOGS_DIR,
    LOGS_RAW_DIR,
    TOP_DIR,
    TOP_FILE_NAME,
    PANDAS_COMPRESSION,
    UPLOADS_TEXT,
    get_ms_str,
    get_report_name_info,
)


def save_raw_logs(file_name: str):
    report_id, ext = os.path.splitext(file_name)
    logs_txt_path = os.path.join(UPLOADS_TEXT, file_name)
    if not os.path.isfile(logs_txt_path):
        return
    
    pc = perf_counter()
    archive_path = os.path.join(LOGS_RAW_DIR, f"{report_id}.7z")
    return_code = logs_archive.archive_file(archive_path, logs_txt_path)
    if return_code == 0:
        os.remove(logs_txt_path)
        if DEFAULT_SERVER_NAME not in report_id:
            _server = get_report_name_info(report_id)["server"]
            _unknown = archive_path.replace(_server, DEFAULT_SERVER_NAME)
            if os.path.isfile(_unknown):
                os.remove(_unknown)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {report_id:50} | Saved raw')

def _to_pickle(df: pandas.DataFrame, fname):
    df.to_pickle(fname, compression=PANDAS_COMPRESSION)

def data_gen(report_id: str):
    report_folder = os.path.join(LOGS_DIR, report_id)
    top_file = os.path.join(report_folder, TOP_FILE_NAME)
    TOP: dict[str, dict[str, list[dict]]] = file_functions.json_read(top_file)
    for boss_name, diffs in TOP.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            yield boss_f_n, data

def save_temp_top(report_id):
    pc = perf_counter()
    server = get_report_name_info(report_id)["server"]
    SERVER_FOLDER = file_functions.new_folder_path(TOP_DIR, server)
    for boss_f_n, data in data_gen(report_id):
        _path = f"{boss_f_n}--{report_id}.json"
        full_path = os.path.join(SERVER_FOLDER, _path)
        file_functions.json_write(full_path, data, indent=None, sep=(',', ':'))
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {report_id:50} | New temp top')
    

def get_player_id(item: dict[str, str]):
    report_name = item['r']
    player_guid = item['i'][-7:]
    report_date = get_report_name_info(report_name)["date"]
    return f"{report_date}-{player_guid}"

def get_boss_top(server_folder: str, boss_f_n: str) -> list[dict]:
    if not os.path.isdir(server_folder):
        server_folder = os.path.join(TOP_DIR, server_folder)
    top_path = os.path.join(server_folder, boss_f_n)
    f = file_functions.bytes_read(top_path, ext="gzip")
    if not f:
        return []
    g = gzip.decompress(f)
    return json.loads(g)

def get_boss_top_wrap(server_folder: str, boss_f_n: str):
    _top = get_boss_top(server_folder, boss_f_n)
    return {get_player_id(item): item for item in _top}

def __data_gen_list(new_data: list[dict[str, str]]):
    for item in new_data:
        player_id = get_player_id(item)
        yield player_id, item

def __data_gen_dict(new_data: dict[str, dict[str, str]]):
    for player_id, item in new_data.items():
        yield player_id, item

def __data_gen(new_data):
    if isinstance(new_data, list):
        return __data_gen_list(new_data)
    else:
        return __data_gen_dict(new_data)

def _dps(entry):
    return entry["u"] / entry["t"]

def update_top(top: dict[str, dict], new_data):
    modified = False
    for player_id, new_entry in __data_gen(new_data):
        cached_report = top.get(player_id)
        if not cached_report or _dps(new_entry) > _dps(cached_report):
            modified = True
            top[player_id] = new_entry
    return modified

def combine_jsons(json_files: list[str]):
    top = {}
    for json_file in json_files:
        _top = file_functions.json_read(json_file)
        update_top(top, _top)
    return top

def group_by_top_file(server_folder: str):
    if not os.path.isdir(server_folder):
        return {}
    
    grouped = defaultdict(list)
    for file in next(os.walk(server_folder))[2]:
        if not file.endswith(".json"):
            continue
        boss_f_n = file.split("--", 1)[0]
        full_name = os.path.join(server_folder, file)
        grouped[boss_f_n].append(full_name)

    return grouped

def save_top(server_folder: str, boss_f_n: str, data: dict[str, dict[str, str]]):
    data = sorted(data.values(), key=lambda x: x["t"])

    pc = perf_counter()
    dfpath = os.path.join(server_folder, f"{boss_f_n}.{PANDAS_COMPRESSION}")
    _to_pickle(pandas.DataFrame.from_dict(data), dfpath)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {boss_f_n:50} | Pandas saved')

    pc = perf_counter()
    top_path = os.path.join(server_folder, f"{boss_f_n}.gzip")
    top_path_tmp = f"{top_path}.tmp"
    data = json.dumps(data, separators=(',', ':'), ).encode()
    data = gzip.compress(data, compresslevel=5)
    file_functions.bytes_write(top_path_tmp, data)
    os.replace(top_path_tmp, top_path)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {boss_f_n:50} | Top saved')

def top_add_new_data(full_server_folder_name, boss_f_n, json_files):
    pc = perf_counter()
    new_top_data = combine_jsons(json_files)
    pc_get_top = perf_counter()
    current_top = get_boss_top_wrap(full_server_folder_name, boss_f_n)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc_get_top)} | {boss_f_n:50} | Cache read')
    modified = update_top(current_top, new_top_data)
    if modified:
        save_top(full_server_folder_name, boss_f_n, current_top)
    for json_file in json_files:
        if os.path.isfile(json_file):
            os.remove(json_file)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {boss_f_n:50} | Modified: {modified}')

def top_grouped():
    for server_folder_name in next(os.walk(TOP_DIR))[1]:
        full_server_folder_name = os.path.join(TOP_DIR, server_folder_name)
        grouped_json_files = group_by_top_file(full_server_folder_name)
        for boss_f_n, json_files in grouped_json_files.items():
            yield full_server_folder_name, boss_f_n, json_files


def main_sequential():
    if not os.path.isdir(UPLOADS_TEXT):
        return
    
    RAW_LOGS = [
        file_name
        for file_name in os.listdir(UPLOADS_TEXT)
        if file_name.endswith(".txt")
    ]
    if not RAW_LOGS:
        return
    
    RAW_LOGS_NO_EXT = [
        os.path.splitext(fpath)[0]
        for fpath in RAW_LOGS
    ]

    for report_id in RAW_LOGS_NO_EXT:
        logs_top.make_report_top_wrap(report_id)

    # needs player and encounter data, thats why after logs top
    logs_calendar.add_new_logs()

    for report_id in RAW_LOGS_NO_EXT:
        save_temp_top(report_id)
    
    for _data in top_grouped():
        top_add_new_data(*_data)
    
    if not os.path.exists(LOGS_RAW_DIR):
        os.makedirs(LOGS_RAW_DIR, exist_ok=True)
    
    for report_id in RAW_LOGS:
        save_raw_logs(report_id)


def main():
    if not os.path.isdir(UPLOADS_TEXT):
        return
    
    RAW_LOGS = [
        file_name
        for file_name in os.listdir(UPLOADS_TEXT)
        if file_name.endswith(".txt")
    ]
    if not RAW_LOGS:
        return
    
    RAW_LOGS_NO_EXT = [
        os.path.splitext(fpath)[0]
        for fpath in RAW_LOGS
    ]
    MAX_CPU = max(os.cpu_count() - 1, 1)

    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.map(logs_top.make_report_top_wrap, RAW_LOGS_NO_EXT)

    # needs player and encounter data, thats why after logs top
    logs_calendar.add_new_logs(RAW_LOGS_NO_EXT)

    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.map(save_temp_top, RAW_LOGS_NO_EXT)
    
    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for _data in top_grouped():
            executor.submit(top_add_new_data, *_data)
    
    if not os.path.exists(LOGS_RAW_DIR):
        os.makedirs(LOGS_RAW_DIR, exist_ok=True)
    
    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.map(save_raw_logs, RAW_LOGS)

def main_wrap():
    pc = perf_counter()
    try:
        LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | Auto start')
        main()
        LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | Auto finish')
    except Exception:
        LOGGER_UPLOADS.exception(f'{get_ms_str(pc)} | Auto error')

if __name__ == '__main__':
    main_wrap()
