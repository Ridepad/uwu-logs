# Character info:
# http://armory.warmane.com/character/char_name/server
# BeautifulSoup is like document.querySelector() in js
# Parses basic info like name level guild etc.
# Goes thru each inventory slot, parses id, gems, enchants
# 
# Talents:
# http://armory.warmane.com/character/char_name/server/talents"
# Encoding works by calculating rank of each pair of ranks of talents

import time
from threading import Thread

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from parser_profile_talents import GLYPHS, PlayerTalents
from top_gear import GearDB

done: dict[str, dict] = {}
threads: dict[str, Thread] = {}

HEADERS = {"User-Agent": "WarmaneCharacterParser/2.0; +uwu-logs.xyz"}
TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE"
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


def gen_stats(tags: list[Tag]):
    text: Tag
    for tag in tags:
        for text in tag.find_all(class_="text"):
            try:
                name, value = text.stripped_strings
                yield name, value
            except ValueError:
                pass

def get_talent_rank(talent: Tag):
    return int(talent.text.strip()[0])

def format_glyph_name(t: str):
    return t.replace("Glyph of the ", "").replace("Glyph of ", "")

def get_glyph_name(glyph_div: Tag):
    glyph_link = glyph_div.find("a")
    return format_glyph_name(glyph_link.text)

def gen_glyphs(parent: Tag, class_: str):
    return [
        get_glyph_name(glyph_div)
        for glyph_div in parent.find_all(class_=class_)
    ]


class Specs:
    def __init__(self, name: str, server: str, class_name: str=None):
        self.name = name
        self.server = server
        if class_name:
            self._class_name = class_name
    
    @property
    def profile_soup(self):
        try:
            return self._profile_soup
        except AttributeError:
            url = f"http://armory.warmane.com/character/{self.name}/{self.server}/talents"
            response = requests_get(url, HEADERS)
            self._profile_soup = BeautifulSoup(response.text, "html.parser")
            return self._profile_soup

    @property
    def class_name(self):
        try:
            return self._class_name
        except AttributeError:
            self._class_name = PlayerBaseInfo(self._profile_soup).class_name
            return self._class_name
        
    def both_specs(self):
        return [
            self.get_spec_string(spec_i)
            for spec_i in range(2)
        ]

    def get_allocated_talents(self, spec: int):
        spec_container = self.profile_soup.find(id=f"spec-{spec}")
        trees_table = spec_container.find_all(class_="talent-tree")
        talents: list[list[int]] = [
            [
                get_talent_rank(talent)
                for row in tree.find_all(class_="tier")
                for talent in row.find_all(class_="talent")
            ]
            for tree in trees_table
        ]
        return talents

    def glyphs_by_type(self, spec: int):
        spec_glyphs_tag = self.profile_soup.find("div", attrs={"data-glyphs": f"{spec}"})
        return {
            "major": gen_glyphs(spec_glyphs_tag, class_="major"),
            "minor": gen_glyphs(spec_glyphs_tag, class_="minor"),
        }

    def get_glyphs(self, spec: int):
        g = self.glyphs_by_type(spec)
        return g["major"] + g["minor"]
    
    def make_glyph_string(self, spec: int):
        glyphs = self.get_glyphs(spec)
        return GLYPHS.make_glyph_string(self.class_name, glyphs)
    
    def make_talents_string(self, spec: int):
        talent_trees = self.get_allocated_talents(spec)
        return PlayerTalents(self.class_name).spec_data(talent_trees)

    def get_spec_string(self, spec: int):
        glyph_str = self.make_glyph_string(spec)
        talents_data = self.make_talents_string(spec)
        talents_data.add_glyphs_to_talent_string(glyph_str)
        return talents_data.as_list()


class Profile:
    def __init__(self, name: str, server: str):
        self.name = name
        self.server = server
        self.profile_url = f"http://armory.warmane.com/character/{name}/{server}"
    
    @property
    def profile_soup(self):
        try:
            return self._profile_soup
        except AttributeError:
            response = requests_get(self.profile_url, HEADERS)
            self._profile_soup = BeautifulSoup(response.text, "html.parser")
            return self._profile_soup


class PlayerBaseInfo(Profile):
    @property
    def info(self):
        try:
            return self._info
        except AttributeError:
            pass
        base_info_str = self.profile_soup.find(class_="level-race-class").text
        base_info_str = base_info_str.replace("Level", "").strip()
        base_info_str = base_info_str.split(",", 1)[0]
        self._info = base_info_str.split(" ")
        return self._info
    
    @property
    def guild_name(self):
        return self.profile_soup.find(class_="guild-name").text
    
    @property
    def level(self):
        return self.info[0]
    
    @property
    def class_name(self):
        class_name = self.info[-1]
        if class_name in DOUBLE_CLASSES:
            class_name = " ".join(self.info[-2:])
        return class_name

    @property
    def race(self):
        race = self.info[1]
        if race in DOUBLE_RACES:
            race = " ".join(self.info[1:3])
        return race


class PlayerGear(Profile):
    def parse_gear(self):
        equipment = self.profile_soup.find(class_="item-model").find_all("a")
        return [
            self.parse_slot(slot)
            for slot in equipment
        ]
    
    @staticmethod
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


class PlayerProfessions(Profile):
    def get_profs(self):
        stats = self.profile_soup.find(id="character-profile").find(class_="information-right")
        tags = stats.find_all(class_="profskills")
        return [
            [name, value.split(maxsplit=1)[0]]
            for name, value in gen_stats(tags)
        ]


class ProfileParser(
    PlayerBaseInfo,
    PlayerProfessions,
    PlayerGear,
):
    def talents(self):
        return Specs(self.name, self.server, self.class_name).both_specs()
    
    def make(self):
        return {
            "level": self.level,
            "race": self.race,
            "class": self.class_name,
            "guild": self.guild_name,
            "specs": self.talents(),
            "profs": self.get_profs(),
            "gear_data": self.parse_gear(),
        }


def get_profile(player_name, server):
    return ProfileParser(player_name, server).make()

def parse_and_save_player(player: dict[str, str]):
    server = player["server"]
    player_name = player["name"]

    new_profile = get_profile(player_name, server)
    if not new_profile:
        return
    
    GearDB(server).update_player_row(player_name, new_profile)

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



def test1():
    player_name = "Nomadra"
    server = "Lordaeron"

    new_profile = ProfileParser(player_name, server).make()
    print(new_profile)

if __name__ == "__main__":
    test1()
