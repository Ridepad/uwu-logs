import os
from time import sleep, time

import bs4
import requests

from constants_WBF import (CLASSES_LIST, DIR_PATH, FACTION, RACES_LIST,
                           SPECS_LIST, json_read, json_write)

TMP_CACHE = os.path.join(DIR_PATH, "tmp_cache")


URL = 'http://armory.warmane.com/pveladder/Lordaeron/details/'
USER_AGENT = "Pls implement api with rate limits instead of nuking website to oblivion and removing the simple way of parsing, im still learning best to cause as low load as possible, sowwy"
USER_AGENT = "Me: Can I use script to GET some data? / Admin: No, otherwise I'll ban / Ban: nuke_half_website_to_combat_parsing = true"
HEADERS = {'User-Agent': USER_AGENT}
DESIRED_STATUS_CODES = [200, 302, 404]
RETRY_TIMEOUT = 1

NAMES_LABEL = 'names'
GUILDS_LABEL = 'guilds'
FACTIONS_LABEL = 'factions'
RACES_LABEL = 'races'
CLASSES_LABEL = 'classes'
SPECS_LABEL = 'specs'
PLAYER_LABELS = [NAMES_LABEL, GUILDS_LABEL, FACTIONS_LABEL, RACES_LABEL, CLASSES_LABEL, SPECS_LABEL]
BASE_PLAYERS = {title: [] for title in PLAYER_LABELS}

class Current:
    delay = 0.52
    def new_value(self, index: int, done: int, batch: int):
        self.started = time()
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

        duration = time() - self.started
        running = self.get_time_str(duration)

        eta = duration / (reports / self.to_do) - duration
        eta = self.get_time_str(eta)
        print(f"\r{current} | {running} | ETA: {eta}", end="")

    def save_json(self):
        if not self.ALL_DATA:
            return self.done
        
        current = self.at_index // self.batch
        current_name = os.path.join(TMP_CACHE, f"data_kills_{current}-{(current+1)}.json")
        _data = json_read(current_name)
        _data.update(self.ALL_DATA)

        if self.redirects > 5:
            print('\nTrimmed 30 most recent reports')
            _data = dict(list(_data.items())[:-30])

        json_write(current_name, _data, indent=None)
        # with open(current_name, 'w') as f:
            # json.dump(_data, f)
        return len(_data)

CURRENT = Current()


def parse_page_until_status_code(url):
    for _ in range(5):
        try:
            page = requests.get(url, headers=HEADERS, timeout=RETRY_TIMEOUT, allow_redirects=False)
            if page.status_code in DESIRED_STATUS_CODES:
                break
        except requests.exceptions.ReadTimeout:
            pass
        sleep(CURRENT.delay)
    return page

def get_page(kill_id, attempt=0):
    if attempt > 2:
        return
    
    try:
        page = parse_page_until_status_code(f"{URL}{kill_id}")
        sc = page.status_code
        if sc == 200:
            return page.text
        print(f"\n{sc} ERROR:", kill_id, "TRIES:", attempt)
        if sc == 302:
            CURRENT.redirects += 1
            return
    except requests.exceptions.ConnectionError as e:
        print("\nCONNECTION ERROR:", kill_id, "TRIES:", attempt, "\nMSG:", e)
    
    return get_page(kill_id, attempt+1)

def get_fight_duration(soup: bs4.BeautifulSoup):
    dur_elem = soup.find(class_="duration")
    dur_text = dur_elem.text.strip()
    minutes, seconds = dur_text.split(":")
    return int(minutes)*60 + int(seconds)

def get_fight_name(soup: bs4.BeautifulSoup):
    boss_elem = soup.find(class_="name")
    return boss_elem.text.strip()

def get_fight_specs(soup: bs4.BeautifulSoup):
    spec_elems = soup.find_all(class_="specifications")
    raid_type, *wipes = [elem.text.strip().split() for elem in spec_elems]
    wipes = int(wipes[0][3]) if wipes else 0
    size = int(raid_type[0])
    difficulty = int("Heroic" in raid_type)
    return size, difficulty, wipes

def get_player_info(soup: bs4.BeautifulSoup):
    name, guild = [td.text for td in soup.find_all("td")[:2]]
    faction, race, class_, spec = [img.get('alt') for img in soup.find_all("img")]
    # faction = FACTION[faction]
    if not spec:
        if class_ == "Mage":
            spec = "Fire"
        elif class_ == "Shaman":
            spec = "Restoration"
        else:
            spec = ""
    return [name, guild, faction, race, class_, spec]

def get_fight_achievs(soup: bs4.BeautifulSoup):
    achi = [a.get('href').split('=')[-1] for a in soup.find_all(target="_blank")]
    achi = [a for a in achi if a]
    return list(map(int, achi))


def get_players_data(soup: bs4.BeautifulSoup):
    tbody = soup.find(id="data-table-list")
    players = [get_player_info(row) for row in tbody.find_all("tr")]
    # print(players)
    if not players:
        return BASE_PLAYERS
    players = zip(*players)
    return {title: list(p_data) for title, p_data in zip(PLAYER_LABELS, players)}

def format_players(players_data):
    classes = players_data[CLASSES_LABEL]
    specs = players_data[SPECS_LABEL]
    for i, (class_name, spec_name) in enumerate(zip(classes, specs)):
        class_index = CLASSES_LIST.index(class_name)
        spec_index = SPECS_LIST[class_name].index(spec_name)
        classes[i] = class_index
        specs[i] = class_index*4 + spec_index
    rnames = players_data[RACES_LABEL]
    races = [RACES_LIST.index(rname) for rname in rnames]


    gnames = players_data[GUILDS_LABEL]
    gi = sorted(set(gnames))
    guilds = [gi.index(gname) for gname in gnames]

    fnames = players_data[FACTIONS_LABEL]
    factions = [FACTION.index(fname) for fname in fnames]
    return {
        'g': gi,
        'pn': players_data[NAMES_LABEL],
        'pg': guilds,
        'pf': factions,
        'pr': races,
        'pc': classes,
        'ps': specs,
    }

def format_report_data(soup: bs4.BeautifulSoup):
    size, difficulty, wipes = get_fight_specs(soup)
    report_data = {
        "b": get_fight_name(soup),
        "s": size,
        "m": difficulty,
        "t": get_fight_duration(soup),
        "w": wipes,
        "a": get_fight_achievs(soup),
    }
    players = get_players_data(soup)
    report_data |= format_players(players)
    return report_data

def get_report_info(report_id):
    page = get_page(report_id)
    if not page:
        return

    soup = bs4.BeautifulSoup(page, features="html.parser")
    crop = soup.find(class_="content-inner")
    return format_report_data(crop)

def main_parser(start, batch=1000, stop=None, redo=None):
    if stop is not None and start == stop: return
    if redo is None: redo = set()
    finish = start+1
    name = os.path.join(TMP_CACHE, f"data_kills_{start}-{finish}.json")
    done = json_read(name)
    done = set(map(int, done)) - set(redo)

    CURRENT.new_value(start, len(done), batch)

    for report_id in range(start*batch, finish*batch):
        if report_id in done and report_id not in redo:
            continue

        report_data = get_report_info(report_id)
        CURRENT.add_report(report_id, report_data)

        if CURRENT.redirects > 5:
            break

    last_parse_count = CURRENT.save_json()
    if last_parse_count > batch * 0.95:
        return main_parser(finish, batch, stop, redo)

def main_main():
    redo = []
    redo = [
        # 3523793, 3523824, 3523860, 3523886, 3523927, 3523949, 3524038, 3526766, 3526789, 3526812, 3526827, 3526841, 3526854, 3526863,
        # 3531675, 3531713, 3531734, 3531753, 3531772, 3531815, 3531835, 3531866, 3531892, 3531904, 3531929, 3531942, 3531961
    ]
    # CURRENT.delay = .8
    # q = get_report_info(3275178)
    # print(q[NAMES_LABEL])
    # import json
    # with open('all_redo4.json', 'r') as f:
    #     redo = json.load(f)
    # print(redo)
    stop = 3300
    stop = 3575
    stop = None
    start = 3689
    # last = 3409
    # last = 3100
    main_parser(start, stop=stop, redo=redo)
    input()

if __name__ == "__main__":
    # get_report_info(3523539)
    # get_report_info(3643003)
    # get_report_info(3643424)
    main_main()
