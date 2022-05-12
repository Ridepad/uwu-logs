import json
import os
from time import time as tm, sleep
from typing import Dict, List

import bs4
import requests


real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
TMP_CACHE = os.path.join(DIR_PATH, "tmp_cache")

LABELS = ['names', 'guilds', 'factions', 'races', 'classes', 'specs']

URL = 'http://armory.warmane.com/pveladder/Lordaeron/details/'
HEADERS = {'User-Agent': "Me: Can I use script to GET some data? / Admin: No, otherwise I'll ban / Ban: if 'python--requests' in request.headers['User-Agent'] return 404"}


class Current:
    def new_value(self, index: int, done: int, batch: int):
        self.started = tm()
        self.at_index = index*batch
        self.done = done
        self.to_do = (batch - done) or 1
        self.batch = batch
        self.redirects = 0
        self.ALL_DATA = {}
        print("\nNEXT:", self.at_index)

    def add_report(self, report_id, data):
        if not data:
            self.to_do -= 1
            print("\nREPORT EMPTY:", report_id)
            return

        self.ALL_DATA[report_id] = data
        self.create_report_str()

    @staticmethod
    def get_time_str(t):
        t = int(t)
        seconds = t % 60
        minutes = t // 60 % 60
        hours = minutes // 60
        return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"

    def create_report_str(self):
        reports = len(self.ALL_DATA)
        current = f"{reports:>5}/{self.to_do:>5}"

        duration = tm() - self.started
        running = self.get_time_str(duration)

        eta = duration / (reports / self.to_do) - duration
        eta = self.get_time_str(eta)
        print(f"\r{current} | {running} | ETA: {eta}", end="")

    def save_json(self):
        if not self.ALL_DATA:
            return self.done
        current = self.at_index // self.batch
        combined = f"data_kills_{current}-{(current+1)}.json"
        name = os.path.join(TMP_CACHE, combined)
        _data = load_json(name)
        _data.update(self.ALL_DATA)
        with open(name, 'w') as f:
            json.dump(_data, f)
        return len(_data)

CURRENT = Current()


def load_json(name):
    try:
        with open(name) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def get_page(kill_id, attempt=0):
    if attempt > 2:
        return
    try:
        for _ in range(5):
            page = requests.get(f"{URL}{kill_id}", headers=HEADERS, timeout=2, allow_redirects=False)
            if page.status_code != 503:
                break
            sleep(.5)
        sc = page.status_code
        if sc == 200:
            return page.text
        print(f"\n{sc} ERROR:", kill_id, "TRIES:", attempt)
        if sc == 302:
            CURRENT.redirects += 1
            return
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
        print("\nTIMEOUT:", kill_id, "TRIES:", attempt)
    return get_page(kill_id, attempt+1)

def get_fight_duration(soup: bs4.BeautifulSoup):
    t = soup.find(class_="duration")
    t = t.text.strip()
    minutes, seconds = t.split(":")
    return int(minutes)*60 + int(seconds)

def get_fight_name(soup: bs4.BeautifulSoup):
    t = soup.find(class_="name")
    return t.text.strip()

def get_fight_specs(soup: bs4.BeautifulSoup):
    s = soup.find_all(class_="specifications")
    raid_type, *attempts = [x.text.strip().split() for x in s]
    attempts = int(attempts[0][3]) if attempts else 0
    size = int(raid_type[0])
    difficulty = int("Heroic" in raid_type)
    return size, difficulty, attempts

def get_player_info(soup: bs4.BeautifulSoup):
    name, guild = [td.text for td in soup.find_all("td")[:2]]
    other = [img.get('alt') for img in soup.find_all("img")]
    player = [name, guild] + other
    spec = player[-1]
    if not spec:
        if "Mage" in player:
            spec = "Fire"
        elif "Shaman" in player:
            spec = "Restoration"
        player[-1] = spec
    return player

def players_data(soup: bs4.BeautifulSoup):
    tbody = soup.find(id="data-table-list")
    players = [get_player_info(row) for row in tbody.find_all("tr")]
    players = zip(*players)
    return {title: list(p_data) for title, p_data in zip(LABELS, players)}

def get_fight_achievs(soup: bs4.BeautifulSoup):
    return [a.get('href').split('=')[-1] for a in soup.find_all(target="_blank")]

def is_guild(players: Dict[str, List[str]], size):
    guilds = players['guilds']
    guild = max(guilds, key=guilds.count)
    qualify = int(size) // 5 * 4
    b = guilds.count(guild) >= qualify
    return int(b)

def format_report_data(soup: bs4.BeautifulSoup):
    players = players_data(soup)
    if not players:
        return
    
    size, difficulty, attempts = get_fight_specs(soup)
    report_data = {
        "boss": get_fight_name(soup),
        "size": size,
        "difficulty": difficulty,
        "duration": get_fight_duration(soup),
        "attempts": attempts,
        "guild": is_guild(players, size),
        "achievements": get_fight_achievs(soup),
    }
    report_data.update(players)
    return report_data

def get_report_info(report_id):
    page = get_page(report_id)
    if not page:
        return

    soup = bs4.BeautifulSoup(page, features="html.parser")
    crop = soup.find(class_="content-inner")
    return format_report_data(crop)

def main4(start, redo, batch=1000):
    finish = start+1
    name = os.path.join(TMP_CACHE, f"data_kills_{start}-{finish}.json")
    done = load_json(name)
    done = set(map(int, done)) - set(redo)

    CURRENT.new_value(start, len(done), batch)

    for report_id in range(start*batch, finish*batch):
        if report_id in done and report_id not in redo:
            continue
        report_data = get_report_info(report_id)

        CURRENT.add_report(report_id, report_data)

        if CURRENT.redirects > 5:
            break

    _L = CURRENT.save_json()
    if _L > batch * 0.9:
        return main4(finish, redo, batch)

def get_s(name: str):
    z = name.split('-')[0].split('_')[-1]
    return int(f"{z:0<4}")

def get_all_files(ext, dir='.'):
    files = next(os.walk(dir))[2]
    return [file for file in files if file.rsplit('.', 1)[-1] == ext][::-1]

def get_last_n():
    q = get_all_files('json', dir=TMP_CACHE)
    try:
        return get_s(q[0]) // 10 * 10
    except IndexError:
        return 2500

def main19(s):
    full_name = os.path.join(TMP_CACHE, f"data_kills_{s}-{s+1}.json")
    js = load_json(full_name)
    if not js:
        return

    new_js = {}
    for report_id, data in js.items():
        try:
            soup = bs4.BeautifulSoup(data, features="html.parser")
            report_data = format_report_data(soup)
            if not report_data:
                print('report empty:', report_id)
                continue
            new_js[report_id] = report_data
        except:
            continue

    new_js = dict(sorted(new_js.items()))
    print("TOTAL REPORTS:", len(new_js))
    old_name = f"{full_name}.old"
    os.rename(full_name, old_name)
    with open(full_name, 'w') as j:
        json.dump(new_js, j)

if __name__ == "__main__":
    last = 1470
    last = 3345
    last = 2780
    last = 3365
    _redo = []
    main4(last, _redo)
    input()