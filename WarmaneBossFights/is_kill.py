import os
import json

from pandas.core.frame import DataFrame
from multiprocessing import Pool

try:
    from . import constants_WBF
    from . import main_db
except ImportError:
    import constants_WBF
    import main_db

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
DB_PATH = os.path.join(DIR_PATH, "kill_db_date")
ACHI_DUMP = os.path.join(DIR_PATH, "achi_dump")
    
__dates = os.path.join(DIR_PATH, "__dates.json")
DATES: dict[str, int] = constants_WBF.json_read(__dates)
DATES = {v:k for k,v in DATES.items()}
DATES_KEYS = list(DATES)
def find_date(report_id: str):
    for reportID1, reportID2 in zip(DATES_KEYS, DATES_KEYS[1:]):
        if report_id < reportID2:
            return DATES[reportID1]
    # return DATES[DATES_KEYS[-1]]
    return "??-??-??"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]
MONTHS = {f"{n:0>2}": month for n, month in enumerate(MONTHS, 1)}

def format_date(date: str):
    year, month, day = date.split("-")
    month = MONTHS[month][:3]
    return f"{int(day)} {month} {year}"

TOPS = []
class Top:
    files = constants_WBF.get_all_files('pickle', DB_PATH)
    def __init__(self, n: int) -> None:
        name = self.files[n]
        name = os.path.join(DB_PATH, name)
        self.df = main_db.df_read(name)

    def prep_df(self, filters: dict):
        return main_db.df_apply_filters(self.df, filters)


def format_report(df: DataFrame, report_id: str):
    data = df.loc[report_id]
    duration = data['duration']
    duration = main_db.duration_format(duration)
    guildname = main_db.get_guild(data)
    return {
        "date": find_date(report_id),
        "report_id": report_id,
        "boss": data["boss"],
        "size": data["size"],
        "attempts": data["attempts"],
        "duration": duration,
        "guild": guildname,
        "players": data["names"],
        "difficulty": "H" if data["difficulty"] else "N",
    }

def finalize(top: dict):
    top = sorted(top, key=lambda x: x['date'])
    top = sorted(top, key=lambda x: x['duration'])
    top = sorted(top, key=lambda x: len(x['duration']))
    for d in top:
        d['date'] = format_date(d['date'])
    return enumerate(top, 1)


def add_report(report_id, zzz: dict[int, set]):
    rid = report_id // 1000
    for ridrange, ridset in zzz.items():
        if rid in range(ridrange, ridrange+2):
            ridset.add(report_id)
            break
    else:
        zzz.setdefault(rid, set()).add(report_id)

@constants_WBF.running_time
def fetch_reports_combined(df: DataFrame):
    '''{
        guildname: {
            attempts_num: {
                rid: set()
            }}}'''
    reports: dict[str, dict[str, dict[int, set[int]]]] = {}

    for report_id, data in df.iterrows():
        guild = main_db.get_guild(data)
        attempts_num = data['attempts']
        zzz = reports.setdefault(guild, {}).setdefault(attempts_num, {})
        add_report(report_id, zzz)

    return reports

@constants_WBF.running_time
def make_kills_combined(df: DataFrame, j: dict[str, dict[str, dict[int, set[int]]]]):
    kills: dict[str, set[int]] = {}
    for guildname, attempts in j.items():
        if guildname == "Pug": continue
        for attempts_num, reports in attempts.items():
            attempts_num = int(attempts_num)
            for ridrange, ridset in reports.items():
                m_id = max(ridset)
                report = df.loc[m_id]
                if report["achievements"] or len(ridset) - 1 == attempts_num:
                    kills.setdefault(guildname, set()).add(m_id)
    return kills

def get_fastest_kill(df: DataFrame, s: set[int]) -> tuple[int]:
    return min((df.loc[x]['duration'], x) for x in s)

def format_report_combined(df: DataFrame, ids: set[int]):
    duration, report_id = get_fastest_kill(df, ids)
    return format_report(df, report_id)

@constants_WBF.running_time
def finalize_combined(df: DataFrame, kills: dict[str, set[int]]):
    _top = [
        format_report_combined(df, ids)
        for ids in kills.values()
    ]
    return finalize(_top)

@constants_WBF.running_time
def make_top_combined(df: DataFrame):
    reports = fetch_reports_combined(df)
    # print(json.dumps(reports, default=list))
    kills = make_kills_combined(df, reports)

    return finalize_combined(df, kills)


@constants_WBF.running_time
def fetch_reports_all(df: DataFrame):
    '''{
        attempts_num: {
            char_name: {
                rid: set()
            }}}'''
    reports: dict[str, dict[str, dict[int, set[int]]]] = {}

    for report_id, data in df.iterrows():
        attempts_num = data['attempts']
        for char_name in data['names']:
            zzz = reports.setdefault(attempts_num, {}).setdefault(char_name, {})
            add_report(report_id, zzz)

    return reports

@constants_WBF.running_time
def make_kills_all(df: DataFrame, j: dict[str, dict[str, dict[int, set[int]]]]):
    cache = {}
    all_kills: dict[str, set[int]] = {}
    for attempts_num, chars in j.items():
        attempts_num = int(attempts_num)
        for char_name, attempts in chars.items():
            for ridrange, ridset in attempts.items():
                m_id = max(ridset)
                try:
                    data = cache[m_id]
                except KeyError:
                    data = cache[m_id] = df.loc[m_id]
                delta = -1 if data["achievements"] else attempts_num - len(ridset)
                
                all_kills.setdefault(m_id, set()).add(delta)
    return {
        report_id
        for report_id, reports in all_kills.items()
        if min(reports) == -1
    }

@constants_WBF.running_time
def finalize_all(df: DataFrame, kills: set[int]):
    _top = [
        format_report(df, report_id)
        for report_id in kills
    ]
    return finalize(_top)

@constants_WBF.running_time
def make_top_all(df: DataFrame):
    reports = fetch_reports_all(df)
    kills = make_kills_all(df, reports)

    return finalize_all(df, kills)

AA = [
    'The Lich King',
    'Lord Marrowgar', 'Lady Deathwhisper', 'Gunship Battle', 'Deathbringer Saurfang',
    'Festergut', 'Rotface', 'Professor Putricide', 'Blood Prince Council', "Blood-Queen Lana'thel",
    'Valithria Dreamwalker', 'Sindragosa', 'Halion', 'Baltharus the Warborn', 'General Zarithrian',
    'Saviana Ragefire', "Anub'arak", 'Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions',
    "Twin Val'kyr", 'Toravon the Ice Watcher', 'Archavon the Stone Watcher', 'Emalon the Storm Watcher',
    'Koralon the Flame Watcher', 'Onyxia', 'Malygos', 'Sartharion', "Anub'Rekhan", 'Grand Widow Faerlina',
    'Maexxna', 'Noth the Plaguebringer', 'Heigan the Unclean', 'Loatheb', 'Patchwerk', 'Grobbulus', 'Gluth',
    'Thaddius', 'Instructor Razuvious', 'Gothik the Harvester', 'The Four Horsemen', 'Sapphiron', "Kel'Thuzad",
    'Flame Leviathan', 'Ignis the Furnace Master', 'Razorscale', 'XT-002 Deconstructor', 'Assembly of Iron',
    'Kologarn', 'Auriaya', 'Hodir', 'Thorim', 'Freya', 'Mimiron', 'General Vezax', 'Yogg-Saron', 'Algalon the Observer'
]

def convert_to_json(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        if type(value) != str:
            try:
                value = list(value)
            except (TypeError, ValueError):
                pass
    return value

COLUMNS = ['guild', 'duration', 'attempts', 'date', 'report_id']
def bfosdpkfsopd(data):
    return [{k: convert_to_json(v) for k, v in d.items() if k in COLUMNS} for _, d in data]

def __main(top: Top, filters):
    ALL = {}
    COMB = {}
    db = top.prep_df(filters)
    for bossname in AA:
        db_f = main_db.df_apply_filters(db, {'boss': bossname})
        _all = make_top_all(db_f)
        ALL[bossname] = bfosdpkfsopd(_all)
        _combined = make_top_combined(db_f)
        COMB[bossname] = bfosdpkfsopd(_combined)
    
    return {
        'filters': filters,
        'all': ALL,
        'combined': COMB,
    }

def __themain(s):
    top = Top(s)
    
    q = [
        (top, {'difficulty': diff, 'size': size})
        for size in [10, 25]
        for diff in [0, 1]
    ]

    with Pool(4) as p:
        done = p.starmap(__main, q)
    DATA = {}
    for d in done:
        diff = d['filters']['difficulty']
        size = d['filters']['size']
        for type_ in ['all', 'combined']:
            for bossname, new_data in d[type_].items():
                q = DATA.setdefault(type_, {}).setdefault(bossname, {}).setdefault(size, {})
                q[diff] = new_data
    # for d in done:
    #     for type_, bosses in d.items():
    #         for boss, sizes in bosses.items():
    #             for size, new_data in sizes.items():
    #                 DATA.setdefault(type_, {}).setdefault(boss, {}).setdefault(size, {}).update(new_data)

    print('done')

    return DATA
    # DATA = {'all': ALL, 'combined': COMB}
    # with open('_DATA3.json', 'w') as f:
    #     json.dump(DATA, f, indent=4, default=list)
    
    # for n, data in __q:
    #     z = f'{n:>3} | {data["date"]:>9} | {data["duration"]:>5} | {data["attempts"]:>2} | {data["guild"]:>30}'
    #     # z = f'{data["report_id"]} | {data["date"]:>9} | {data["duration"]:>5} | {data["attempts"]:>2} | {data["guild"]:>30}'
    #     print(z)

def main():
    DATA = {}
    for i, name in enumerate(Top.files):
    # for i in range(len(Top.files)):
        name = name.split('_')[-1].split('.')[0]
        print(name)
        DATA[name] = __themain(i)
    with open('_DATA4.json', 'w') as f:
        json.dump(DATA, f, indent=4, default=list)


if __name__ == "__main__":
    main()