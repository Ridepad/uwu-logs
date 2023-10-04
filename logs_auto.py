'''
This file runs in a cron job on the server.
Example (every minute with a lock):
*/1 * * * * /usr/bin/flock -n /tmp/fcj.lockfile /usr/bin/python3 /home/uwu-logs/logs_auto.py

For testing, run it when needed manually.
'''

import itertools
import json
import os

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from time import perf_counter

import logs_top_db
import logs_archive
import logs_calendar
import logs_top
from constants import (
    DEFAULT_SERVER_NAME,
    LOGGER_UPLOADS,
    TOP_FILE_NAME,
    get_ms_str,
    get_report_name_info,
)


PATH = Path().resolve()
PATH_LOGS_DIR = PATH.joinpath("LogsDir")
PATH_LOGS_RAW_DIR = PATH.joinpath("LogsRaw")
PATH_TOP_DIR = PATH.joinpath("top")
UPLOADS_PENDING = PATH.joinpath("uploads", "0archive_pending")


def remove_old_dublicate(report_id: str):
    if DEFAULT_SERVER_NAME in report_id:
        return
    
    _server = get_report_name_info(report_id)["server"]
    report_id_old = report_id.replace(_server, DEFAULT_SERVER_NAME)
    archive_path_old = PATH_LOGS_RAW_DIR.joinpath(f"{report_id_old}.7z")
    if archive_path_old.is_file():
        archive_path_old.unlink()

def save_raw_logs(report_id: str):
    logs_txt_path = UPLOADS_PENDING.joinpath(f"{report_id}.txt")
    if not logs_txt_path.is_file():
        return
    
    pc = perf_counter()
    PATH_LOGS_RAW_DIR.mkdir(exist_ok=True)
    archive_path = PATH_LOGS_RAW_DIR.joinpath(f"{report_id}.7z")
    return_code = logs_archive.archive_file(archive_path, logs_txt_path)
    if return_code == 0:
        logs_txt_path.unlink()
        remove_old_dublicate(report_id)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {report_id:50} | Saved raw')

def _json_read(path: Path) -> dict:
    try:
        return json.loads(path.read_bytes())
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}

def _report_server(report_id: str):
    return get_report_name_info(report_id)["server"]

def add_new_top_data(server, reports):
    top_data: dict[str, dict[str, list[dict]]]

    print(server)
    pc = perf_counter()

    _data = defaultdict(list)
    for report_id in reports:
        top_file = PATH_LOGS_DIR.joinpath(report_id, TOP_FILE_NAME)
        top_data = _json_read(top_file)
        for boss_name, modes in top_data.items():
            for mode, data in modes.items():
                table_name = logs_top_db.get_table_name(boss_name, mode)
                _data[table_name].extend(data)

    logs_top_db.add_new_entries_wrap(server, _data)
    
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | Saved top | {server}')

def group_reports_by_server(new_logs):
    new_logs = sorted(new_logs, key=_report_server)
    return itertools.groupby(new_logs, key=_report_server)


def main_sequential(new_logs):
    for report_id in new_logs:
        logs_top.make_report_top_wrap(report_id)

    # needs player and encounter data, thats why after logs top
    logs_calendar.add_new_logs(new_logs)
    
    for server, reports in group_reports_by_server(new_logs):
        add_new_top_data(server, reports)
    
    for report_id in new_logs:
        save_raw_logs(report_id)


def main_proccess_pool(new_logs):
    MAX_CPU = max(os.cpu_count() - 1, 1)

    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.map(logs_top.make_report_top_wrap, new_logs)

    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.submit(logs_calendar.add_new_logs, new_logs)
        
        for server, reports in group_reports_by_server(new_logs):
            executor.submit(add_new_top_data, server, reports)
        
        executor.map(save_raw_logs, new_logs)

def main():
    if not UPLOADS_PENDING.is_dir():
        return
    
    NEW_LOGS = [
        file_path.stem
        for file_path in UPLOADS_PENDING.iterdir()
        if file_path.suffix == ".txt"
    ]
    if not NEW_LOGS:
        return

    main_proccess_pool(NEW_LOGS)
    # main_sequential(NEW_LOGS)

    for report_id in NEW_LOGS:
        tz_path = UPLOADS_PENDING.joinpath(f"{report_id}.timezone")
        if tz_path.is_file():
            tz_path.unlink()

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
