import calendar
import json
import shutil
from collections import defaultdict
from datetime import datetime

import pandas
import pytz

import logs_main
from constants import DEFAULT_SERVER_NAME
from c_path import (
    Directories,
    PathExt,
)
from h_debug import running_time
from h_other import get_report_name_info


CALENDAR = calendar.Calendar()

DF_MAIN_NAME = "_logs_list"
DF_MAIN_EXT = "pkl"
DF_MAIN_FULL_NAME = f"{DF_MAIN_NAME}.{DF_MAIN_EXT}"

DF_MAIN_PATH = Directories.main / DF_MAIN_FULL_NAME
PATH_BKP = Directories.main / f"{DF_MAIN_NAME}.bkp"
PATH_TMP = Directories.main / f"{DF_MAIN_NAME}.tmp"

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

def get_calend_days(y, m):
    this_month = CALENDAR.monthdatescalendar(y, m + 1)
    return [
        [
            (cell.strftime("%m-%d"), cell.day)
            for cell in row
        ]
        for row in this_month
    ]

@DF_MAIN_PATH.cache_until_new_self
@running_time
def _read_df(path: PathExt):
    try:
        return pandas.read_pickle(path)
    except FileNotFoundError:
        return pandas.DataFrame()

def read_main_df() -> pandas.DataFrame:
    return _read_df()

@running_time
def _save_df(df: pandas.DataFrame, path, comp=None):
    df.to_pickle(path, compression=comp)

def _save_df_with_backup(df: pandas.DataFrame):
    if DF_MAIN_PATH.is_file():
        shutil.copy2(DF_MAIN_PATH, PATH_BKP)
    _save_df(df, PATH_TMP)
    PATH_TMP.replace(DF_MAIN_PATH)

##################################################################

def df_filter_by(df: pandas.DataFrame, category: str, filter_by):
    try:
        filter_by = int(filter_by)
        return df[df[category] == filter_by]
    except ValueError:
        return df[df[category].apply(lambda x: filter_by in x)]

def normalize_filter(filter: dict):
    df = read_main_df()
    return {k:v for k,v in filter.items() if v and k in df.columns}

@running_time
def get_logs_list_df_filter(df: pandas.DataFrame, filter: dict):
    print(filter)
    for filter_key, filter_value in filter.items():
        # if filter_key == "server":
        #     df1 = df_filter_by(df, filter_key, filter_value)
        #     filter_value = filter_value.replace(" ", "-")
        #     df2 = df_filter_by(df, filter_key, filter_value)
        #     print(">>>>>>>>>> get_logs_list_df_filter")
        #     print(filter_value)
        df = df_filter_by(df, filter_key, filter_value)
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
    df = read_main_df()
    df = get_logs_list_df_filter(df, _filter)
    return json.dumps(list(df.index))

def get_logs_list_df_filter_to_calendar_wrap(_filter):
    df = read_main_df()
    if df.empty:
        return {}
    
    _filter = normalize_filter(_filter)
    df = get_logs_list_df_filter(df, _filter)
    df.sort_values(by="time", inplace=True)
    return separate_to_days(df)


##################################################################

def get_timezone_file(report_id):
    return Directories.pending_archive / f"{report_id}.timezone"

def get_timezone(report_id):
    timezone = get_timezone_file(report_id).read_text()
    try:
        return pytz.timezone(timezone)
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

def report_data(report_id: str):
    report = logs_main.THE_LOGS(report_id)
    date = convert_timezone(report_id)
    report_name_info = get_report_name_info(report_id)
    return date | {
        "author": report_name_info["author"],
        "server": report_name_info["server"],
        "player": tuple(report.get_players_guids().values()),
        "fight": tuple(report.get_enc_data()),
    }

def make_new(report_ids: list[str]):
    if not report_ids:
        return
    
    data = {}
    for report_id in report_ids:
        logs_dir = Directories.logs / report_id
        needed_files = (
            file_path.is_file()
            for file_path in [
                logs_dir / "PLAYERS_DATA.json",
                logs_dir / "ENCOUNTER_DATA.json",
            ]
        )
        if not all(needed_files):
            continue

        try:
            data[report_id] = report_data(report_id)
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
        new_reports = Directories.logs.iterdir()
    new_reports = set(new_reports)
    
    df = read_main_df()
    df_index = set(df.index)
    
    reports_copies_with_default_name = {
        _get_default_server(report_id)
        for report_id in new_reports
        if DEFAULT_SERVER_NAME not in report_id
    }
    reports_copies_with_default_name = reports_copies_with_default_name & df_index

    folders = new_reports - df_index
    new_df = make_new(folders)
    if new_df is None and not reports_copies_with_default_name:
        return
    
    df.drop(reports_copies_with_default_name, inplace=True)
    df = pandas.concat([df, new_df])
    df.sort_index()
    _save_df_with_backup(df)
