import calendar
import os
import json
import shutil
from collections import defaultdict
from typing import TypedDict
from datetime import datetime

import pandas
import pytz

import file_functions
import logs_main
from constants import (
    DEFAULT_SERVER_NAME,
    LOGS_DIR,
    PATH_DIR,
    UPLOADS_TEXT,
    get_report_name_info,
    running_time,
)

CALENDAR = calendar.Calendar()

def get_calend_days(y, m):
    this_month = CALENDAR.monthdatescalendar(y, m)
    return [
        [
            (cell.strftime("%m-%d"), cell.day)
            for cell in row
        ]
        for row in this_month
    ]


TEST_FOLDER = file_functions.new_folder_path(PATH_DIR, "_test")

DF_MAIN_NAME = "_logs_list"
DF_MAIN_EXT = "pkl"
DF_MAIN_FULL_NAME = f"{DF_MAIN_NAME}.{DF_MAIN_EXT}"
DF_MAIN_PATH = os.path.join(PATH_DIR, DF_MAIN_FULL_NAME)

class DF_TYPE(TypedDict):
    df: pandas.DataFrame
    last_mtime: float

DF_MAIN_DATA: DF_TYPE = {
    "df": pandas.DataFrame(),
    "last_mtime": 0.0,
}
COLUMN_TYPES = {
    "year": "int8",
    "month": "int8",
    "day": "int8",
    # "time": "string",
    # "author": "string",
    # "server": "string",
    # "players": "string",
    # "fights": "string",
}

@running_time
def _read_df(path) -> pandas.DataFrame:
    try:
        return pandas.read_pickle(path)
    except FileNotFoundError:
        return pandas.DataFrame()

@running_time
def _save_df(df: pandas.DataFrame, path, comp=None):
    df.to_pickle(path, compression=comp)

def _save_df_with_backup(df: pandas.DataFrame):
    PATH_BKP = os.path.join(PATH_DIR, f"{DF_MAIN_NAME}.bkp")
    PATH_TMP = os.path.join(PATH_DIR, f"{DF_MAIN_NAME}.tmp")

    if os.path.isfile(DF_MAIN_PATH):
        shutil.copy2(DF_MAIN_PATH, PATH_BKP)
    _save_df(df, PATH_TMP)
    
    DF_MAIN_DATA["df"] = df
    DF_MAIN_DATA["last_mtime"] = file_functions.get_mtime(PATH_TMP)
    
    os.replace(PATH_TMP, DF_MAIN_PATH)


def get_logs_list_df():
    current_mtime = file_functions.get_mtime(DF_MAIN_PATH)
    if current_mtime > DF_MAIN_DATA["last_mtime"]:
        DF_MAIN_DATA["df"] = _read_df(DF_MAIN_PATH)
        DF_MAIN_DATA["last_mtime"] = current_mtime
    return DF_MAIN_DATA["df"]

def df_filter_by(df: pandas.DataFrame, category: str, filter_by):
    try:
        filter_by = int(filter_by)
        return df[df[category] == filter_by]
    except ValueError:
        return df[df[category].apply(lambda x: filter_by in x)]

def normalize_filter(filter: dict):
    df = get_logs_list_df()
    return {k:v for k,v in filter.items() if v and k in df.columns}

@running_time
def get_logs_list_df_filter(df: pandas.DataFrame, filter: dict):
    for f, v in filter.items():
        df = df_filter_by(df, f, v)
        if df.empty:
            break
    return df

def separate_to_days(df: pandas.DataFrame):
    if df.empty:
        return {}
    # ['year', 'month', 'day', 'time', 'author', 'server', 'player', 'fight']
    columns = list(df.columns)
    i_day = columns.index("day") + 1
    i_month = columns.index("month") + 1
    i_time = columns.index("time") + 1
    i_server = columns.index("server") + 1
    i_author = columns.index("author") + 1

    reports_by_day = defaultdict(list)
    for data in df.itertuples():
        day_key = f"{data[i_month]:0>2}-{data[i_day]:0>2}"
        formatted_report_info = f"{data[i_time]} | {data[i_server]} | {data[i_author]}"
        reports_by_day[day_key].append((data[0], formatted_report_info))
    
    return reports_by_day

@running_time
def get_logs_list_filter_json(_filter):
    df = get_logs_list_df()
    df = get_logs_list_df_filter(df, _filter)
    df.sort_values(by="time")
    return json.dumps(list(df.index))

def get_logs_list_df_filter_to_calendar_wrap(_filter):
    df = get_logs_list_df()
    _filter = normalize_filter(_filter)
    df = get_logs_list_df_filter(df, _filter)
    return separate_to_days(df)

def get_timezone_file(report_id):
    return os.path.join(UPLOADS_TEXT, f"{report_id}.timezone")

def get_timezone(report_id):
    tz_path = get_timezone_file(report_id)
    timezone_str = file_functions.file_read(tz_path)
    try:
        return pytz.timezone(timezone_str)
    except (ValueError, pytz.exceptions.UnknownTimeZoneError):
        return pytz.utc

def get_datetime(report_id):
    _info = get_report_name_info(report_id)
    date_str = f'{_info["date"]}--{_info["time"]}'
    return datetime.strptime(date_str, "%y-%m-%d--%H-%M")

def convert_timezone(report_id):
    timezone = get_timezone(report_id)
    dt_current = get_datetime(report_id)
    dt = timezone.normalize(timezone.localize(dt_current)).astimezone(pytz.utc)
    return {
        "year": dt.year%1000,
        "month": dt.month,
        "day": dt.day,
        "time": dt.strftime("%H:%M"),
    }

def make_new(folders: list[str]):
    if not folders:
        return
    
    data = {}
    for report_id in folders:
        logs_dir = os.path.join(LOGS_DIR, report_id)
        if not os.path.isdir(logs_dir):
            continue
        report = logs_main.THE_LOGS(report_id)
        if not os.path.isfile(report.relative_path("PLAYERS_DATA.json")):
            continue
        if not os.path.isfile(report.relative_path("ENCOUNTER_DATA.json")):
            continue
        try:
            date = convert_timezone(report_id)
            report_name_info = get_report_name_info(report_id)
            data[report_id] = date | {
                "author": report_name_info["author"],
                "server": report_name_info["server"],
                "player": tuple(report.get_players_guids().values()),
                "fight": tuple(report.get_enc_data()),
            }
        except Exception:
            continue
    
    if not data:
        return

    return pandas.DataFrame.from_dict(data, orient="index").astype(COLUMN_TYPES)

def _get_default_server(name: str):
    _server = get_report_name_info(name)["server"]
    return name.replace(_server, DEFAULT_SERVER_NAME)

def add_new_logs(new_reports: list[str]=None):
    if new_reports is None:
        new_reports = os.listdir(LOGS_DIR)
    new_reports = set(new_reports)
    
    df = get_logs_list_df()
    df_index = set(df.index)
    
    default_copies = {
        _get_default_server(report_id)
        for report_id in new_reports
        if DEFAULT_SERVER_NAME not in report_id
    }
    default_copies = default_copies & df_index

    folders = new_reports - df_index
    new_df = make_new(folders)
    if new_df is None and not default_copies:
        return
    
    df.drop(default_copies, inplace=True)
    df = pandas.concat([df, new_df])
    df.sort_index()
    _save_df_with_backup(df)
