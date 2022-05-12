
import pandas
from group_by_raids import do_shit2
import main_db
import constants_WBF

WEDS = {
    '21-09-08': 3188698, '21-09-15': 3204580, '21-09-22': 3220083, '21-09-29': 3235850, '21-10-06': 3251089,
    '21-10-13': 3266402, '21-10-20': 3281825, '21-10-27': 3297829, '21-11-03': 3313298, '21-11-10': 3329808,
    '21-11-17': 3345944, '21-11-24': 3362206, '21-12-01': 3377955, '21-12-08': 3393559
}
WEDS = {
    '21-09-08': 3188698, '21-09-15': 3204580, '21-09-22': 3220083,
    '21-09-29': 3235850, '21-10-06': 3251089, '21-10-13': 3266402,
    '21-10-20': 3281825, '21-10-27': 3297829, '21-11-03': 3313298, '21-11-10': 3329808,
    '21-11-17': 3345944, '21-11-24': 3362206, '21-12-01': 3377955, '21-12-08': 3393559
}

WEDS = {
  "22-02-02": 3503824,
  "22-02-09": 3518676,
  "22-02-16": 3532269,
  "22-02-23": 3546906,
}
# WEDS = constants_WBF.load_json('__dates_wed')

def find_date(report_id: int):
    for date, reportID in reversed(WEDS.items()):
        if report_id > reportID:
            return date
    return "??-??-??"

FILTERS = {
    'boss': 'The Lich King',
    'size': 10
}

def slice2(df, current):
    # date_start = WEDS[find_date(current)]
    # print(date_start, current)
    df_temp = df.loc[:current]
    return main_db.df_apply_filters(df_temp, FILTERS)


def print_instance_info(instance_data):
    max_wipes = max(instance_data['wipes'])
    len_reports = len(instance_data['reports'])
    print("\n")
    print(f"{len_reports:>2} REPORTS: {instance_data['reports']}")
    print(f"{len(instance_data['names']):>2} PLAYERS: {sorted(instance_data['names'])}")
    print(f"{max_wipes:>2} WIPES: {instance_data['wipes']}")


# @constants_WBF.running_time
def new_instance(df, current_id, data1):
    names_set = set(data1['names'])
    reports = {current_id, }
    wipes = {data1['attempts'], }

    df_temp = df.loc[:current_id]
    for i2, data2 in df_temp.iterrows():
        names_set2 = set(data2['names'])
        if names_set & names_set2:
            names_set.update(names_set2)
            reports.add(i2)
            wipes.add(data2['attempts'])
    
    return {
        'names': names_set,
        'reports': reports,
        'wipes': wipes
    }

@constants_WBF.running_time
def doweek(df: pandas.DataFrame, s, f, filters):
    week = []
    df_week = df.loc[s:f]
    df_week_filtered = main_db.df_apply_filters(df_week, filters)
    df_achi = main_db.has_achievs(df_week_filtered)
    print(f"{len(df_achi):>4} TOTAL:", filters)
    for current_id, data1 in df_achi.iterrows():
        instance = new_instance(df_week_filtered, current_id, data1)
        week.append(instance)
    # for instance_data in week:
    #     print_instance_info(instance_data)
    return week
BOSSES = constants_WBF.BOSSES_CATS['Icecrown Citadel']
def main2(df: pandas.DataFrame):
    reports = list(WEDS.values())
    allshit = {}
    for date, (s,f) in zip(WEDS, zip(reports, reports[1:])):
        allshit_dates = allshit.setdefault(date, {})
        for size in [10, 25]:
            allshit_sizes = allshit_dates.setdefault(size, {})
            for boss in BOSSES:
                filters = {
                    'boss': boss,
                    'size': size
                }
                allshit_sizes[boss] = doweek(df, s, f, filters)

    constants_WBF.json_write('all_kills_icc', allshit)

def get_result_code(wipes, reports):
    if wipes + 1 == reports:
        return 0
    elif wipes == reports:
        return 1
    elif wipes > reports:
        return 2
    else: # if wipes < reports:
        return 3

def print_separator():
    print('#'*100)

def main():
    # df1 = main_db.get_df_by_n(32)
    # df2 = main_db.get_df_by_n(33)
    # df = df1.append(df2)
    # main2(df)
    j = constants_WBF.json_read('all_kills_icc')
    week = {}
    for date, sizes in j.items():
        print_separator()
        print(date)
        for size, bosses in sizes.items():
            q = week.setdefault(date, {}).setdefault(size, {})
            for boss, data in bosses.items():
                __data = []
                for instance_data in data:
                    reports = len(instance_data['reports'])
                    len_wipes = max(instance_data['wipes'])
                    code = get_result_code(len_wipes, reports)
                    if code == 2:
                        __data.append(instance_data)
                if __data:
                    q[boss] = __data
            
    constants_WBF.json_write("_icc_extends", week)

if __name__ == "__main__":
    main()