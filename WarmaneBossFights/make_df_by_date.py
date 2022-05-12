import json
import os

from pandas import DataFrame

import constants_WBF
import main_db

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
DB_PATH = os.path.join(DIR_PATH, "kill_db")
DB_DATE_PATH = os.path.join(DIR_PATH, "kill_db_date")
with open("__dates.json") as f:
    DATES = json.load(f)

def format_year_month(year: int, month: int):
    return f"{year:>02}-{month:>02}"

def next_month(year: int, month: int):
    if month > 12:
        month = 1
        year += 1
    return format_year_month(year, month)

def month_gen(date):
    return (d for d in DATES if date in d)

def get_month_range(year: int, month: int):
    date_start = format_year_month(year, month)
    date_end = next_month(year, month + 1)
    _prev = min(month_gen(date_start))
    try:
        _next = min(month_gen(date_end))
    except ValueError:
        _next = max(month_gen(date_start))
    return DATES[_prev], DATES[_next]

@constants_WBF.running_time
def save_df(df: DataFrame, year: int, month: int):
    date = format_year_month(year, month)
    name = os.path.join(DB_DATE_PATH, f"data_kills_{date}.pickle")
    df.to_pickle(name)

@constants_WBF.running_time
def save_list(df: DataFrame, year: int, month: int):
    names: set[str] = set()
    guilds: set[str] = set()
    for _, row in df.iterrows():
        names.update(row['names'])
        guilds.update(row['guilds'])

    date = format_year_month(year, month)
    __d = {"names": names, "guilds": guilds}
    for ff, _set in __d.items():
        if '' in _set:
            _set.remove('')
        _dict = {x.lower(): x for x in sorted(_set)}
        name = f'cache_names/{ff}-{date}.json'
        with open(name, 'w') as f:
            json.dump(_dict, f, indent=4)

@constants_WBF.running_time
def by_date(year: int, month: int):
    sID, fID = get_month_range(year, month)
    print(f"{sID=} {fID=}")
    s = sID // 100000
    f = fID // 100000
    name = os.path.join(DB_PATH, f"data_kills_{s}-{s+1}.pickle")
    DF = main_db.df_read(name)
    if DF is None: return

    new_df = DF.loc[sID:]
    if s == f:
        new_df = new_df.loc[:fID]
    else:
        name = os.path.join(DB_PATH, f"data_kills_{f}-{f+1}.pickle")
        df2 = main_db.df_read(name)
        df2 = df2.loc[:fID]
        new_df = new_df.append(df2)

    save_df(new_df, year, month)

    save_list(new_df, year, month)

# for month in range(4,13):
    # by_date(19, month)
# for year in range(20, 23):
    # for month in range(1, 13):
        # by_date(year, month)
by_date(22, 3)
