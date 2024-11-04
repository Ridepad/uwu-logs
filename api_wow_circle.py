import logging
import subprocess
import re
from dataclasses import dataclass

import requests

from c_path import Directories, Files
from h_debug import running_time, setup_logger
from h_server_fix import SERVERS_WC
from parser_profile_talents import PlayerTalentsWC


DEBUG = False
# DEBUG = True
LOGGER = setup_logger("wow_circle")
LOGGER.setLevel(logging.INFO)

WC_DIR = Directories.temp.new_child("wow_circle")

class WCFiles(Files):
    key_pmbc = WC_DIR / "wc_pmbc_key"
    key_phpsessid = WC_DIR / "wc_phpsessid_key"
    js_pmbc = WC_DIR / "pmbc.js"
    js_aes = WC_DIR / "aes.min.js"
    login_creds = WC_DIR / "login.json"


DOMAIN = "cp.wowcircle.net"
MAIN_URL = "https://cp.wowcircle.net/main.php"
AES_URL = "https://cp.wowcircle.net/aes.min.js"

MOZILLA_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
HEADERS = {
    'User-Agent': MOZILLA_UA,
}

SERVERS_WC_BY_ID = {
    v: k
    for k, v in SERVERS_WC.items()
}

LOGIN_CHECK = [
	{
		"action": "wow_Services",
		"method": "cmdGetCurrentSession",
		"type": "rpc",
	},
]
CLASSES_INDEX = [
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
RACES_INDEX = [
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
GENDERS_INDEX = [
    "Male",
    "Female",
]
FACTIONS = {
    1: "Horde",
    7: "Alliance",
}

GEAR_ORDERED = [
    "0",
    "1",
    "2",
    "14",
    "4",
    "3",
    "18",
    "8",
    "9",
    "5",
    "6",
    "7",
    "10",
    "11",
    "12",
    "13",
    "15",
    "16",
    "17",
]
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

class CharCategories(dict[str, str]):
    __getattr__ = dict.__getitem__

    char = "char"
    gear = "item"
    talents = "talents"

    profs = "skill"
    stats = "stats"
    spec = "talentsInfo"
    
    mounts = "mounts"
    achievement = "achievement"
    arena = "arena"
    pets = "pets"
    bank = "bank"
    bags = "bags"
    reputation = "reputation"
    titles = "titles"

    char_by_name = "char_by_name"

    spells = "spells"


def char_info_dry(action: str, data: list):
    return {
        "action": "wow_Services",
        "type": "rpc",
        "method": action,
        "data": data,
    }

def char_info_j(guid: str, caregory: str):
    data = [{
        "guid": guid,
        "load": caregory,
    }]
    return char_info_dry("cmdGetCharacter", data)

def char_info_by_name(name: str):
    data = [{
        "name": name,
    }]
    return char_info_dry("cmdGetCharactersView", data)

def char_info_by_names(names: list[str]):
    return [
        char_info_by_name(name)
        for name in names
    ]

def char_talents(guid: str, spec_index: int=0):
    data = [{
        "guid": guid,
        "load": CharCategories.talents,
        "filter": [{
            "property": "spec",
            "value": spec_index,
        }],
    }]
    return char_info_dry("cmdGetCharacter", data)

def char_talents_wrap(guid: str):
    return [
        char_talents(guid, i)
        for i in range(2)
    ]


def get_aes_script() -> bytes:
    try:
        return WCFiles.js_aes.read_bytes()
    except FileNotFoundError:
        pass

    LOGGER.debug("Downloading aes")
    response = requests.get(AES_URL, headers=HEADERS)
    aes_script = response.content
    WCFiles.js_aes.write_bytes(aes_script)
    return aes_script

def get_pmbc_script() -> bytes:
    request_data = char_info_by_name("Test")
    z = requests.post(MAIN_URL, json=request_data, headers=HEADERS)
    b = re.findall(b"aes.min.js.*?<script>(.*)</script>", z.content, re.S)
    return b[0]

def read_js_output():
    s = subprocess.Popen(["node", str(WCFiles.js_pmbc)], stdout=subprocess.PIPE)
    z = s.stdout.readline()
    pmbc_part = z.split(b';')[0]
    pmbc_key = pmbc_part.split(b'=', 1)[1]
    WCFiles.key_pmbc.write_bytes(pmbc_key)
    LOGGER.debug(f"pmbc_key | {pmbc_key.decode()}")
    return pmbc_key

def make_pmbc_key():
    parts = (
        get_aes_script(),
        b'var document = {location: {}};',
        get_pmbc_script(),
        b'''console.log(document.cookie);''',
    )
    pmbc_script_combined = b'\n'.join(parts)
    
    LOGGER.debug(f"+++ write js")
    WCFiles.js_pmbc.write_bytes(pmbc_script_combined)

    LOGGER.debug(f"+++ call js")
    return read_js_output()


def login_data():
    try:
        creds = WCFiles.login_creds.json()
    except Exception:
        creds = {
            "accountName": input("login    | "),
            "password":    input("password | "),
        }
        WCFiles.login_creds.json_write(creds)

    return [
        {
            "action": "wow_Services",
            "method": "cmdLogin",
            "type": "rpc",
            "data": [creds],
        }
    ]

class WCCharacterResult:
    type = CharCategories.char

    name: str
    totaltime: str
    guild_name: str
    deleteInfos_Name: str
    guid: int
    level: int
    class_index: int
    faction_index: int
    race_index: int
    gender_index: int
    money: int
    logout_time: int
    totalKills: int
    totalHonorPoints: int
    totaltime_sort: int

    keys_convert = {
        "class": "class_index",
        "race": "race_index",
        "gender": "gender_index",
        "faction": "faction_index",
    }

    def __init__(self, data: dict) -> None:
        self.exists = "name" in data
        self.data = {}
        for k, v in list(data.items()):
            k = self.keys_convert.get(k, k)
            try:
                v = int(v)
            except Exception:
                pass
            self.data[k] = v
            setattr(self, k, v)

    @property
    def class_name(self):
        return CLASSES_INDEX[self.class_index]

    @property
    def race(self):
        return RACES_INDEX[self.race_index]

    @property
    def faction(self):
        return FACTIONS[self.faction_index]

    @property
    def gender(self):
        return GENDERS_INDEX[self.gender_index]

    def has_same_name(self, name: str):
        return self.exists and self.name == name

    def __repr__(self):
        try:
            return f"{self.name:12} | {self.guid:>9} | {self.faction:>9} | {self.class_name:>12} | {self.race:>12} | {self.guild_name}"
        except AttributeError:
            return str(self.data)


class WCProfResult:
    type = CharCategories.profs
    def __init__(self, data: dict) -> None:
        self.data = data
        self.prof_id = data.get("skill")
        self.value = int(data.get("value") or 0)
        self.max = data.get("max")
        self.rus_name = data.get("name")
        self.name = PROFS.get(self.prof_id) or PROFS_SECONDARY.get(self.prof_id)
        if self.prof_id and not self.name:
            LOGGER.error(f"PROF NOT FOUND | {self.prof_id} | {self.rus_name}")

    @property
    def type(self):
        if self.prof_id in PROFS:
            return "main"
        if self.prof_id in PROFS_SECONDARY:
            return "secondary"
        return "unknown"
        
    def __str__(self):
        return ' | '.join((
            f"Skill ID: {self.prof_id}",
            f"Value: {self.value}",
            f"Max: {self.max}",
            f"Name: {self.name}",
        ))
    __repr__ = __str__

class WCProfsResults:
    type = CharCategories.profs
    def __init__(self, data: list[dict]) -> None:
        # self.data: list[WCProfResult] = []
        # for x in data:
        #     prof = WCProfResult(x)
        #     if prof.prof_id is None:
        #         continue
        #     self.data.append(prof)
        self.data = [
            WCProfResult(prof)
            for prof in data
            if prof.get("skill")
        ]
        # self.data = [
        #     prof
        #     for prof in self.data
        #     if prof.prof_id
        # ]

    def get_main_profs(self):
        profs = []
        for prof in self.data:
            if prof.type == "main":
                profs.append([prof.name, prof.value])
        return profs

    def get_secondary_profs(self):
        profs = []
        for prof in self.data:
            if prof.type == "secondary":
                profs.append([prof.name, prof.value])
        return profs


class WCSpecResult:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.tab = data.get("tab")
        self.points = data.get("points")
        self.pos = data.get("pos")
        self.spec = data.get("spec")
        self.name = data.get("name")

    def __str__(self):
        return ' | '.join((
            f"Spec: {self.spec}",
            f"tab: {self.tab}",
            f"points: {self.points}",
            f"pos: {self.pos}",
            f"Name: {self.name}",
        ))
    __repr__ = __str__

class WCSpecResults(list[WCSpecResult]):
    def __init__(self, data: list[dict]) -> None:
        for x in data:
            self.append(WCSpecResult(x))


class WCStatsResults(dict[str, float]):
    type = CharCategories.stats
    def __init__(self, data: list[dict]) -> None:
        d = sorted(
            (x.get("stat", "?"), float(x.get("value", "0")))
            for x in data
        )
        for k, v in d:
            self[k] = v

    def __str__(self) -> str:
        return '\n'.join((
            f"{slot:20} | {value:>10,.3f}"
            for slot, value in self.items()
        ))
    __repr__ = __str__


class WCGearResult:
    type = CharCategories.gear
    def __init__(self, data: list[dict]) -> None:
        self.data = data

    def as_list(self):
        formatted_gear = [0] * 19
        for item_dict in self.data:
            try:
                item_id = int(item_dict["entry"])
                slot_i = GEAR_ORDERED.index(item_dict["slot"])
                formatted_gear[slot_i] = {
                    "item": item_id,
                }
            except (KeyError, TypeError):
                pass
            except IndexError:
                pass
        
        return formatted_gear


class WCSpellsResult(dict[int, int]):
    type = CharCategories.spells
    def __init__(self, spells: list[dict]) -> None:
        d = sorted(
            (int(x.get("spell", "0")), int(x.get("spec")))
            for x in spells
        )
        for k,v in d:
            self[k] = v


class Talent:
    def __init__(self, **kwargs):
        self.spell_id = int(kwargs["spell"])
        self.spec = kwargs["spec"] or 0
        self.name = kwargs["name"] or ""

    def __str__(self):
        return " | ".join((
            f"{self.spell_id:>5}",
            f"{self.spec}",
            f"{self.name}",
        ))

class WCTalentsResult(list[Talent]):
    type = CharCategories.talents
    def __init__(self, talents: list[dict]) -> None:
        for x in talents:
            self.append(Talent(**x))


class WCOtherResult:
    def __init__(self, j: dict) -> None:
        self.data = j.get("result")
        self.type = j.get("type")
        self.method = j.get("method")

class WCException:
    type = "exception"
    def __init__(self, data: dict) -> None:
        self.data = data.get("data")


def wc_request_type(request_data: dict):
    data = request_data.get("data")
    if not data:
        raise ValueError("? not data")
    
    if request_data.get("method") == "cmdGetCharacter":
        return data[0]["load"]
    
    if request_data.get("method") == "cmdGetCharactersView":
        return "char_by_name"

    raise ValueError("? method")


def make_list(j):
    if not isinstance(j, list):
        return [j, ]
    if not j:
        return [{}, ]
    return j

def wcresponse_map(request_data: dict, response_data: dict):
    type = wc_request_type(request_data)
    
    result = response_data.get("result", {})
    result = make_list(result)

    if type == CharCategories.profs:
        return WCProfsResults(result)
    if type == CharCategories.spec:
        return WCSpecResults(result)
    
    first = result[0]
    if type == CharCategories.char:
        return WCCharacterResult(first)
    if type == CharCategories.char_by_name:
        return WCCharacterResult(first)
    
    data = first.get("data", [])
    if type == CharCategories.gear:
        return WCGearResult(data)
    
    if type == CharCategories.stats:
        return WCStatsResults(data)
    
    if type == CharCategories.talents:
        return WCTalentsResult(data)
    
    # if type == CharCategories.spells:
    #     return WCSpellsResult(data)
    
    return WCOtherResult(response_data)

def wcresponse(request_data: list[dict], response_data: list[dict]):
    request_data = make_list(request_data)
    response_data = make_list(response_data)
    d = []
    for req, res in zip(request_data, response_data):
        d.append(wcresponse_map(req, res))
    return d

class WCSimpleHtml:
    def __init__(self, response: requests.Response) -> None:
        self.html = response.content.decode("utf-8")
        self.headers = response.headers


class WCLogin:
    def __init__(self, response: requests.Response) -> None:
        j = response.json()
        result: dict = j.get("result", {})
        self.armoryURL: str = result.get("armoryURL")
        self.isAuth: bool = result.get("isAuth")
        self.name: str = result.get("name")
        self.id: int = result.get("id")
        self.serverType: str = result.get("serverType")
        self.realm: str = result.get("realm")
        self.version: int = result.get("version")
        self.recaptchaKey: str = result.get("recaptchaKey")
        self.accountLevel: int = result.get("accountLevel")


class WCSession(requests.Session):
    def __init__(self):
        super().__init__()
        
        self.headers = HEADERS
        self.login_tries = 0

        self._set_pmbc()
        self._set_phpsessid()

        LOGGER.debug(f"self.cookies __init__ | {self.cookies}")

    @property
    def phpsessid(self):
        return self.cookies.get("PHPSESSID", domain=DOMAIN)

    def post(self, url, **kwargs):
        old_phpsessid = self.phpsessid

        response = super().post(url, **kwargs)

        if self.phpsessid != old_phpsessid:
            WCFiles.key_phpsessid.write_text(self.phpsessid)

        return response

    def login(self):
        LOGGER.info(f"login")
        if self.login_tries > 2:
            LOGGER.error("Double Auth")
            raise ValueError("Double Auth Error")
        
        self.login_tries += 1
        if DEBUG:
            LOGGER.debug(f"self.cookies {self.cookies}")
        login_response = self.post(MAIN_URL, json=login_data())
        LOGGER.debug(f"Login response: {login_response.content}")
        
        wc_login_response = WCLogin(login_response)
        LOGGER.debug(f"Login Auth: {wc_login_response.isAuth}")
        if wc_login_response.isAuth:
            return True
        
        raise ValueError(f"Auth is {wc_login_response.isAuth}")

    def _set_pmbc(self, redo=False):
        if redo or not WCFiles.key_pmbc.is_file():
            make_pmbc_key()

        LOGGER.debug(f"Set PMBC | Redo: {redo}")
        pmbc = WCFiles.key_pmbc.read_text().strip()
        self.cookies.set("PMBC", pmbc, domain=DOMAIN)

    def _set_phpsessid(self):
        try:
            phpsessid = WCFiles.key_phpsessid.read_text().strip()
            self.cookies.set("PHPSESSID", phpsessid, domain=DOMAIN)
        except FileNotFoundError:
            pass


class WCServer:
    session = WCSession()

    def __init__(self, server: str) -> None:
        server = SERVERS_WC.get(server, server)
        if server not in SERVERS_WC_BY_ID:
            raise ValueError("Invalid Server ID")

        self.server = server
        self.url = f"{MAIN_URL}?serverId={server}"
    
    @running_time
    def post(self, request_data: dict, retry=False):
        response = self.session.post(self.url, json=request_data)
        # if DEBUG:
        # print("\n>>> post | content")
        # print(response.content.decode())

        if "application/json" not in response.headers.get("Content-Type"):
            r = WCSimpleHtml(response)
            if not retry and "+toHex" in r.html:
                self.session._set_pmbc(redo=True)
                return self.post(request_data=request_data, retry=True)
            raise ValueError("not a json")
            # return r
        
        j = response.json()
        j = make_list(j)
        if j[0] and j[0].get("type") == "exception":
            LOGGER.info(f"login retry")
            self.session.login()
            return self.post(request_data=request_data)
        
        return wcresponse(request_data, j)

    def get_char_data(self, guid: str, category: str):
        request_data = char_info_j(guid, category)
        return self.post(request_data)

    def get_multi_char_data(self, guids: list[str]) -> list[WCCharacterResult]:
        request_data = [
            char_info_j(guid, CharCategories.char)
            for guid in guids
        ]
        return self.post(request_data)
    
    def char_get_gear(self, guid: str):
        return self.get_char_data(guid, CharCategories.gear)
    
    def get_char_data_mutliple(self, guid: str, categories: list[str]):
        request_data = [
            char_info_j(guid, category)
            for category in categories
        ]
        return self.post(request_data)
    
    def get_talents(self, guid: str):
        request_data = char_talents_wrap(guid)
        return self.post(request_data)

    def get_character_data_list(self, names: list[str]):
        request_data = char_info_by_names(names)
        return self.post(request_data)

    def get_character_data_list_guid(self, guids: list[str]):
        request_data = char_info_by_names(guids)
        return self.post(request_data)
    
    def get_character_data(self, name: str):
        request_data = char_info_by_name(name)
        return self.post(request_data)
    
    def get_test_data(self):
        request_data = char_info_by_name("Test")
        return self.session.post(MAIN_URL, json=request_data)


@dataclass
class WCCharacter:
    char: WCCharacterResult
    gear: WCGearResult
    profs: WCProfsResults
    spec1: WCTalentsResult
    spec2: WCTalentsResult
    
    def base_stats(self):
        return {
            "guid": self.char.guid,
            "level": self.char.level,
            "race": self.char.race,
            "class": self.char.class_name,
            "guild": self.char.guild_name,
            "gender": self.char.gender,
        }
    def profile(self):
        return self.base_stats() | {
            "specs": self.spec_data(),
            "profs": self.profs.get_main_profs(),
            "profssecondary": self.profs.get_secondary_profs(),
            "gear_data": self.gear.as_list(),
        }
        
    def spec_data(self):
        return [
            self._spec_data(spec)
            for spec in [self.spec1, self.spec2]
        ]

    def _spec_data(self, spec: WCTalentsResult):
        zz = [t.spell_id for t in spec]
        pt = PlayerTalentsWC(self.char.class_name)
        return pt.get_talents_data(zz).as_list()


class WCCharacterBuild(dict):
    def __setitem__(self, key, value):
        if key == CharCategories.talents:
            if "spec1" in self:
                key = "spec2"
            else:
                key = "spec1"
        elif key == CharCategories.gear:
            key = "gear"
        elif key == CharCategories.profs:
            key = "profs"
        return super().__setitem__(key, value)


class WCCharactersProfiles(WCServer):
    def split_to_characters(self, responses: list):
        characters = []
        current_character = WCCharacterBuild()
        for response in responses:
            # response: WCCharacterResult
            if response.type == CharCategories.char:
                LOGGER.debug(f"split_to_characters | {response.name}")
                characters.append(current_character)
                current_character = WCCharacterBuild()
            current_character[response.type] = response
        characters.append(current_character)

        return [
            WCCharacter(**character)
            for character in characters
            if character
        ]
        
    def get_profiles(self, guids: list[str]):
        request_data = []
        for guid in guids:
            request_data.extend(self.make_profile_query(guid))
        resp = self.post(request_data)
        return self.split_to_characters(resp)
    
    def make_profile_query(self, guid: str):
        categories = [
            CharCategories.char,
            CharCategories.gear,
            CharCategories.profs,
        ]
        request_data = [
            char_info_j(guid, category)
            for category in categories
        ]
        request_data += char_talents_wrap(guid)
        return request_data
