import os
from datetime import datetime, timedelta

from pandas.core.frame import DataFrame

import kill_date
import main_db
import json

# from constants_WBF import running_time
import constants_WBF

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
KILL_DB = os.path.join(DIR_PATH, "kill_db")

def to_datetime(date: str):
    y, m, d = map(int, date.split('-'))
    return datetime(year=y+2000, month=m, day=d)

TD = timedelta(days=1)
def _next_td(_now, _next):
    return (to_datetime(_next) - to_datetime(_now)) == TD

def get_leaps(data):
    zz = list(data.items())
    return [
        (id1, id2)
        for (id1, d1), (id2, d2) in zip(zz, zz[1:])
        if _next_td(d1, d2)
    ]

def get_df(s):
    name = f"data_kills_{s}-{s+1}.pickle"
    name = os.path.join(KILL_DB, name)
    return main_db.df_read(name)


def find_key(data: dict[str, str], filter):
    for x, y in data.items():
        if y == filter:
            return x

def refine_leap(data: dict,  d1, d2):
    rdata = dict(reversed(data.items()))
    i1 = find_key(rdata, d1)
    i2 = find_key(data, d2)
    return i1, i2


def find_f(DF: DataFrame, f, shift=3, leap=None):
    df_f = DF.loc[f::leap]
    df_f_i = df_f.iterrows()
    for _ in range(shift):
        try:
            f, _ = next(df_f_i)
        except StopIteration:
            break
    return f

def get_dates_in_cut_rec(DF: DataFrame, s: int, f: int, leap=None, attempt=0) -> tuple[dict[str, str], str, str]:
    if attempt > 7:
        input()
    print(f"{s=}, {f=}, {leap=}, {attempt=}")
    __df = DF.loc[s:f:leap]
    _dates = CURRENT.loop1(__df)
    # _dates = get_dates_in_cut(DF, s, f, leap)
    print('CURRENT.loop1:\n', _dates)
    _dates = kill_date.correct_dates(_dates)
    print('kill_date.correct_dates:\n', _dates)
    two_dates = sorted(set(_dates.values()))
    try:
        d1, d2 = two_dates
        return _dates, d1, d2
    except ValueError:
        print(f'\nATTEMPT {attempt+1}, NOT ENOUGH DATA:', two_dates)
        f1 = find_f(DF, f, leap=leap)
        print(f"{f} => {f1}")
        return get_dates_in_cut_rec(DF, s, f1, leap=leap, attempt=attempt+1)

def refine_slice(df1, df_all, s, f):
    print('\n\n\nNEW LEAP:', s, f)
    _dates, d1, d2 = get_dates_in_cut_rec(df1, s, f, leap=5)

    s1, f1 = refine_leap(_dates, d1, d2)
    print('refine_leap:', s, f)

    _dates, _, _ = get_dates_in_cut_rec(df_all, s1, f1, leap=5)

    s2, f2 = refine_leap(_dates, d1, d2)
    print('refine_leap:', s, f)

    _dates, _, _ = get_dates_in_cut_rec(df_all, s2, f2)
        
    s3, f3 = refine_leap(_dates, d1, d2)
    new_date = (_dates[f3], f3)
    print('new date:', new_date)
    return new_date

@constants_WBF.running_time
def get_more_precise_dates(df1, df_all, all_leaps):
    new_dates = [
        refine_slice(df1, df_all, s, f)
        for s, f in all_leaps
    ]
    for x,y in new_dates:
        print(x,y)
    return dict(new_dates)

def add_to_main_dates(new_dates):
    NAME = "__dates"
    full_name = f"{NAME}.json"
    try:
        with open(full_name, 'r') as f:
            _old: dict = json.load(f)
    except FileNotFoundError:
        _old = {}
    
    _new = dict(_old)
    
    _new.update(new_dates)
    _new = dict(sorted(_new.items()))
    if _old == _new:
        return

    now = datetime.now()
    old_name = now.strftime(f"trash/{NAME}-%Y-%m-%d-%H-%M-%S.json")

    if os.path.isfile(full_name):
        if os.path.isfile(old_name):
            os.remove(old_name)
        os.rename(full_name, old_name)

    with open(full_name, 'w') as f:
        json.dump(_new, f, indent=4)

def dates_between(start, finish):
    df_n = start//100000
    full_df = get_df(df_n)
    print(full_df)
    # 3559240 3559584
    full_df = full_df.loc[start:finish+1]
    print(full_df)
    df_all = main_db.has_achievs(full_df)
    df1 = main_db.df_filter_by(full_df, "size", 10)
    df1 = main_db.has_1_achievs(df1)
    df1_step = df1.loc[::8]
    dates = CURRENT.loop1(df1_step)
    print(dates)
    new_dates = kill_date.correct_dates(dates)
    print("new_dates:\n", new_dates)
    leaps = get_leaps(new_dates)
    print('\nGOT NEW LEAPS:\n', leaps)

    _dates = get_more_precise_dates(df1, df_all, leaps)

    print(json.dumps(_dates))


def main(df_n, middle=False, _custom_start=None):
    full_df = get_df(df_n)
    if middle:
        if _custom_start:
            full_df1 = full_df.loc[_custom_start:]
        else:
            full_df1 = full_df.loc[df_n*100000+95000:]
        
        full_df2 = get_df(df_n+1)
        full_df2 = full_df2.loc[:(df_n+1)*100000+10000]
        full_df = full_df1.append(full_df2)
    else:
        full_df = get_df(df_n)
        if _custom_start:
            full_df = full_df.loc[_custom_start:]
    # full_df = full_df.loc[1790586:1794151]
    df_all = main_db.has_achievs(full_df)

    df1 = main_db.df_filter_by(full_df, "size", 10)
    df1 = main_db.has_1_achievs(df1)
    # df1 = main_db.has_1_achievs(full_df)
    # df1_step = df1.loc[::2]
    df1_step = df1.loc[::20]
    # for row, __data in df1_step.iterrows():
    #     __names = __data['playerNames']
    #     print(row)
    #     print(__names)
    #     print(type(__names))
    #     print(type(__names[0]))
    #     break
    # input()
    dates = CURRENT.loop1(df1_step)
    print(dates)
    # print(json.dumps({v:k for k,v in dates.items()}))
    new_dates = kill_date.correct_dates(dates)
    # print("new_dates:\n", new_dates)
    leaps = get_leaps(new_dates)
    # print('\nGOT NEW LEAPS:\n', leaps)

    input()

    if not leaps:
        i = list(dates)[0]
        dates.pop(i)
        new_dates = kill_date.correct_dates(dates)
        print("new_dates:\n", new_dates)
        leaps = get_leaps(new_dates)
        print('\nGOT NEW LEAPS:\n', leaps)

    _dates = get_more_precise_dates(df1, df_all, leaps)
    print(json.dumps(_dates))

    constants_WBF.add_data_to_json('__dates', _dates)
    # add_to_main_dates(_dates)

    kill_date.save_new()

if __name__ == "__main__":
    server = "Lordaeron"
    CURRENT = kill_date.Current(server)
    # main(35, _custom_start=3500296)
    # main(35, middle=True, _custom_start=3597358)
    # main(36)
    main(36, _custom_start=3686297)
    # dates_between(3559240, 3559584)
