from pandas import DataFrame
import main_db
import constants_WBF
from datetime import datetime, timedelta

DATES_WED = "__dates_wed"
LIMIT = 50
KILL_DB = 'kill_db'
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SKIP = {'Onyxia', 'Malygos', 'Northrend Beasts', 'Toravon the Ice Watcher', 'Lord Marrowgar', 'Baltharus the Warborn'}

ONE_DAY = timedelta(days=1)
ONE_WEEK = timedelta(days=7)

def date_minus_week(date):
    return date - ONE_WEEK

def date_plus_week(date):
    return date + ONE_WEEK

DATES = constants_WBF.json_read('__dates.json')

def find_date(report_id: int):
    for date, reportID in reversed(DATES.items()):
        if report_id > reportID:
            return date
    return "??-??-??"

def date_to_string(date: datetime):
    return date.strftime("%y-%m-%d")

def to_report_id(date: datetime) -> int:
    return DATES[date_to_string(date)]

def get_report_ids(wednesday: datetime):
    thusday = wednesday + ONE_DAY
    wednesday_next = wednesday + ONE_WEEK
    report_id_wednesday = to_report_id(wednesday)
    try:
        report_id_thusday = to_report_id(thusday)
    except KeyError:
        return
    try:
        report_id_wednesday_next = to_report_id(wednesday_next)
    except KeyError:
        report_id_wednesday_next = list(DATES.items())[-2][1]
        if report_id_thusday == report_id_wednesday_next:
            return
    return report_id_wednesday, report_id_thusday, report_id_wednesday_next

def slice_by_week(DF: DataFrame, r1, r2, r7):
    db_wednesday = DF.loc[r1:r2]
    db_after_wednesday = DF.loc[r2:r7]
    return db_wednesday, db_after_wednesday

def reversed_df_filter_by(df: DataFrame, category: str, _filter):
    by_category = df[category]
    filtered = by_category.apply(lambda x: _filter != x)
    return df[filtered]



def get_df(start, end=None):
    sID = start // 100000
    eID = sID if end is None else end // 100000
    name = f"{KILL_DB}/data_kills_{sID}-{sID+1}.pickle"
    DF = main_db.df_read(name)
    DF = DF.loc[start:]
    if sID == eID:
        return DF.loc[:end]
    name_next = f"{KILL_DB}/data_kills_{eID}-{eID+1}.pickle"
    DF2 = main_db.df_read(name_next)
    DF2 = DF2.loc[:end]
    return DF.append(DF2)

def nearest_wednesday(date: datetime):
    for _ in range(6):
        date = date - ONE_DAY
        if date.weekday() == 2:
            return date

def new_wednesday(year, month, day, autocorrect=False):
    if year < 1000:
        year += 2000
    date = datetime(year, month, day)
    print("[DATE INPUT]:", date_to_string(date))
    weekday = date.weekday()
    if weekday != 2:
        if not autocorrect:
            raise ValueError(f"Date should point to Wednesday, but points to {WEEKDAYS[weekday]}, change parameter autocorrect=True to ignore this error")
        date = nearest_wednesday(date)
        print("[CORRECTED DATE]:", date_to_string(date))
    return date

def new_wednesday_report_id(report_id):
    kill_date = find_date(report_id)
    y, m, d = map(int, kill_date.split('-'))
    return new_wednesday(y, m, d, True)


def check1(temp_df: DataFrame, players_db_wed: set[str]):
    for n_db_after, row_db_after in temp_df.iterrows():
        if players_db_wed & set(row_db_after['names']):
            return n_db_after

@constants_WBF.running_time
def check_week_change(db_wednesday: DataFrame, db_after_wednesday: DataFrame) -> tuple[int, int]:
    without_dublicate = 0
    report_id_wednesday, report_id_after = 0, 0

    for n_db_wed, row_db_wed in db_wednesday.iterrows():
        if without_dublicate > LIMIT:
            print(f'REACHED LIMIT OF {LIMIT}')
            break
        
        boss_db_wed = row_db_wed['boss']
        if boss_db_wed in SKIP:
            continue
        
        temp_df = db_after_wednesday
        temp_df = main_db.df_filter_by(temp_df, "boss", boss_db_wed)
        temp_df = main_db.df_filter_by(temp_df, "size", row_db_wed['size'])
        if temp_df.empty: continue
        temp_df = reversed_df_filter_by(temp_df, "attempts", row_db_wed['attempts'])
        if temp_df.empty: continue

        players_db_wed = set(row_db_wed['names'])
        n_db_after = check1(temp_df, players_db_wed)
        if n_db_after:
            report_id_wednesday, report_id_after = n_db_wed, n_db_after
            without_dublicate = 0
        else:
            without_dublicate += 1
    
    return report_id_wednesday, report_id_after

def find_last_id_before_reset(date: datetime):
    report_ids = get_report_ids(date)
    if report_ids is None:
        return
    report_id_wednesday, report_id_thusday, report_id_wednesday_next = report_ids
    print(f"{report_id_wednesday=} {report_id_thusday=} {report_id_wednesday_next=}")
    DF = get_df(report_id_wednesday, report_id_wednesday_next)

    db_wednesday, db_after_wednesday = slice_by_week(DF, report_id_wednesday, report_id_thusday, report_id_wednesday_next)
    report_id_wednesday, report_id_after = check_week_change(db_wednesday, db_after_wednesday)
    # print(f"\n[FOUND DOUBLE] SIZE: {size_db_wed} | WIPES WED: {wipe_db_wed:>2} | WIPES AFTER: {row_db_after['attempts']:>2} | BOSS: {boss_db_wed}")
    # print(report_id_wednesday, report_id_after)
    if report_id_wednesday and report_id_after:
        wed_names = DF.loc[report_id_wednesday]['names']
        after_names = DF.loc[report_id_after]['names']
        # print(sorted(set(wed_names) & set(after_names)))

    return date.strftime("%y-%m-%d"), report_id_wednesday
    # return {
    #     date.strftime("%y-%m-%d"): {
    #         "last_id_before_reset": report_id_wednesday,
    #         "dublicate": report_id_after
    #     }
    # }

def main():
    dates_json = constants_WBF.json_read(DATES_WED)
    pre_last_wed = list(dates_json)[-2]
    y, m, d = map(int, pre_last_wed.split('-'))
    # y, m, d = 19, 1, 2
    
    data = []
    # now = datetime(2019, 6, 1)
    now = datetime.now() - ONE_DAY
    __date = new_wednesday(y, m, d, autocorrect=True)
    while __date < now:
        __result = find_last_id_before_reset(__date)
        print(__result)
        if __result is None:
            break
        data.append(__result)
        __date = __date + ONE_WEEK

    new_dates = dict(sorted(data))
    print(new_dates)

    constants_WBF.add_data_to_json(DATES_WED, new_dates)

if __name__ == "__main__":
    main()