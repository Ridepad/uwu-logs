import concurrent.futures
import json
import os
import re
from datetime import datetime, timedelta
from time import time as tm

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pandas import DataFrame

import main_db
from constants_WBF import CATEGORIES, running_time

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
KILL_DB = os.path.join(DIR_PATH, "kill_db")

HEADERS = {'User-Agent': "AchiParser"}

def load_json(name):
    try:
        with open(name) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def find_category(achi_id):
    for category_id, achievement_ids in CATEGORIES.items():
        if achi_id in achievement_ids:
            return category_id


def get_date(achi: Tag):
    _date = achi.find(class_="date")
    if not _date:
        return ""
    _date = _date.text.strip()
    m, d, y = re.findall('(\d\d)/(\d\d)/\d\d(\d\d)', _date)[0]
    return f"{y}-{m}-{d}"

def get_time_str(t: float):
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = minutes // 60
    return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"


class Current:
    cache_no_char = os.path.join(DIR_PATH, "cache_no_char.json")
    NO_CHAR: dict[str, str] = load_json(cache_no_char)

    cache_achi = os.path.join(DIR_PATH, "cache_achi.json")
    CACHE: dict[str, dict[str, dict[str, str]]] = load_json(cache_achi)

    POST_REQUESTS = 0

    def __init__(self, server: str):
        self.server = server

    @staticmethod
    def add_to_cache(achievements: str, char_achievements: dict[str, str]):
        achi: Tag
        achievs = BeautifulSoup(achievements, features="html.parser")
        for achi in achievs.find_all(class_="achievement"):
            _id = achi["id"].replace('ach', '')
            char_achievements[_id] = get_date(achi)
        return char_achievements

    def get_post(self, url, category, attempt=0):
        if attempt > 2:
            return
        try:
            self.POST_REQUESTS += 1
            return requests.post(url, data={"category": category}, headers=HEADERS, timeout=1)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            return self.get_post(url, category, attempt+1)

    def get_achievements(self, char_name: str, category: str):
        if char_name in self.NO_CHAR:
            return

        char_achievements = self.CACHE.setdefault(char_name, {}).setdefault(category, {})
        if char_achievements:
            return char_achievements

        url = f"http://armory.warmane.com/character/{char_name}/{self.server}/achievements"
        response = self.get_post(url, category)

        try:
            achievements = response.json()['content']
            return self.add_to_cache(achievements, char_achievements)
        except json.decoder.JSONDecodeError:
            self.NO_CHAR[char_name] = self.report_id
            print(response.text)
            print(f'\n{response.status_code} | Char not found: {char_name}')
        except AttributeError:
            print(f'\nTIMEOUT: {char_name} {category}')


    def get_date(self, achi_id: str):
        category = str(find_category(achi_id))

        with concurrent.futures.ThreadPoolExecutor(3) as executor:
            _threads = [
                executor.submit(self.get_achievements, char_name=char_name, category=category)
                for char_name in self.characters
            ]
        dates = [_thread.result() for _thread in concurrent.futures.as_completed(_threads)]
        dates = [char_achievs[achi_id] for char_achievs in dates if char_achievs]
        dates = [achiev for achiev in dates if achiev]
        return max(dates)

    def main(self, chars: list[str], achievements: list[str], report_id: str):
        if not achievements:
            return
        self.report_id = report_id
        self.characters = chars
        dates = []
        for achi_id in achievements:
            try:
                _date = self.get_date(achi_id)
                if _date:
                    dates.append(_date)
            except ValueError:
                print('0 ACHI RETURNED:', report_id, achi_id)
        # dates = [self.get_date(achi_id) for achi_id in achievements]
        # dates = [_date for _date in dates if _date]
        if not dates:
            return
        return min(dates)

    @staticmethod
    def save2(name, _new):
        _old = load_json(name)
                
        if _old != _new:
            with open(name, 'w') as f:
                json.dump(_new, f)

    def saveshit(self):
        self.save2(self.cache_achi, self.CACHE)
        self.save2(self.cache_no_char, self.NO_CHAR)

    def create_report_str(self, ):
        current = f"{self.at_index:>7}/{self.total:>7}"

        duration = tm() - self.started
        running = get_time_str(duration)

        e = duration / (self.at_index / self.total) - duration
        eta = get_time_str(e)
        posts = f" | POSTS: {self.POST_REQUESTS:>8}"
        print(f"{current} | {running} | ETA: {eta}{posts} | {self.report_id}")

    def loop1(self, df: DataFrame):
        self.started = tm()
        self.total = len(df)
        dates = {}
        for n, (report_id, row) in enumerate(df.iterrows(), 1):
            self.at_index = n

            names = row['names']
            achievements = row['achievements']
            _date = self.main(names, achievements, report_id)
            if _date:
                self.create_report_str()
                dates[report_id] = _date

        #     if n%50==0:
        #         self.saveshit()
        self.saveshit()

        return dates



TD = timedelta(days=1)

def to_datetime(date: str):
    y, m, d = map(int, date.split('-'))
    return datetime(year=y+2000, month=m, day=d)

def _next_td(_now, _next):
    return (to_datetime(_next) - to_datetime(_now)).days

def correct_dates(dates: dict[str, str], debug=0):
    new_dates = {}
    dates_items = list(dates.items())
    last_report_id, last_date = dates_items[0]
    for (id1, date1), (id2, date2), (id3, date3) in zip(dates_items, dates_items[1:], dates_items[2:]):
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
    
def main_loop(s):
    name = f"data_kills_{s}-{s+1}.pickle"
    name = os.path.join(KILL_DB, name)
    df = main_db.df_read(name)
    df = main_db.has_achievs(df)
    df = df.loc[::25]
    return CURRENT.loop1(df)

if __name__ == "__main__":
    server = "Lordaeron"
    CURRENT = Current(server)
    # CURRENT.category = 15042
    # q = CURRENT.get_achievements("Nomadra")
    # print(q["4632"])

    dates = main_loop(31)
    new_dates = correct_dates(dates)
    # print(dates)
    print(new_dates)
