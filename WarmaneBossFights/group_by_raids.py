import json
from multiprocessing import Pool
from pandas import DataFrame
import main_db
import constants_WBF
import week_id_start

def print_separator():
    print('#'*100)

def find_s():
    main_week = week_id_start.new_wednesday(2021, 11, 6, True)
    prev_week = week_id_start.date_minus_week(main_week)
    dates = [
        week_id_start.date_minus_week(prev_week),
        prev_week,
        main_week,
        week_id_start.date_plus_week(main_week),
    ]
    for date in dates:
        result = week_id_start.find_last_id_before_reset(date)
        # result = list(result.values())[0]['last_id_before_reset']
        print(result)

REPORT_CODES = ['^^^ KILLED', 'XXX NO KILL', '+++ EXTENDED', '??? WTF ???']

def get_result_code(wipes, reports):
    if wipes + 1 == reports:
        return 0
    elif wipes == reports:
        return 1
    elif wipes > reports:
        return 2
    else: # if wipes < reports:
        return 3

# @constants_WBF.running_time
def week_instance_data(df: DataFrame):
    INSTANCE_DATA_ALL: list[dict[str, set]] = []
    for report_id, row in df.iterrows():
        names_set: set[str] = set(row['names'])
        for data in INSTANCE_DATA_ALL:
            all_saved_names: set[str] = data['names']
            if names_set & all_saved_names:
                data['reports'].add(report_id)
                data['wipes'].add(row['attempts'])
                all_saved_names.update(names_set)
                # INSTANCE_DATA_ALL[report_id] = INSTANCE_DATA_ALL.pop(last_report_id)
                break
        else:
            new_entry = {
                'reports': {report_id, },
                'names': names_set,
                'wipes': {row['attempts'], }
            }
            INSTANCE_DATA_ALL.append(new_entry)
            
    to_delete = []
    for n1, data1 in enumerate(INSTANCE_DATA_ALL, 1):
        if n1-1 in to_delete:
            # print("n1-1 in delete")
            # print(data1)
            continue
        for n2, data2 in enumerate(INSTANCE_DATA_ALL[n1:]):
            names = data1['names'] & data2['names']
            if not names:
                continue
            for x in {'reports', 'names', 'wipes'}:
                data1[x].update(data2[x])
            to_delete.append(n1+n2)
            # print(data2)
            # break
    try:
    # if 1:
        for x in reversed(sorted(to_delete)):
            INSTANCE_DATA_ALL.pop(x)
    except IndexError:
        i, row = next(df.iterrows())
        print(row['size'], row['boss'])
    
    return INSTANCE_DATA_ALL

def print_instance_info(instance_data, result_code):
    max_wipes = max(instance_data['wipes'])
    len_reports = len(instance_data['reports'])
    print("\n")
    print(f"{len_reports:>2} REPORTS: {instance_data['reports']}")
    print(f"{len(instance_data['names']):>2} PLAYERS: {sorted(instance_data['names'])}")
    result = REPORT_CODES[result_code]
    print(f"{result:<15} | {max_wipes:>2} WIPES: {instance_data['wipes']}")

def combine_instance_data_by_result_code(instance_data_all: list[dict[str, set]]):
    combined_instance_data: dict[int, list[dict]] = {}
    for instance_data in instance_data_all:
        max_wipes = max(instance_data['wipes'])
        len_reports = len(instance_data['reports'])
        result_code = get_result_code(max_wipes, len_reports)
        combined_instance_data.setdefault(result_code, []).append(instance_data)
    
    combined_instance_data = dict(sorted(combined_instance_data.items()))
    return combined_instance_data

def sdofjisdfj(data: dict[int, list[dict]]) -> set[int]:
    return {
        max(instance['reports'])
        for code in [2,3,4]
        for instance in data.get(code, [])
        if max(instance['wipes']) > 0
    }

def do_main_shit(df: DataFrame, filters: dict):
    df = main_db.df_apply_filters(df, filters)
    instance_data_all = week_instance_data(df)
    # print(json.dumps(instance_data_all, default=sorted))
    combined_instance_data = combine_instance_data_by_result_code(instance_data_all)
    __latest = sdofjisdfj(combined_instance_data)
    return {
        'data': combined_instance_data,
        'latest': __latest
    }

def new_filters(DB_Cache: main_db.DB_Cache, date, s, f):
    df = DB_Cache.df_from_range(s, f)
    # print(DB_Cache.cache.keys())
    data = {}
    latest = set()
    for size in [10, 25]:
        bosses = {}
        for boss in constants_WBF.BOSSES:
        # for boss in constants_WBF.BOSSES[:1]:
            filters = {
                'size': size,
                'boss': boss,
            }
            __result = do_main_shit(df, filters)
            bosses[boss] = __result['data']
            latest.update(__result['latest'])
        data[size] = bosses
    return {
        date: data,
        'latest': latest
    }

def main():
    wednesdays = constants_WBF.json_read('__dates_wed')
    wednesdays = dict(list(wednesdays.items())[-12:])
    # wednesdays = dict(list(wednesdays.items())[-11:-9])
    dbs = main_db.DB_Cache()

    w_dates = list(wednesdays.keys())
    w_ids = list(wednesdays.values())

    __test = [
        [dbs, w_dates[i], s, f]
        for i, (s, f) in enumerate(zip(w_ids, w_ids[1:]))
    ]

    with Pool(4) as p:
        all_shit = p.starmap(new_filters, __test)
    all_shit_dict = {}
    all_latest = set()
    for x in all_shit:
        all_latest.update(x.pop('latest'))
        all_shit_dict.update(x)
    # print(all_latest)
    with open('all_redo3.json', 'w') as f:
        json.dump(sorted(all_latest), f)
    # print(LATEST)
    constants_WBF.zlib_pickle_write(all_shit_dict, "wed_data_few.pickle.zlib")

def gothru(current_week: dict[str, set], week2: list[dict[str, set]], week3: list[dict[str, set]]):
    found: list[dict[str, set]] = []
    wipes = max(current_week['wipes'])
    names = set(current_week['names'])
    for week in [week2, week3]:
        for _id in week:
            if max(_id['wipes']) == wipes and names & set(_id['names']):
                found.append(_id)
                break
    return found

def print_extended(data):
    print(f"PLAYERS: {len(data['names']):>2} | {data['names']}")
    print(f"REPORTS: {len(data['reports']):>2} | {data['reports']}")
    print(f"  WIPES: {max(data['wipes']):>2} | {data['wipes']}")

def get_data(data: dict, size=10, boss="The Lich King", code=2):
    q = {}
    for date, sizes in data.items():
        bosses = sizes[size]
        q[date] = bosses[boss].get(code, [])
    return q

def do_shit2(filtered: dict):
    _new_shit = []

    _all: list[list[dict[str, set]]] = list(filtered.values())
    for week1, week2, week3 in zip(_all, _all[1:], _all[2:]):
        for current in week1:
            found = gothru(current, week2, week3)
            if not found:
                continue
            _new = dict(current)
            print()
            print_extended(current)
            for _found in found:
                for x in {'reports', 'names', 'wipes'}:
                    _new[x].update(_found[x])
                print_extended(_found)
            print_separator()
            print_extended(_new)
            print_separator()
            _new_shit.append(_new)

    _new_shit2 = combine_instance_data_by_result_code(_new_shit)

    only_kills = {}

    kills = _new_shit2[0]
    for kill in kills:
        kill_report_id = max(kill['reports'])
        date = week_id_start.new_wednesday_report_id(kill_report_id)
        date_str = week_id_start.date_to_string(date)
        only_kills.setdefault(date_str, []).append(kill)
    # print(only_kills)
    return only_kills

def main():
    # date - size - boss - report code
    wed_data_pickle: dict[str, dict[int, dict[str, dict[int, list[dict]]]]]
    wed_data_pickle = constants_WBF.zlib_pickle_read("wed_data_few.pickle.zlib")
    print(wed_data_pickle['21-12-15'][10]['The Lich King'].keys())
    # filtered = get_data(wed_data_pickle, 10, "The Lich King", 3)

    # print(json.dumps(filtered, default=sorted))

    # only_kills = do_shit2(filtered)
    # constants_WBF.save_json('new_kills', only_kills)

def main():
    return

# find_s()
if __name__ == "__main__":
    main()
    # all_shit_zlib = constants_WBF.zlib_pickle_make(all_shit_dict)
    # constants_WBF.zlib_pickle_write('wed_data.pickle.zlib', all_shit_zlib)

# marrow = check if lady pulled = dead
# get last marrow kill of everyone participated
# show all names - green who participated in kill - red others