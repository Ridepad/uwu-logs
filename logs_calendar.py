import calendar
import os
import json
import shutil
from collections import defaultdict
from typing import TypedDict

import pandas

import file_functions
import logs_main
from constants import LOGS_DIR, PATH_DIR, get_report_name_info, running_time

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

    reports_by_day = defaultdict(set)
    for data in df.itertuples():
        day_key = (f"{data[i_month]:0>2}-{data[i_day]:0>2}")
        formatted_report_info = f"{data[i_time]} | {data[i_server]} | {data[i_author]}"
        reports_by_day[day_key].add((data[0], formatted_report_info))
    
    return {k: sorted(v) for k, v in reports_by_day.items()}

@running_time
def get_logs_list_filter_json(_filter):
    df = get_logs_list_df()
    df = get_logs_list_df_filter(df, _filter)
    return json.dumps(list(df.index))

def get_logs_list_df_filter_to_calendar_wrap(_filter):
    df = get_logs_list_df()
    _filter = normalize_filter(_filter)
    df = get_logs_list_df_filter(df, _filter)
    return separate_to_days(df)



def make_new(folders: list[str]):
    if not folders:
        return
    
    data = {}
    for report_id in folders:
        report = logs_main.THE_LOGS(report_id)
        if not os.path.isfile(report.relative_path("PLAYERS_DATA.json")):
            continue
        if not os.path.isfile(report.relative_path("ENCOUNTER_DATA.json")):
            continue
        try:
            report_name_info = get_report_name_info(report_id)
            date = map(int, report_name_info["date"].split("-"))
            date = dict(zip(("year", "month", "day"), date))
            data[report_id] = date | {
                "time": report_name_info["time"].replace("-", ":"),
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

def add_new_logs(folders: list[str]=None):
    df = get_logs_list_df()
    if folders is None:
        folders = os.listdir(LOGS_DIR)
    folders = (set(folders) - set(df.index))
    new_df = make_new(folders)
    if new_df is None:
        return
    
    df = pandas.concat([df, new_df])
    df.sort_index()
    _save_df_with_backup(df)
