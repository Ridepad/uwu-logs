from collections import defaultdict
import concurrent.futures
import gzip
import json
import os
import subprocess
from sys import platform
from time import perf_counter

import constants
import file_functions
import logs_top
from constants import (
    LOGGER_UPLOADS, LOGS_DIR, LOGS_RAW_DIR, PATH_DIR, TOP_DIR, UPLOADS_TEXT,
    get_ms_str, get_report_name_info,
)

TOP_FILE = 'top.json'
USEFUL_DAMAGE = 'ud'

if platform.startswith("linux"):
    EXE_7Z = os.path.join(PATH_DIR, "7zz")
elif platform == "win32":
    EXE_7Z = os.path.join(PATH_DIR, "7z.exe")
else:
    raise RuntimeError("Unsupported OS")

def save_raw_logs(file_name: str):
    report_id, ext = os.path.splitext(file_name)
    logs_txt_path = os.path.join(UPLOADS_TEXT, file_name)
    if not os.path.isfile(logs_txt_path):
        return
    
    pc = perf_counter()
    archive_path = os.path.join(LOGS_RAW_DIR, f"{report_id}.7z")
    if os.path.isfile(archive_path):
        os.remove(archive_path)
    cmd = [EXE_7Z, 'a', archive_path, logs_txt_path, '-m0=PPMd', '-mo=11', '-mx=9']
    return_code = subprocess.call(cmd)
    if return_code == 0:
        os.remove(logs_txt_path)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {report_id:50} | Saved raw')
    

def data_gen(report_id: str):
    report_folder = os.path.join(LOGS_DIR, report_id)
    top_file = os.path.join(report_folder, TOP_FILE)
    TOP: dict[str, dict[str, list[dict]]] = file_functions.json_read(top_file)
    for boss_name, diffs in TOP.items():
        for diff, data in diffs.items():
            boss_f_n = f"{boss_name} {diff}"
            yield boss_f_n, data

def save_temp_top(report_id):
    pc = perf_counter()
    server = get_report_name_info(report_id)["server"]
    SERVER_FOLDER = os.path.join(TOP_DIR, server)
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

def update_top(top: dict[str, dict], new_data):
    modified = False
    for player_id, item in __data_gen(new_data):
        cached_report = top.get(player_id)
        if cached_report and cached_report[USEFUL_DAMAGE] > item[USEFUL_DAMAGE]:
            continue
        modified = True
        top[player_id] = item
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
    pc = perf_counter()
    data = sorted(data.values(), key=lambda x: x["t"])

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
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {boss_f_n:50} | {modified}')

def top_grouped():
    for server_folder_name in next(os.walk(TOP_DIR))[1]:
        full_server_folder_name = os.path.join(TOP_DIR, server_folder_name)
        grouped_json_files = group_by_top_file(full_server_folder_name)
        for boss_f_n, json_files in grouped_json_files.items():
            yield full_server_folder_name, boss_f_n, json_files


def main():
    if not os.path.isdir(UPLOADS_TEXT):
        return
    
    RAW_LOGS = next(os.walk(UPLOADS_TEXT))[2]
    if not RAW_LOGS:
        return
    
    RAW_LOGS_NO_EXT = [os.path.splitext(fpath)[0] for fpath in RAW_LOGS]
    MAX_CPU = max(os.cpu_count() - 1, 1)

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for report_id in RAW_LOGS_NO_EXT:
            executor.submit(logs_top.make_report_top_wrap, report_id)

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for report_id in RAW_LOGS_NO_EXT:
            executor.submit(save_temp_top, report_id)
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        for _data in top_grouped():
            executor.submit(top_add_new_data, *_data)
    
    if not os.path.exists(LOGS_RAW_DIR):
        os.makedirs(LOGS_RAW_DIR, exist_ok=True)
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.map(save_raw_logs, RAW_LOGS)

def main_wrap():
    pc = perf_counter()
    try:
        main()
        LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | Auto finish')
    except Exception:
        LOGGER_UPLOADS.exception(f'{get_ms_str(pc)} | Auto error')

if __name__ == '__main__':
    main_wrap()
