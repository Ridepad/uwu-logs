import concurrent.futures
import json
import os
import re
from datetime import datetime
from time import time as tm

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pandas import DataFrame

try:
    from . import main_db
    from . import constants_WBF
except ImportError:
    import main_db
    import constants_WBF

CATEGORIES = constants_WBF.CATEGORIES

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
KILL_DB = os.path.join(DIR_PATH, "kill_db")
ACHI_DUMP = os.path.join(DIR_PATH, "achi_dump")

# CACHE_ACHI = os.path.join(ACHI_DUMP, "__main_cache.json")
CACHE_ACHI = os.path.join(ACHI_DUMP, "__main_cache.pickle.zlib")
CACHE_ACHI_OLD = f"{CACHE_ACHI}.old"

HEADERS = {'User-Agent': "WrmnAchPrsr"}

def open_cache(fname):
    try:
        return constants_WBF.zlib_pickle_read(fname)
    except FileNotFoundError:
        return

def load_json(name):
    try:
        with open(name) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def find_category(achi_id):
    # achi_id = str(achi_id)
    # print('find_category', achi_id, type(achi_id))
    for category_id, achievement_ids in CATEGORIES.items():
        # print(category_id, achievement_ids)
        # print(achi_id in achievement_ids)
        if achi_id in achievement_ids:
            return category_id

def open_all():
    __j: dict[str, dict[str, dict[str, str]]]

    __main_cache: dict[str, dict[str, dict[str, str]]] = open_cache(CACHE_ACHI) or {}

    __all_json = constants_WBF.get_all_files('json', ACHI_DUMP)

    for file_name in __all_json:
        full_file_name = os.path.join(ACHI_DUMP, file_name)
        __j = load_json(full_file_name)
        for char_name, categories in __j.items():
            __main_cache.setdefault(char_name, {}).update(categories)

    return __main_cache

def save_new():
    cache_old = open_cache(CACHE_ACHI) or {}
    cache_new = open_all()
    if not cache_new: return
    if cache_new == cache_old: return

    if os.path.isfile(CACHE_ACHI):
        if os.path.isfile(CACHE_ACHI_OLD):
            os.remove(CACHE_ACHI_OLD)
        os.rename(CACHE_ACHI, CACHE_ACHI_OLD)

    constants_WBF.zlib_pickle_write(cache_new, CACHE_ACHI)

    __all_files = constants_WBF.get_all_files('json', ACHI_DUMP)
    for file_name in __all_files:
        full_file_name = os.path.join(ACHI_DUMP, file_name)
        os.remove(full_file_name)


def parse_date(achi: Tag):
    _date = achi.find(class_="date")
    if not _date:
        return ""
    _date = _date.text.strip()
    m, d, y = re.findall('(\d\d)/(\d\d)/\d\d(\d\d)', _date)[0]
    return f"{y}-{m}-{d}"

def create_time_str(t: float):
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = minutes // 60
    return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"

def save_json(name, _new):
    if not _new: return
    _old = load_json(name)
            
    if _old == _new: return
    with open(name, 'w') as f:
        json.dump(_new, f)

class Current:
    post_requests = 0
    achivs_post = 0

    cache_no_char = os.path.join(DIR_PATH, "cache_no_char.json")
    NO_CHAR: dict[str, str] = load_json(cache_no_char)

    def __init__(self, server: str):
        self.server = server
        self.CACHE = open_all()
        self.new_cache: dict[str, dict[str, dict[str, str]]] = {}
        # _date = datetime.now().strftime("%y-%m-%d-%H-%M-%S.json")
        # self.cache_achi = os.path.join(ACHI_DUMP, _date)

    def save_data(self):
        _date = datetime.now().strftime("%y-%m-%d-%H-%M-%S-%f.json")
        cache_achi = os.path.join(ACHI_DUMP, _date)
        save_json(cache_achi, self.new_cache)
        save_json(self.cache_no_char, self.NO_CHAR)
        self.new_cache = {}

    def get_post(self, url, category, attempt=0):
        # print('getpost', attempt)
        if attempt > 2:
            return
        try:
            self.post_requests += 1
            return requests.post(url, data={"category": category}, headers=HEADERS, timeout=1)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print('requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout')
            return self.get_post(url, category, attempt+1)

    def add_to_cache(self, achievements: str, char_name: str, category: str):
        char_achievements = self.CACHE.setdefault(char_name, {}).setdefault(category, {})
        char_achievements_new = self.new_cache.setdefault(char_name, {}).setdefault(category, {})
        achi: Tag
        achievs = BeautifulSoup(achievements, features="html.parser")
        for achi in achievs.find_all(class_="achievement"):
            _id = achi["id"].replace('ach', '')
            _date = parse_date(achi)
            char_achievements[_id] = _date
            char_achievements_new[_id] = _date
        return char_achievements

    def get_achievements(self, char_name: str, category: str):
        if char_name in self.NO_CHAR:
            return

        if char_name in self.CACHE:
            char_achievements = self.CACHE.get(char_name, {})
            if category in char_achievements:
                return char_achievements[category]

        url = f"http://armory.warmane.com/character/{char_name}/{self.server}/achievements"
        response = self.get_post(url, category)
        # print(response.headers)
        # input()

        try:
            achievements = response.json()['content']
            return self.add_to_cache(achievements, char_name, category)
        except json.decoder.JSONDecodeError:
            print(f'\nChar not found: {char_name} | json error:', response.text[:15])
            return

    def parse_dates(self, characters: list[str], category: str):
        with concurrent.futures.ThreadPoolExecutor(2) as executor:
            _threads = {
                char_name: executor.submit(self.get_achievements, char_name=char_name, category=category)
                for char_name in characters
            }
        concurrent.futures.wait(_threads.values())
        return {char_name: _thread.result() for char_name, _thread in _threads.items()}

    def main(self, achievements: list[str], characters: list[str], report_id: str):
        if not achievements: return

        all_dates: list[str] = []
        for achi_id in achievements:
            self.achivs_post += 1
            achi_id = str(achi_id)
            category = str(find_category(achi_id))
            # print(f"{category=}")
            data = self.parse_dates(characters, category)

            new_dates = []
            for char_name, result in data.items():
                if result is None:
                    self.NO_CHAR[char_name] = report_id
                elif achi_id in result:
                    new_dates.append(result[achi_id])
                else:
                    print('\nACHI ERROR:', char_name, achi_id)
                    print(result)
            if new_dates:
                all_dates.append(max(new_dates))
            else:
                print('0 ACHI RETURNED:', report_id, achi_id)

        if all_dates:
            return min(all_dates)
            
    def create_report_str(self, _add: str):
        current = f"{self.at_index:>7}/{self.total:>7}"

        duration = tm() - self.started
        running = create_time_str(duration)

        e = duration / (self.at_index / self.total) - duration
        eta = create_time_str(e)
        posts = f" | POSTS: {self.post_requests:>6} | L: {self.achivs_post:>6}"
        print(f"{current} | {running} | ETA: {eta}{posts} {_add}")

    def loop1(self, df: DataFrame):
        self.started = tm()
        self.total = len(df)
        dates = {}
        for n, (report_id, row) in enumerate(df.iterrows(), 1):
            self.at_index = n

            names = row['playerNames']
            achievements = row['achievements']
            _date = self.main(achievements, names, report_id)
            _add = f" | {report_id} | {_date}"
            self.create_report_str(_add)
            if _date is not None:
                dates[report_id] = _date

            if n%100==0:
                self.save_data()
        self.save_data()

        return dates

    
def to_datetime(date: str):
    y, m, d = map(int, date.split('-'))
    return datetime(year=y+2000, month=m, day=d)

def _next_td(_now, _next):
    return (to_datetime(_next) - to_datetime(_now)).days

def correct_dates(dates: dict[str, str], debug=0):
    # sourcery skip: merge-duplicate-blocks, remove-redundant-if
    new_dates: dict[str, str] = {}
    dates_items = list(dates.items())
    last_report_id, last_date = dates_items[0]
    for (id1, date1), (id2, date2), (id3, date3) in zip(dates_items, dates_items[1:], dates_items[2:]):
        if not date1: continue
        if debug:
            print(f"{id1} | {last_date} | {date1} | {date2} | {date3}")
        if last_date == date1:
            new_dates[id1] = date1
            continue
        tdays = _next_td(last_date, date1)
        if tdays == 1:
            if date1 in [date2, date3]:
                if debug:
                    print(f"{last_date} => {date1}")
                last_date = date1
                new_dates[id1] = last_date
            elif last_date == date2:
                new_dates[id1] = last_date
        elif last_date in [date2, date3]:
            new_dates[id1] = last_date

    return new_dates

def __idk():
    cache_achi = os.path.join(DIR_PATH, "cache_achi.json")
    MAIN_JSON = load_json(cache_achi)
    for char_name, categories in dict(MAIN_JSON).items():
        for category, data in dict(categories).items():
            if not data:
                print(char_name, data)
                del MAIN_JSON[char_name][category]
                continue
            for achi_id, value in data.items():
                if not value:
                    data[achi_id] = ''
        if not categories:
            print(char_name, categories)
            del MAIN_JSON[char_name]
            print()

    with open(cache_achi, 'w') as f:
        json.dump(MAIN_JSON, f)


def __main():
    def main_loop(s, step=50):
        name = f"data_kills_{s}-{s+1}.pickle"
        name = os.path.join(KILL_DB, name)
        df = main_db.df_read(name)
        df = main_db.has_achievs(df)
        df = df.loc[::step]
        return CURRENT.loop1(df)

    dates = main_loop(36)
    new_dates = correct_dates(dates)
    print(new_dates)

if __name__ == "__main__":
    server = "Lordaeron"
    CURRENT = Current(server)
    # __main()
    # save_new()
    # data = CURRENT.get_achievements("Nomadra", 15042)
    # data = CURRENT.get_achievements("Fallenz", 15042)
    achi = (4527,)
    report_id = 3607928
    characters = ('Fallenz', 'Shaamlee', 'Doomlorderan', 'Miningd', 'Missrize', 'Turalyoon', 'Saeidsyco', 'Cucurbits', 'Prasetoeblio', 'Senzonjr')
    data = CURRENT.main(achi, characters, report_id)
    print(data)