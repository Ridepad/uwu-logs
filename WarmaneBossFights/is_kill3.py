from flask import appcontext_popped
import pandas
import main_db
import constants_WBF

def print_instance_info(instance_data):
    max_wipes = max(instance_data['wipes'])
    len_reports = len(instance_data['reports'])
    print("\n")
    print(f"{max_wipes:>2} WIPES: {instance_data['wipes']}")
    print(f"{len_reports:>2} REPORTS: {instance_data['reports']}")
    print(f"{len(instance_data['names']):>2} PLAYERS: {sorted(instance_data['names'])}")

WED = {
  "21-12-15": 3408968,
  "21-12-22": 3422712,
  "21-12-29": 3434885,
  "22-01-05": 3445585,
  "22-01-12": 3459522,
  "22-01-19": 3473934,
  "22-01-26": 3488841,
  "22-02-02": 3503824,
  "22-02-09": 3518676,
  "22-02-16": 3532269,
  "22-02-23": 3546906,
  "22-03-02": 3561432,
  "22-03-09": 3574884
}
WEDVK = {v:k for k,v in WED.items()}

DONE = set()

week = []
def new_instance(df, current_id, data1):
    names_set = set(data1['names'])
    reports = {current_id, }
    wipes = {data1['attempts'], }

    df_temp = df.loc[current_id:]
    for i2, data2 in df_temp.iterrows():
        names_set2 = set(data2['names'])
        if names_set & names_set2:
            names_set.update(names_set2)
            reports.add(i2)
            wipes.add(data2['attempts'])
            DONE.add(i2)
    
    return {
        'names': names_set,
        'reports': reports,
        'wipes': wipes
    }

def combine_week(week: list[dict[str, set]]):
    DONE = set()
    def new_instance2(n, instance1: dict[str, set]):
        names_set = instance1['names']
        reports = instance1['reports']
        wipes = instance1['wipes']
        for i, instance2 in enumerate(week[n:]):
            if names_set & instance2['names']:
                DONE.add(i+n)
                names_set.update(instance2['names'])
                reports.update(instance2['reports'])
                wipes.update(instance2['wipes'])
        return {
            'names': names_set,
            'reports': reports,
            'wipes': wipes
        }

    __week = []
    for n, instance1 in enumerate(week):
        if n in DONE:
            continue
        _i = new_instance2(n+1, instance1)
        if _i:
            __week.append(_i)
    return __week

@constants_WBF.running_time
def new_week(temp_df_rev: pandas.DataFrame):
    week = []

    for current_id, data in temp_df_rev.iterrows():
        if current_id in DONE:
            continue
        instance = new_instance(temp_df_rev, current_id, data)
        week.append(instance)

    week = combine_week(week[::-1])
    week = combine_week(week)
    return week

def df_cut_reverse(df: pandas.DataFrame, s, f, filters):
    temp_df = df.loc[s:f]
    temp_df = main_db.df_apply_filters(temp_df, filters)
    return temp_df[::-1]

def main():
    df = main_db.get_df_by_n(34)
    df2 = main_db.get_df_by_n(35)
    df = df.append(df2)
    filters = {
        'boss': 'The Lich King',
        'size': 10
    }
    all_weeks = {}
    report_list = list(WED.values())[::-1]
    for f, s in zip(report_list, report_list[1:]):
        temp_df_rev = df_cut_reverse(df, s, f, filters)
        week = new_week(temp_df_rev)
        __wed = WEDVK[s]
        all_weeks[__wed] = week
    

    s = []
    for date, week in all_weeks.items():
    #     print()
    #     print(date)
        for instance in week:
            s.append(max(instance['reports']))
    #         print_instance_info(instance)
    print(s)
    constants_WBF.json_write('_icc_data', all_weeks)

# def main():
#     df = main_db.get_df_by_n(35)

if __name__ == "__main__":
    main()