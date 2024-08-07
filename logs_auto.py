'''
This file runs in a cron job on the server.
Example (every minute with a lock):
*/1 * * * * /usr/bin/flock -n /tmp/fcj.lockfile /usr/bin/python3 /home/uwu-logs/logs_auto.py

For testing, run it when needed manually.
'''

import itertools
import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter

import logs_calendar
import logs_top
import logs_top_db
import api_7z
from constants import (
    DEFAULT_SERVER_NAME,
    TOP_FILE_NAME,
)
from c_path import Directories
from h_debug import Loggers, get_ms_str
from h_other import get_report_name_info

LOGGER_UPLOADS = Loggers.uploads


def remove_old_dublicate(report_id: str):
    if DEFAULT_SERVER_NAME in report_id:
        return
    
    _server = get_report_name_info(report_id)["server"]
    report_id_old = report_id.replace(_server, DEFAULT_SERVER_NAME)
    archive_path_old = Directories.archives.joinpath(f"{report_id_old}.7z")
    if archive_path_old.is_file():
        archive_path_old.unlink()

def save_raw_logs(report_id: str):
    pending_text = Directories.pending_archive / f"{report_id}.txt"
    if not pending_text.is_file():
        return
    
    pc = perf_counter()
    Directories.archives.mkdir(exist_ok=True)
    archive_path = Directories.archives / f"{report_id}.7z"
    archive = api_7z.SevenZipArchive(archive_path)
    return_code = archive.create(pending_text)
    if return_code == 0:
        pending_text.unlink()
        remove_old_dublicate(report_id)
        LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {report_id:50} | Saved raw')
        return
    
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {report_id:50} | ERROR {return_code}')

def _report_server(report_id: str):
    return get_report_name_info(report_id)["server"]

def add_new_top_data(server, reports):
    top_data: dict[str, dict[str, list[dict]]]

    pc = perf_counter()

    _data = defaultdict(list)
    for report_id in reports:
        top_file = Directories.logs.joinpath(report_id, TOP_FILE_NAME)
        top_data = top_file._json()
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

    # needs player and encounter data, thats why after logs top
    logs_calendar.add_new_logs(new_logs)
    
    for server, reports in group_reports_by_server(new_logs):
        add_new_top_data(server, reports)
    
    with ProcessPoolExecutor(max_workers=MAX_CPU) as executor:
        executor.map(save_raw_logs, new_logs)

def main():
    if not Directories.pending_archive.is_dir():
        return
    
    NEW_LOGS = [
        file_path.stem
        for file_path in Directories.pending_archive.iterdir()
        if file_path.suffix == ".txt"
    ]
    if not NEW_LOGS:
        return

    main_proccess_pool(NEW_LOGS)
    # main_sequential(NEW_LOGS)

    api_7z.SevenZip().download()


    for report_id in NEW_LOGS:
        tz_path = Directories.pending_archive / f"{report_id}.timezone"
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
