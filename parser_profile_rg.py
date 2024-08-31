import json
import requests
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import logs_base
from c_path import Directories
from top_gear import GearDB


RISING_GODS = "Rising-Gods"
DATABASE = GearDB(RISING_GODS, new=True)

TEMP_PROFILE_DATA_DIR = Directories.main.new_child("temp").new_child(RISING_GODS)
GEM_TO_ENCH_DICT_PATH = Directories.main / "x_gem_to_ench.json"

URL_RG_PROFILE = "https://db.rising-gods.de/?profile=eu.rising-gods"
URL_RG_PROFILE_LOAD = "https://db.rising-gods.de/?profile=load&id"

HEADERS = {"User-Agent": "CharacterParserRG/1.1; +uwu-logs.xyz"}

TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE"

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
TALENTS = {
  "Death Knight": {
    "nodes": [28, 29, 31],
    "specs": ["Blood", "Frost", "Unholy"],
    "prefix": "j",
  },
  "Druid": {
    "nodes": [28, 30, 27],
    "specs": ["Balance", "Feral Combat", "Restoration"],
    "prefix": "0",
  },
  "Hunter": {
    "nodes": [26, 27, 28],
    "specs": ["Beast Mastery", "Marksmanship", "Survival"],
    "prefix": "c",
  },
  "Mage": {
    "nodes": [30, 28, 28],
    "specs": ["Arcane", "Fire", "Frost"],
    "prefix": "o",
  },
  "Paladin": {
    "nodes": [26, 26, 26],
    "specs": ["Holy", "Protection", "Retribution"],
    "prefix": "s",
  },
  "Priest": {
    "nodes": [28, 27, 27],
    "specs": ["Discipline", "Holy", "Shadow"],
    "prefix": "b",
  },
  "Rogue": {
    "nodes": [27, 28, 28],
    "specs": ["Assassination", "Combat", "Subtlety"],
    "prefix": "f",
  },
  "Shaman": {
    "nodes": [25, 29, 26],
    "specs": ["Elemental", "Enhancement", "Restoration"],
    "prefix": "h",
  },
  "Warlock": {
    "nodes": [28, 27, 26],
    "specs": ["Affliction", "Demonology", "Destruction"],
    "prefix": "I",
  },
  "Warrior": {
    "nodes": [31, 27, 27],
    "specs": ["Arms", "Fury", "Protection"],
    "prefix": "L",
  }
}

def requests_get(page_url, timeout_mult=2, attempts=5):
    for attempt in range(1, attempts+1):
        timeout = timeout_mult * attempt
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=timeout, allow_redirects=False)
            if response.status_code == 200:
                return response.text
            if response.status_code == 404:
                return
            print("! ERROR1", attempt, response.status_code)
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            AttributeError,
        ):
            print("! ERROR2", attempt, response.status_code)
        
        time.sleep(2)
    
    return None

def json_read(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def json_write(p: Path, d: dict):
    p.write_text(json.dumps(d))

class GemToEnch:
    cls_dict = {
        "changed": False,
    }
    gem_to_ench_dict = json_read(GEM_TO_ENCH_DICT_PATH)

    def gem_to_ench(self, gem_id):
        gem_id = str(gem_id)
        if gem_id in self.gem_to_ench_dict:
            return self.gem_to_ench_dict[gem_id]
        if gem_id == "0" or gem_id == "None":
            self.gem_to_ench_dict[gem_id] = "0"
            return "0"
        
        print(gem_id)
        url = f"https://wotlk.evowow.com/?item={gem_id}"
        response_text = requests_get(url)
        if not response_text:
            print("! ERROR MISSING GEM DATA:", gem_id)
            return "0"
        
        ench_index = response_text.find("?enchantment=")
        ench_str = response_text[ench_index:ench_index+25]
        ench_id = re.findall("(\d{3,4})", ench_str)[0]
        self.gem_to_ench_dict[gem_id] = ench_id
        self.cls_dict["changed"] = True
        print(f"NEW GEM: {gem_id} = {ench_id}")
        return ench_id

    def write_cache(self):
        print('+'*50)
        print('write_cache', self.cls_dict["changed"])
        if self.cls_dict["changed"]:
            json_write(GEM_TO_ENCH_DICT_PATH, self.gem_to_ench_dict)
        self.cls_dict["changed"] = False

def convert_to_string(talent_str):
    talents = list(map(int, talent_str))
    if len(talents) & 1:
        talents.append(0)
    
    z = zip(talents[::2], talents[1::2])
    g = (TALENTS_ENCODE_STR[r1 * 6 + r2] for r1, r2 in z)
    s = "".join(g)
    
    if s[-1] == TALENTS_ENCODE_STR[0]:
        return s.rstrip(TALENTS_ENCODE_STR[0]) + "Z"
    return s


def split_trees(full_spec: str, class_name: str):
    trees: list[list[int]] = []
    for tree_size in TALENTS[class_name]["nodes"]:
        current_tree, full_spec = full_spec[:tree_size], full_spec[tree_size:]
        trees.append(list(map(int, current_tree)))
    return trees

def convert_spec_to_string(spec_trees: list[int]):
    tree_gen = (convert_to_string(tree) for tree in spec_trees)
    return "".join(tree_gen).rstrip("Z")

def spec_data(full_spec, class_name):
    spec_trees = split_trees(full_spec, class_name)
    
    tree_string = convert_spec_to_string(spec_trees)
    talent_string_prefix = TALENTS[class_name]["prefix"]
    tree_string = talent_string_prefix + tree_string
    
    allocated = [sum(x) for x in spec_trees]
    class_specs = TALENTS[class_name]["specs"]
    spec_index_max_allocated = allocated.index(max(allocated))
    spec = class_specs[spec_index_max_allocated]
    allocated_str = "/".join(map(str, allocated))
    
    return [
        spec,
        allocated_str,
        tree_string,
    ]

def rg_url(name):
    return f"{URL_RG_PROFILE}.{name}"

def get_now_timestamp():
    return int(datetime.now().timestamp() * 1000)
def rg_url_full(char_id):
    timestamp = get_now_timestamp()
    return f"{URL_RG_PROFILE_LOAD}={char_id}&{timestamp}"

def get_profile(name: str, forced: bool=False):
    profile_path = TEMP_PROFILE_DATA_DIR / f"{name}.txt"
    if not forced and profile_path.is_file():
        print('profile from cache')
        return profile_path.read_text()
    
    url = rg_url(name)
    try:
        profile1 = requests_get(url)
    except AttributeError:
        print('ERROR: response empty')
        return

    if not profile1:
        print("ERROR: profile is empty1")
        return
    
    try:
        profile_number_id = re.findall("profilah-generic.*?(\d+)", profile1)[0]
    except IndexError:
        print('ERROR: id wasnt found')
        return

    print("> get_profile | ID:", profile_number_id)
    
    url = rg_url_full(profile_number_id)
    profile_txt = requests_get(url)
    if not profile_txt:
        print("ERROR: profile is empty2")
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
        print("ERROR in slot")
        print(slot)
        gems = ["0", "0", "0"]
    gems = list(map(int, gems))
    return {
        "item": item_id,
        "ench": ench_id,
        "gems": gems,
    }

def parse_gear(profile_json: dict):
    gear: dict[str, list[int]] = profile_json["inventory"]
    return [
        parse_slot(gear.get(slot, {}))
        for slot in GEAR_ORDERED
    ]

def make_profile(profile):
    if not profile:
        print("doshit | not profile")
        return
    
    try:
        profile_json_str = re.findall("WowheadProfiler.+?({.*})", profile)[0]
        profile_json_str = profile_json_str.replace("'", '"')
        profile_json_str = re.sub('new Date.(\d+)[\D]', "\g<1>", profile_json_str)
        j = json.loads(profile_json_str)
    except Exception as e:
        print("doshit | Exception", e)
        return 
    
    class_name = CLASSES_ORDERED_DB[int(j["classs"])]
    
    specs = [
        spec_data(spec["talents"], class_name)
        for spec in j["talents"]["builds"]
    ]

    gear = j["inventory"]
    gear = [
        parse_slot(gear.get(slot, {}))
        for slot in GEAR_ORDERED
    ]

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
    print("> parse_profile:", name)
    profile = get_profile(name, forced)
    new_profile = make_profile(profile)
    DATABASE.add(name, new_profile)

def gen_rg():
    p = Path("/mnt/uwu-logs/LogsDir")
    # for x in (PATH / "LogsDir").iterdir():
    for report_path in p.iterdir():
        if report_path.name.endswith(RISING_GODS):
            yield report_path

class RGParser:
    def __init__(self, forced: bool=True) -> None:
        self.forced = forced

    def __enter__(self):
        print('enter')
        return self

    def run(self):
        if self.forced:
            for x in TEMP_PROFILE_DATA_DIR.iterdir():
                x.unlink()

        # _now = (datetime.now() - timedelta(hours=1)).timestamp()
        _now = (datetime.now() - timedelta(days=1)).timestamp()
        # _now = (datetime.now() - timedelta(days=60)).timestamp()

        for x in gen_rg():
            _log = x / "LOGS_CUT.zstd"
            if _log.stat().st_atime > _now:
                print("skipped old")
                continue

            print()
            print(x)
            report = logs_base.THE_LOGS(x.name)
            for x in report.get_players_guids().values():
                parse_profile(x)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exit')
        print(exc_type)
        print(exc_val)
        GemToEnch().write_cache()
        return self

def test1():
    with RGParser():
        z = parse_profile("Carrydoter", forced=True)
    print(z)

def main():
    forced = False
    forced = True
    with RGParser(forced) as parser:
        parser.run()
    
if __name__ == "__main__":
    main()
