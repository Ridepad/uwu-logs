from pandas.core.frame import DataFrame
import main_db
import os
from datetime import datetime, timedelta
import kill_date

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
KILL_DB = os.path.join(DIR_PATH, "kill_db")

TD = timedelta(days=1)

def to_datetime(date: str):
    y, m, d = map(int, date.split('-'))
    return datetime(year=y+2000, month=m, day=d)

def _next_td(_now, _next):
    return (to_datetime(_next) - to_datetime(_now)) == TD

def get_leaps(data):
    zz = list(data.items())
    return [
        (id1, id2)
        for (id1, d1), (id2, d2) in zip(zz, zz[1:])
        if _next_td(d1, d2)
    ]

def date_add_1(date):
    td = to_datetime(date) + TD
    return f"{td.year%100:0>2}-{td.month:0>2}-{td.day:0>2}"

def date_sub_1(date):
    td = to_datetime(date) - TD
    return f"{td.year%100:0>2}-{td.month:0>2}-{td.day:0>2}"

def count_values(data: dict):
    v = list(data.values())
    return max(v, key=v.count)

def find_key(data: dict, filter):
    for x, y in data.items():
        if y == filter:
            return x

def find_leap(data: dict):
    rdata = dict(reversed(data.items()))
    
    date = count_values(data)

    date2 = date_add_1(date)
    i2 = find_key(data, date2)
    if i2 is None:
        i1 = find_key(data, date)
        date2 = date_sub_1(date)
        i2 = find_key(rdata, date2)
        return i2, i1
         
    i1 = find_key(rdata, date)
    return i1, i2

def find_leap(data: dict,  d1, d2):
    # two_dates = sorted(set(data.values()))
    # try:
    #     d1, d2 = two_dates
    # except ValueError:
    #     print(two_dates)
    #     input()

    rdata = dict(reversed(data.items()))
    i1 = find_key(rdata, d1)

    i2 = find_key(data, d2)

    return i1, i2

def get_cut(df_const: DataFrame, s, f, leap=None):
    df = df_const.loc[s:f:leap]
    df = main_db.has_achievs(df)
    return CURRENT.loop1(df)

def get_dates_in_cut(df_const, s, f, leap=None):
    df = df_const.loc[s:f:leap]
    df = main_db.has_achievs(df)
    return CURRENT.loop1(df)

def get_dates_in_cut_rec(df_const: DataFrame, s, f, shift=50, leap=None, attempt=0):
    if attempt > 2:
        input()
    _f = f+shift*(attempt+1)
    # df = df_const.loc[s:f+shift*(attempt+1):leap]
    # df = main_db.has_achievs(df)
    # _dates = CURRENT.loop1(df)
    _dates = get_dates_in_cut(df_const, s, _f, leap)
    print('CURRENT.loop1:')
    print(_dates)
    _dates = kill_date.correct_dates(_dates)
    print('kill_date.correct_dates:')
    print(_dates)
    two_dates = sorted(set(_dates.values()))
    try:
        d1, d2 = two_dates
        return _dates, d1, d2
    except ValueError:
        print(f'\nATTEMPT {attempt+1}, NOT ENOUGH DATA:', two_dates)
        return get_dates_in_cut_rec(df_const, s, f, shift=shift, leap=leap, attempt=attempt+1)

def get_more_precise_leaps(df_const, all_leaps):
    new_leaps = []
    # s, f = LEAPS[5]
    # for _ in range(1,2):
    for s, f in all_leaps:
        print('\nleap:', s, f)
        _dates, d1, d2 = get_dates_in_cut_rec(df_const, s, f, leap=5)
        # _dates = get_dates_in_cut(df_const, s, f+50, leap=5)
        # print(_dates)
        # _dates = kill_date.correct_dates(_dates)
        # print(_dates)

        # two_dates = sorted(set(_dates.values()))
        # try:
        #     d1, d2 = two_dates
        # except ValueError:
        #     print('\nNOT ENOUGH DATA:', two_dates)
        #     _dates = get_dates_in_cut(df_const, s, f+100, leap=5)
        #     print(_dates)
        #     _dates = kill_date.correct_dates(_dates)
        #     print(_dates)

        #     two_dates = sorted(set(_dates.values()))
        #     try:
        #         d1, d2 = two_dates
        #     except ValueError:
        #         print('\nNOT ENOUGH DATA:', two_dates)
        #         input()

        s, f = find_leap(_dates, d1, d2)
        print('find_leap:', s, f)
        # if None in leaps:
        #     print('NONE IN LEAPS')
        #     _dates = get_dates_in_cut(df_const, s, f+250)
        #     print(_dates)
        #     _dates = kill_date.correct_dates(_dates)
        #     print(_dates)
        #     leaps = find_leap(_dates, d1, d2)
        #     print(leaps)

        _dates = get_dates_in_cut(df_const, s, f)
        # _dates, _, _ = get_dates_in_cut(df_const, s, f)
        print('get_dates_in_cut:\n', _dates)
        s, f = find_leap(_dates, d1, d2)
        _d = (_dates[f], f)
        print('new date:', _d)
        new_leaps.append(_d)

    for x,y in new_leaps:
        print(x,y)

    return new_leaps
    # df = df.loc[:3202110]

def get_df(s):
    name = f"data_kills_{s}-{s+1}.pickle"
    name = os.path.join(KILL_DB, name)
    return main_db.df_read(name)

def get_df_achi(df, step=50):
    df = main_db.has_achievs(df)
    df = df.loc[::step]
    return df

if __name__ == "__main__":
    server = "Lordaeron"
    CURRENT = kill_date.Current(server)

    df_n = 32
    df = get_df(df_n)

    step = 50
    df_achi = get_df_achi(df, step)

    dates = CURRENT.loop1(df_achi)
    new_dates = kill_date.correct_dates(dates)
    leaps = get_leaps(new_dates)

    print('\nGOT NEW LEAPS\n')
    print(leaps)

    get_more_precise_leaps(df, leaps)

