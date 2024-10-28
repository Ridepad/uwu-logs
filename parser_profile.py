# Character info:
# http://armory.warmane.com/character/char_name/server
# BeautifulSoup is like document.querySelector() in js
# Parses basic info like name level guild etc.
# Goes thru each inventory slot, parses id, gems, enchants
# 
# Talents:
# http://armory.warmane.com/character/char_name/server/talents"
# Encoding works by calculating rank of each pair of ranks of talents
# idk why i just translated it from lua code
# couldnt figure out glyphs cz it seemed random to me


import time
from threading import Thread

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from top_gear import GearDB

done: dict[str, dict] = {}
threads: dict[str, Thread] = {}

HEADERS = {"User-Agent": "WarmaneCharacterParser/2.0; +uwu-logs.xyz"}
TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE"
CLASS_NAME_SPEC = "specialization"
CLASS_NAME_PROF = "profskills"
FORMAT_FUNCTION = {
    CLASS_NAME_SPEC: lambda v: v.replace(" ", ""),
    CLASS_NAME_PROF: lambda v: v.split(maxsplit=1)[0],
}
DOUBLE_RACES = [
    "Night", # Night Elf
    "Blood", # Blood Elf
]
DOUBLE_CLASSES = [
    "Knight", # Death Knight
]
CLASSES_ORDERED = [
    "Druid",
    "Hunter",
    "Mage",
    "Paladin",
    "Priest",
    "Rogue",
    "Shaman",
    "Warlock",
    "Warrior",
    "Death Knight",
]

def player_id(player: dict):
    return f"{player['name']}--{player['server']}"

def is_valid_response(response: requests.Response):
    return response is not None and "guild-name" in response.text

def requests_get(page_url, headers, timeout=2, attempts=3):
    for _ in range(attempts):
        try:
            page = requests.get(page_url, headers=headers, timeout=timeout, allow_redirects=False)
            if page.status_code == 200:
                return page
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            time.sleep(2)
    
    # LOGGER.error(f"Failed to load page: {page_url}")
    return None


def parse_slot(slot: Tag):
    if not slot.get("rel"): # Empty slot
        return {}
    # rel="item=51290&ench=3820&gems=3621:3520:0&transmog=22718"
    item_properties_list = slot["rel"][0].split("&")
    # item_properties = ["item=51290", "ench=3820", "gems=3621:3520:0", "transmog=22718"]
    item_properties = dict(property.split("=") for property in item_properties_list)
    # item_properties = {"item": "51290", "ench": "3820", "gems": "3621:3520:0", "transmog": "22718"}
    item_properties["gems"] = item_properties.get("gems", "0:0:0").split(":")
    # item_properties = {"item": "51290", "ench": "3820", "gems": ["3621","3520","0"], "transmog": "22718"}
    return item_properties

def get_gear(profile: BeautifulSoup):
    equipment = profile.find(class_="item-model").find_all("a")
    return [parse_slot(slot) for slot in equipment]

def get_stats_data(stats: Tag, class_name: str) -> dict[str, str]:
    if class_name not in FORMAT_FUNCTION:
        return []

    text: Tag
    data = []
    format_value = FORMAT_FUNCTION[class_name]
    for tag in stats.find_all(class_=class_name):
        for text in tag.find_all(class_="text"):
            try:
                name, value = text.stripped_strings
                data.append([name, format_value(value)])
            except ValueError:
                pass

    return data

def _get_race(level_race_class: list[str]):
    race = level_race_class[1]
    if race in DOUBLE_RACES:
        race = " ".join(level_race_class[1:3])
    return race

def _get_class(level_race_class: list[str]):
    class_ = level_race_class[-1]
    if class_ in DOUBLE_CLASSES:
        class_ = " ".join(level_race_class[-2:])
    return class_

def get_basic_info(profile: BeautifulSoup):
    level_race_class_full = profile.find(class_="level-race-class").text.strip()
    level_race_class = level_race_class_full.split(",", 1)[0].split(" ")
    if "Level" in level_race_class:
        level_race_class.remove("Level")
    
    return {
        "level": level_race_class[0],
        "race": _get_race(level_race_class),
        "class": _get_class(level_race_class),
    }

def get_class_prefix(soup: BeautifulSoup):
    basic_info = get_basic_info(soup)
    class_i = CLASSES_ORDERED.index(basic_info["class"])
    return TALENTS_ENCODE_STR[class_i * 3]

def get_talent_rank(talent: Tag):
    return int(talent.text.strip()[0])

def convert_to_string(tree: Tag):
    talents: list[int] = [
        get_talent_rank(talent)
        for row in tree.find_all(class_="tier")
        for talent in row.find_all(class_="talent")
    ]

    if len(talents) & 1:
        talents.append(0)
    
    z = zip(talents[::2], talents[1::2])
    g = (TALENTS_ENCODE_STR[r1 * 6 + r2] for r1, r2 in z)
    s = "".join(g)
    
    if s[-1] == TALENTS_ENCODE_STR[0]:
        return s.rstrip(TALENTS_ENCODE_STR[0]) + "Z"
    return s

def convert_spec_to_string(spec: Tag):
    trees = spec.find_all(class_="talent-tree")
    tree_gen = (convert_to_string(tree) for tree in trees)
    return "".join(tree_gen).rstrip("Z")

def get_talents_strings(char_name: str, server: str):
    url = f"http://armory.warmane.com/character/{char_name}/{server}/talents"
    response = requests_get(url, HEADERS)
    if not is_valid_response(response):
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    CLASS_PREFIX = get_class_prefix(soup)
    return [
        CLASS_PREFIX + convert_spec_to_string(spec)
        for spec in soup.find_all(class_="talents-container")
    ]


def get_profile(char_name: str, server: str):
    char_url = f"http://armory.warmane.com/character/{char_name}/{server}"
    response = requests_get(char_url, HEADERS)
    if not is_valid_response(response):
        return {}
    
    soup = BeautifulSoup(response.text, "html.parser")
    stats = soup.find(id="character-profile").find(class_="information-right")
    talents = get_talents_strings(char_name, server)
    
    profile_dict = get_basic_info(soup)
    profile_dict["guild"] = soup.find(class_="guild-name").text
    profile_dict["specs"] = get_stats_data(stats, CLASS_NAME_SPEC)
    profile_dict["profs"] = get_stats_data(stats, CLASS_NAME_PROF)
    profile_dict["talents"] = talents
    profile_dict["gear_data"] = get_gear(soup)
    return profile_dict

def parse_and_save_player(player: dict[str, str]):
    server = player["server"]
    player_name = player["name"]

    new_profile = get_profile(player_name, server)
    GearDB(server).update_player(player_name, new_profile)

### Used to assure single instance of parser

def wait_for_thread(t: Thread):
    try:
        t.start()
    except RuntimeError:
        pass

    t.join()

def parse_and_save_player_wrap(player):
    player_profile = parse_and_save_player(player)
    id = player_id(player)
    done[id] = player_profile
    return player_profile

def parse_and_save_wrap(player: dict):
    id = player_id(player)
    if id in done:
        return done[id]
    
    if id in threads:
        t = threads[id]
    else:
        t = Thread(target=parse_and_save_player_wrap, args=(player, ))
        threads[id] = t

    wait_for_thread(t)
    return done[id]



def __test():
    d = {
        "name": "Nomadra",
        "server": "Lordaeron",
    }
    parse_and_save_player(d)

def __test2():
    chars = [
        "Nomadra",
        "Safiyah",
        # "Meownya",
    ]
    for char_name in chars:
        url = f"https://armory.warmane.com/api/character/{char_name}/Lordaeron/"
        r = requests.get(url, headers=HEADERS)
        print()
        print(r.text)
        time.sleep(3)

if __name__ == "__main__":
    __test()
