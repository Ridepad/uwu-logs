import json
import requests
import re
import time
from datetime import datetime, timedelta

import logs_calendar
from c_path import Directories, PathExt
from h_debug import Loggers
from top_gear import Columns, GearDB
from parser_profile_talents import PlayerTalentsRG

LOGGER = Loggers.raging_gods

IS_OLD_DT = datetime.now() - timedelta(hours=12)
IS_OLD_DT_TS = IS_OLD_DT.timestamp()

RISING_GODS = "Rising-Gods"
DATABASE = GearDB(RISING_GODS, new=True)

TEMP_PROFILE_DATA_DIR = Directories.main.new_child("temp").new_child(RISING_GODS)
GEM_TO_ENCH_DICT_PATH = Directories.main / "x_gem_to_ench.json"

URL_RG_PROFILE = "https://db.rising-gods.de/?profile=eu.rising-gods"
URL_RG_PROFILE_LOAD = "https://db.rising-gods.de/?profile=load&id"

HEADERS = {"User-Agent": "CharacterParserRG/1.1; +uwu-logs.xyz"}

PROFS = {
    "171": "Alchemy",
    "164": "Blacksmithing",
    "333": "Enchanting",
    "202": "Engineering",
    "182": "Herbalism",
    "773": "Inscription",
    "755": "Jewelcrafting",
    "165": "Leatherworking",
    "186": "Mining",
    "393": "Skinning",
    "197": "Tailoring",
}
PROFS_SECONDARY = {
    "185": "Cooking",
    "129": "First Aid",
    "356": "Fishing",
    "762": "Riding",
}

CLASSES_ORDERED_DB = [
    "",
    "Warrior",
    "Paladin",
    "Hunter",
    "Rogue",
    "Priest",
    "Death Knight",
    "Shaman",
    "Mage",
    "Warlock",
    "",
    "Druid",
]
RACES_ORDERED = [
    "",
    "Human",
    "Orc",
    "Dwarf",
    "Night Elf",
    "Undead",
    "Tauren",
    "Gnome",
    "Troll",
    "Goblin",
    "Blood Elf",
    "Draenei",
]
GEAR_ORDERED = [
    "1",
    "2",
    "3",
    "15",
    "5",
    "4",
    "19",
    "9",
    "10",
    "6",
    "7",
    "8",
    "11",
    "12",
    "13",
    "14",
    "16",
    "17",
    "18",
]

def requests_get(page_url, timeout_mult=2, attempts=5):
    for attempt in range(1, attempts+1):
        try:
            response = requests.get(
                page_url,
                headers=HEADERS,
                timeout=attempt * timeout_mult,
                allow_redirects=False,
            )
            if response.status_code == 200:
                return response.text
            if response.status_code == 404:
                return
            # print("! ERROR1", attempt, response.status_code)
            msg = f"ATTEMPT: {attempt:>2} | STATUS {response.status_code} | {page_url}"
            LOGGER.warning(msg)
        except requests.exceptions.ConnectionError:
            msg = f"ATTEMPT: {attempt:>2} | CONNECTION ABORTED {page_url}"
            LOGGER.warning(msg)
        except requests.exceptions.ReadTimeout:
            msg = f"ATTEMPT: {attempt:>2} | CONNECTION TIMEOUT {page_url}"
            LOGGER.warning(msg)
        except Exception:
            msg = f"ATTEMPT: {attempt:>2} | OTHER"
            LOGGER.exception(msg)
        
        time.sleep(2)
    
    return None


class GemToEnch:
    cls_dict = {
        "changed": False,
    }
    gem_to_ench_dict = GEM_TO_ENCH_DICT_PATH.json()

    def gem_to_ench(self, gem_id):
        gem_id = str(gem_id)
        if gem_id in self.gem_to_ench_dict:
            return self.gem_to_ench_dict[gem_id]
        if gem_id == "0" or gem_id == "None":
            self.gem_to_ench_dict[gem_id] = "0"
            return "0"
        
        url = f"https://wotlk.evowow.com/?item={gem_id}"
        response_text = requests_get(url)
        if not response_text:
            LOGGER.warning(f"{gem_id:>5} | ERROR MISSING GEM DATA")
            return "0"
        
        ench_index = response_text.find("?enchantment=")
        ench_str = response_text[ench_index:ench_index+25]
        ench_id = re.findall("(\d{3,4})", ench_str)[0]
        self.gem_to_ench_dict[gem_id] = ench_id
        self.cls_dict["changed"] = True
        LOGGER.debug(f"{gem_id:>5} | {ench_id:>5} | NEW GEM")
        return ench_id

    def write_cache(self):
        if self.cls_dict["changed"]:
            LOGGER.debug(f"Saved new gem data")
            GEM_TO_ENCH_DICT_PATH.json_write(self.gem_to_ench_dict)
        self.cls_dict["changed"] = False


def rg_url(name):
    return f"{URL_RG_PROFILE}.{name}"

def get_now_timestamp():
    return int(datetime.now().timestamp() * 1000)
def rg_url_full(char_id):
    timestamp = get_now_timestamp()
    return f"{URL_RG_PROFILE_LOAD}={char_id}&{timestamp}"

def profile_is_fresh(p: PathExt):
    if not p.is_file():
        return False
    return p.mtime > IS_OLD_DT_TS

def get_profile(name: str, forced: bool=False):
    profile_path = TEMP_PROFILE_DATA_DIR / f"{name}.txt"
    if not forced and profile_is_fresh(profile_path):
        LOGGER.debug(f"{name} | from cache")
        return profile_path.read_text()
    
    url = rg_url(name)
    try:
        profile1 = requests_get(url)
    except AttributeError:
        LOGGER.warning(f"{name:12} | response empty 1 | AttributeError")
        return

    if not profile1:
        LOGGER.warning(f"{name:12} | response empty 2 | not profile1")
        return
    
    try:
        profile_number_id = re.findall("profilah-generic.*?(\d+)", profile1)[0]
    except IndexError:
        LOGGER.warning(f"{name:12} | id wasnt found")
        return

    LOGGER.debug(f"{name:12} | {profile_number_id:>12} | profile_number_id")
    
    url = rg_url_full(profile_number_id)
    profile_txt = requests_get(url)
    if not profile_txt:
        LOGGER.warning(f"{name:12} | response empty 3 | not profile_txt")
        return
    
    profile_path.write_text(profile_txt)
    
    return profile_txt



def parse_slot(slot: list[str]):
    if not slot: # Empty slot
        return {}

    item_id = slot[0]
    ench_id = slot[2]
    _g2e = GemToEnch().gem_to_ench
    try:
        gems = list(map(_g2e, slot[4:7]))
    except Exception:
        LOGGER.exception(f"parse_slot {slot}")
        gems = ["0", "0", "0"]
    gems = list(map(int, gems))
    return {
        "item": item_id,
        "ench": ench_id,
        "gems": gems,
    }

def parse_gear(profile_json: dict):
    gear: dict[str, list[int]] = profile_json["inventory"] or {}
    return [
        parse_slot(gear.get(slot, {}))
        for slot in GEAR_ORDERED
    ]

def make_profile(profile):
    if not profile:
        return
    
    try:
        profile_json_str = re.findall("WowheadProfiler.+?({.*})", profile)[0]
        profile_json_str = profile_json_str.replace("'", '"')
        profile_json_str = re.sub('new Date.(\d+)[\D]', "\g<1>", profile_json_str)
        j = json.loads(profile_json_str)
    except Exception:
        LOGGER.exception("make_profile")
        return 
    
    class_name = CLASSES_ORDERED_DB[int(j["classs"])]
    
    talents_stings = (
        spec["talents"]
        for spec in j["talents"]["builds"]
    )
    specs = PlayerTalentsRG(class_name).get_talents_data_list(talents_stings)

    gear = parse_gear(j)

    profs = []
    profssecondary = []
    professions = j["skills"] or {}
    for prof_id, levels in professions.items():
        if prof_id in PROFS:
            profs.append([PROFS[prof_id], levels[0]])
        elif prof_id in PROFS_SECONDARY:
            profssecondary.append([PROFS_SECONDARY[prof_id], levels[0]])

    return {
        "level": j["level"],
        "race": RACES_ORDERED[int(j["race"])],
        "class": class_name,
        "guild": j["guild"],
        "specs": specs,
        "profs": profs,
        "profssecondary": profssecondary,
        "gear_data": gear,
    }


def parse_profile(name, forced: bool=False):
    profile = get_profile(name, forced)
    new_profile = make_profile(profile)
    DATABASE.update_player_row(name, new_profile)


def db_where_players(players: list[str]):
    c = DATABASE.cursor
    player_names = ','.join(f'"{x}"' for x in players)
    q = '\n'.join((
        f"SELECT {Columns.NAME}, {Columns.LAST_MODIFIED}, {Columns.DATA}",
        f"FROM [Rising-Gods]",
        f"WHERE {Columns.NAME} in ({player_names})",
    ))
    return c.execute(q)

def gen_players():
    df = logs_calendar.read_main_df()
    df_filtered = df[df["server"] == "Rising-Gods"]
    z = set()
    for report_id, data in df_filtered.iterrows():
        hour, minute = map(int, data["time"].split(":"))
        dt = datetime(
            year=2000+data["year"],
            month=data["month"],
            day=data["day"],
            hour=hour,
            minute=minute,
        )
        if dt < IS_OLD_DT:
            continue
        z.update(data["player"])
    return z

class RGParser:
    def __init__(
        self,
        forced: bool=False,
    ) -> None:
        self.forced = forced

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        LOGGER.debug(f"exit | type: {exc_type}")
        GemToEnch().write_cache()
        if exc_type != KeyboardInterrupt:
            LOGGER.exception("exit")
        return self

    def run(self):
        s = gen_players()
        total = len(s)
        for i, player in enumerate(s, 1):
            LOGGER.debug(f"{i:>6} | {total:>6}")
            parse_profile(player)


def test1():
    with RGParser():
        z = parse_profile("Dämohexer")
    print(z)


def main():
    forced = False
    # forced = True
    with RGParser(forced) as parser:
        parser.run()

if __name__ == "__main__":
    with RGParser() as parser:
        main()
