import concurrent.futures
import json
import os
import pickle
import re
from datetime import datetime
from time import time as tm
from typing import Dict, List
from pandas import DataFrame
import requests
from bs4 import BeautifulSoup

import main
from constants_WBF import CATEGORIES, running_time

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)

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


def to_dt(s: str):
    try:
        _date = s.text.strip()
        m, d, y = re.findall('(\d\d)/(\d\d)/\d\d(\d\d)', _date)[0]
        return f"{y}-{m}-{d}"
    except AttributeError:
        return ""

def get_time_str(t):
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = minutes // 60
    return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"


class Current:
    cache_no_char = os.path.join(DIR_PATH, "cache_no_char.json")
    NO_CHAR: Dict[str, str] = load_json(cache_no_char)

    cache_achi = os.path.join(DIR_PATH, "cache_achi.json")
    CACHE: Dict[str, Dict[str, Dict[str, str]]] = load_json(cache_achi)

    POST_REQUESTS = 0

    def __init__(self, server: str):
        self.server = server

    def get_achievs(self, char_name: str):
        url = f"http://armory.warmane.com/character/{char_name}/{self.server}/achievements"
        req = requests.post(url, data={"category": self.category}, headers=HEADERS)
        self.POST_REQUESTS += 1
        try:
            response = req.json()
            if 'content' in response:
                return response['content']
        except:
            self.NO_CHAR[char_name] = self.report_id
            print(f'\n{req.status_code} | Char not found: {char_name}')
            return

    def get_all(self, char_name: str):
        if char_name in self.NO_CHAR:
            return
        char_achievs = self.CACHE.setdefault(char_name, {}).setdefault(str(self.category), {})
        if not char_achievs:
            achievs = self.get_achievs(char_name)
            if not achievs:
                return
            achievs = BeautifulSoup(achievs, features="html.parser")
            for achi in achievs.find_all(class_="achievement"):
                _id = achi["id"].replace('ach', '')
                _date = achi.find(class_="date")
                char_achievs[_id] = to_dt(_date)
        return char_achievs

    def get_date(self, achi_id: str):
        self.category = find_category(achi_id)

        with concurrent.futures.ThreadPoolExecutor(3) as executor:
            _threads = [
                executor.submit(self.get_all, char_name=char_name)
                for char_name in self.characters
            ]
        dates = [_thread.result() for _thread in concurrent.futures.as_completed(_threads)]
        dates = [char_achievs[achi_id] for char_achievs in dates if char_achievs]
        return max(dates)

    @running_time
    def main(self, chars: List[str], achievements: List[str], report_id: str):
        if not achievements:
            return "no ahievs"
        self.report_id = report_id
        self.characters = chars
        dates = [self.get_date(achi_id) for achi_id in achievements]
        if not dates:
            return "no ahievs"
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

    def create_report_str(self):
        current = f"{self.at_index:>7}/{self.total:>7}"

        duration = tm() - self.started
        running = get_time_str(duration)

        e = duration / (self.at_index / self.total) - duration
        eta = get_time_str(e)
        posts = f" | POSTS: {self.POST_REQUESTS:>8}"
        v = f" | {self.df_index} | {self.date}"
        print(f"\r{current} | {running} | ETA: {eta}{posts}{v} | ", end="")

    def loop1(self, df: DataFrame):
        self.started = tm()
        self.total = len(df)
        for n, (report_id, row) in enumerate(df.iterrows(), 1):
            self.at_index = n
            self.df_index = report_id

            names = row['names']
            achievements = row['achievements']
            # try:
            d = self.main(names, achievements, report_id)
            self.date = d
            self.create_report_str()
            # except Exception as e:
                # print(e)
                # print(report_id, achievements, names)
                # input()
            if n%100==0:
                self.saveshit()
        self.saveshit()


# def get_achievs(category: int, char_name: str, server: str):
#     url = f"http://armory.warmane.com/character/{char_name}/{server}/achievements"
#     req = requests.post(url, data={"category": category}, headers=HEADERS)
#     response = req.text
#     if response.startswith('{"content":'):
#         html = json.loads(response)
#         return html['content']
#     NO_CHAR.add(char_name)
#     print(f'\n{req.status_code} | Char not found: {char_name}')
#     return

# def has_achi(category: int, achi_id: str, char_name: str, server="Lordaeron"):
#     if char_name in NO_CHAR:
#         return
#     char_achievs = CACHE.setdefault(char_name, {}).setdefault(str(category), {})
#     if not char_achievs:
#         achievs = get_achievs(category, char_name, server)
#         POST_REQUESTS[0] += 1
#         if not achievs:
#             return
#         achievs = BeautifulSoup(achievs, features="html.parser")
#         for achi in achievs.find_all(class_="achievement"):
#             _id = achi["id"].replace('ach', '')
#             _date = achi.find(class_="date")
#             char_achievs[_id] = to_dt(_date)
#     return char_achievs[achi_id]

# def get_date(chars: List[str], achi_id: str):
#     category = find_category(achi_id)
#     with concurrent.futures.ThreadPoolExecutor(3) as executor:
#         _threads = [
#             executor.submit(has_achi, category=category, achi_id=achi_id, char_name=char_name)
#             for char_name in chars
#         ]
#     dates = [_thread.result() for _thread in concurrent.futures.as_completed(_threads)]
#     dates = [x for x in dates if x]
#     return max(dates)

# @running_time
# def main(chars: List[str], achievements: List[str]):
#     dates = [get_date(chars, achi_id) for achi_id in achievements]
#     if not dates:
#         return "no ahievs"
#     return min(dates)
#     # dt = min(dates)
#     # return dt_to_str(dt)

if __name__ == "__main__":
    server = "Lordaeron"
    CURRENT = Current(server)
    # CURRENT.category = 15042
    # q = CURRENT.get_all("Nomadra")
    # print(q["4632"])
    
    def main1(s):
        name = f"data_kills_{s}-{s+10}"
        df = main.get_df(name)
        df = main.has_achievs(df)
        df = df.loc[::50]
        CURRENT.loop1(df)

    main1(300)
