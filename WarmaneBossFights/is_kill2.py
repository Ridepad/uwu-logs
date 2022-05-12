import pandas
import main_db
import week_id_start
import constants_WBF
import importlib
import is_kill2_import
import traceback

def find_slice():
    WEDS = constants_WBF.json_read('__dates_wed')

    def find_date(report_id: int):
        for date, reportID in reversed(WEDS.items()):
            if report_id > reportID:
                return date
        return "??-??-??"

    def between(s, f):
        return {x: _id for x, _id in WEDS.items() if s <= x <= f}

    s = find_date(32*100000)
    f = find_date(34*100000)
    print(s, f)
    print(between(s,f ))


df1 = main_db.get_df_by_n(32)
df2 = main_db.get_df_by_n(33)
df = df1.append(df2)

def main():
    while 1:
        importlib.reload(is_kill2_import)
        try:
            is_kill2_import.main(df)
        except Exception:
            print(traceback.format_exc())
        input()
# df1 = main_db.has_achievs(df1)

main()
# for i, data in df1.iterrows():
    # if data['']: continue