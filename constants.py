import json
import os
import logging
import pickle
import re
import zlib
from collections import defaultdict
from datetime import datetime, timedelta
from time import perf_counter
import atexit


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print('[CREATED FOLDER]', path)

def new_folder_path(root, name):
    new_folder = os.path.join(root, name)
    create_folder(new_folder)
    return new_folder

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
LOGS_DIR = new_folder_path(DIR_PATH, "LogsDir")
LOGS_RAW = new_folder_path(DIR_PATH, "LogsRaw")
UPLOADS_DIR = new_folder_path(DIR_PATH, "uploads")
PARSED_DIR = new_folder_path(UPLOADS_DIR, "__parsed__")

LOGGING_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s():%(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"
LOGGING_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s():%(lineno)s] %(message)s"

def setup_logger(logger_name, log_file, level=logging.DEBUG):
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter(LOGGING_FORMAT)
    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

LOGFILE = os.path.join(DIR_PATH,'_log.log')
logging.basicConfig(
    filename=LOGFILE,
    format=LOGGING_FORMAT,
    datefmt="%d/%m/%Y %H:%M:%S",
    level=logging.DEBUG,
    
)

T_DELTA_2MIN = timedelta(minutes=2)
T_DELTA_5MIN = timedelta(minutes=5)
T_DELTA_10MIN = timedelta(minutes=10)
T_DELTA_15MIN = timedelta(minutes=15)
T_DELTA_20MIN = timedelta(minutes=20)
T_DELTA = timedelta(seconds=100)
T_DELTA_SHORT = timedelta(seconds=15)
T_DELTA_SEP = timedelta(minutes=20)
T_DELTA_ONE_SECOND = timedelta(seconds=1)

LOGS_CUT_NAME = "LOGS_CUT"

FLAG_ORDER = [
    "SPELL_DISPEL", "SPELL_CAST_SUCCESS", "SPELL_EXTRA_ATTACKS",  "SPELL_ENERGIZE",
    "SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE", "SPELL_HEAL",
    "SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_REMOVED",
    "SPELL_MISSED", "SPELL_CAST_START", ]

BOSSES_FROM_HTML = {
    "the-lich-king": "The Lich King",
    "halion": "Halion",
    "deathbringer-saurfang": "Deathbringer Saurfang",
    "festergut": "Festergut",
    "rotface": "Rotface",
    "professor-putricide": "Professor Putricide",
    "blood-queen-lanathel": "Blood-Queen Lana'thel",
    "sindragosa": "Sindragosa",
    "lord-marrowgar": "Lord Marrowgar",
    "lady-deathwhisper": "Lady Deathwhisper",
    "gunship-battle": "Gunship Battle",
    "blood-prince-council": "Blood Prince Council",
    "valithria-dreamwalker": "Valithria Dreamwalker",
    "northrend-beasts": "Northrend Beasts",
    "lord-jaraxxus": "Lord Jaraxxus",
    "faction-champions": "Faction Champions",
    "twin-valkyr": "Twin Val'kyr",
    "anubarak": "Anub'arak",
    "onyxia": "Onyxia",
    "malygos": "Malygos",
    "sartharion": "Sartharion",
    "baltharus-the-warborn": "Baltharus the Warborn",
    "general-zarithrian": "General Zarithrian",
    "saviana-ragefire": "Saviana Ragefire",
    "archavon-the-stone-watcher": "Archavon the Stone Watcher",
    "emalon-the-storm-watcher": "Emalon the Storm Watcher",
    "koralon-the-flame-watcher": "Koralon the Flame Watcher",
    "toravon-the-ice-watcher": "Toravon the Ice Watcher",
    "anubrekhan": "Anub'Rekhan",
    "grand-widow-faerlina": "Grand Widow Faerlina",
    "maexxna": "Maexxna",
    "noth-the-plaguebringer": "Noth the Plaguebringer",
    "heigan-the-unclean": "Heigan the Unclean",
    "loatheb": "Loatheb",
    "patchwerk": "Patchwerk",
    "grobbulus": "Grobbulus",
    "gluth": "Gluth",
    "thaddius": "Thaddius",
    "instructor-razuvious": "Instructor Razuvious",
    "gothik-the-harvester": "Gothik the Harvester",
    "the-four-horsemen": "The Four Horsemen",
    "sapphiron": "Sapphiron",
    "kelthuzad": "Kel'Thuzad",
    "flame-leviathan": "Flame Leviathan",
    "ignis-the-furnace-master": "Ignis the Furnace Master",
    "razorscale": "Razorscale",
    "xt-002-deconstructor": "XT-002 Deconstructor",
    "assembly-of-iron": "Assembly of Iron",
    "kologarn": "Kologarn",
    "auriaya": "Auriaya",
    "hodir": "Hodir",
    "thorim": "Thorim",
    "freya": "Freya",
    "mimiron": "Mimiron",
    "general-vezax": "General Vezax",
    "yogg-saron": "Yogg-Saron",
    "algalon-the-observer": "Algalon the Observer"
}

BOSSES_GUIDS = {
    "007995": "Archavon the Stone Watcher",
    "0084C9": "Emalon the Storm Watcher",
    "0088C5": "Koralon the Flame Watcher",
    "009621": "Toravon the Ice Watcher",

    "0070BB": "Malygos",
    "0070BC": "Sartharion",
    "0027C8": "Onyxia",

    "008F04": "Lord Marrowgar",
    "008FF7": "Lady Deathwhisper",
    "0092A4": "The Skybreaker",
    "00915F": "Orgrim's Hammer",
    "0093B5": "Deathbringer Saurfang",
    "008F12": "Festergut",
    "008F13": "Rotface",
    "008F46": "Professor Putricide",
    "009454": "Prince Keleseth",
    "009455": "Prince Taldaram",
    "009452": "Prince Valanar",
    "009443": "Blood-Queen Lana'thel",
    "008FB5": "Valithria Dreamwalker",
    # "0093EC": "Risen Archmage",
    "008FF5": "Sindragosa",
    "008EF5": "The Lich King",
    
    "009B42": "General Zarithrian",
    "009B43": "Saviana Ragefire",
    "009B47": "Baltharus the Warborn",
    "009BB7": "Halion",
    "009CD2": "Halion",
    
    "0087EC": "Gormok the Impaler",
    "008948": "Acidmaw",
    "0087EF": "Dreadscale",
    "0087ED": "Icehowl",
    "0087DC": "Lord Jaraxxus",
    "0086C0": "Eydis Darkbane",
    "0086C1": "Fjola Lightbane",
    "008704": "Anub'arak",

    "0076F1": "Vesperon",
    "0076F3": "Shadron",
    "0076F4": "Tenebron",
    "0070BC": "Sartharion",

    "003E54": "Anub'Rekhan",
    "003E51": "Grand Widow Faerlina",
    "003E50": "Maexxna",
    "003E52": "Noth the Plaguebringer",
    "003E40": "Heigan the Unclean",
    "003E8B": "Loatheb",
    "003EBD": "Instructor Razuvious",
    "003EBC": "Gothik the Harvester",
    "003EBF": "Sir Zeliek",
    "003EC0": "Thane Korth'azz",
    "003EC1": "Lady Blaumeux",
    "007755": "Baron Rivendare",
    "003E9C": "Patchwerk",
    "003E3B": "Grobbulus",
    "003E3C": "Gluth",
    "003E38": "Thaddius",
    "003E75": "Sapphiron",
    "003E76": "Kel'Thuzad",

    
    "008159": "Flame Leviathan",
    "00808A": "Freya",
    "008061": "Thorim",
    "0081A2": "Razorscale",
    "00815E": "Ignis the Furnace Master",
    "00820D": "XT-002 Deconstructor",
    
    "008063": "Steelbreaker",
    "00809F": "Runemaster Molgeim",
    "008059": "Stormcaller Brundir",
    "0080A2": "Kologarn",
    "0082EB": "Auriaya",
    "008067": "Algalon the Observer",
    "00804D": "Hodir",
    "008208": "Leviathan Mk II",
    "008373": "VX-001",
    "008386": "Aerial Command Unit",
    "008246": "Mimiron",
    "008061": "Thorim",
    "0081F7": "General Vezax",
    "008208": "Yogg-Saron",

    # "0080A5": "Left Arm",
    # "0080A6": "Right Arm",

    # "008231": "Heart of the Deconstructor",
    # "008242": "XE-321 Boombot",
    # "008240": "XM-024 Pummeller",
    # "00823F": "XS-013 Scrapbot",

    # "0081B3": "Ancient Conservator",
    # "0081B2": "Ancient Water Spirit",
    # "008096": "Detonating Lasher",
    # "0081CC": "Eonar's Gift",
    # "008094": "Snaplasher",
    # "008097": "Storm Lasher",
    # "008190": "Strengthened Iron Roots",

}

TOC_CHAMPIONS = {
    "00869D": "Tyrius Duskblade <DK>",
    "00869C": "Kavina Grovesong <Druid>",
    "0086A5": "Melador Valestrider <Druid>",
    "0086A3": "Alyssia Moonstalker <Hunter>",
    "0086A4": "Noozle Whizzlestick <Mage>",
    "0086A1": "Velanaa <Paladin>",
    "0086A7": "Baelnor Lightbearer <Paladin>",
    "0086A2": "Anthar Forgemender <Priest>",
    "0086A9": "Brienna Nightfell <Priest>",
    "0086A8": "Irieth Shadowstep <Rogue>",
    "00869F": "Shaabad <Shaman>",
    "0086A6": "Saamul <Shaman>",
    "0086AA": "Serissa Grimdabbler <Warlock>",
    "0086AB": "Shocuul <Warrior>",
    
    "00869A": "Gorgrim Shadowcleave <DK>",
    "008693": "Birana Stormhoof <Druid>",
    "00869B": "Erin Misthoof <Druid>",
    "008690": "Ruj'kah <Hunter>",
    "008691": "Ginselle Blightslinger <Mage>",
    "00868D": "Liandra Suncaller <Paladin>",
    "008698": "Malithas Brightblade <Paladin>",
    "00868F": "Caiphus the Stern <Priest>",
    "008689": "Vivienne Blackwhisper <Priest>",
    "008696": "Maz'dinah <Rogue>",
    "008697": "Broln Stouthorn <Shaman>",
    "00868C": "Thrakgar <Shaman>",
    "008692": "Harkzog <Warlock>",
    "008695": "Narrhok Steelbreaker <Warrior>",
}
BOSSES_GUIDS.update(TOC_CHAMPIONS)

MUTLIBOSSES = {
    "Halion": ['009BB7', '009CCE', '009CD2'],
    "Gunship": ['0092A4', '00915F'],
    "Blood Prince Council": ['009454', '009455', '009452'],
    "Northrend Beasts": ['0087EC', '008948', '0087EF', '0087ED'],
    "Faction Champions": list(TOC_CHAMPIONS),
    "Twin Val'kyr": ['0086C0', '0086C1'],
    "The Four Horsemen": ["003EBF", "007755", "003EC1", "003EC0"],
    "Mimiron": ["008246", "008208", "008373", "008386"],
    "Assembly of Iron": ["008063", "00809F", "008059"],

}

SPELLS_SCHOOLS = {
    0: "",
    1: "physical", #FFFF00   255, 255, 0
    2: "holy", ##FFE680   255, 230, 128
    4: "fire", ##FF8000   255, 128, 0
    8: "nature", ##4DFF4D   77, 255, 77
    16: "frost", ##80FFFF   128, 255, 255
    32: "shadow", ##8080FF   128, 128, 255
    64: "arcane", ##FF80FF   255, 128, 255
    3: "holystrike", #Holy + Physical
    5: "flamestrike", #-- Fire + Physical
    # 6: "holyfire", #-- Fire + Holy (Radiant)
    # 9: "stormstrike", #-- Nature + Physical
    # 10: "holystorm", #-- Nature + Holy
    12: "firestorm", #Nature + Fire
    17: "froststrike", #Frost + Physical
    # 18: "holyfrost", #-- Frost + Holy
    20: "frostfire", #Frost + Fire
    # 24: "froststorm", #-- Frost + Nature
    33: "shadowstrike", #Shadow + Physical
    34: "shadowlight", #Shadow + Holy
    # 36: "shadowflame", #-- Shadow + Fire
    40: "shadowstorm", #Shadow + Nature
    48: "shadowfrost", #Shadow + Frost
    # 65: "spellstrike", #-- Arcane + Physical
    66: "divine", #Arcane + Holy
    68: "spellfire", #-- Arcane + Fire
    # 72: "spellstorm", #-- Arcane + Nature
    80: "spellfrost", #-- Arcane + Frost
    96: "spellshadow", #Arcane + Shadow
    # 28: "elemental", #-- Frost + Nature + Fire
    # 124: "chromatic", #-- Arcane + Shadow + Frost + Nature + Fire
    # 126: "magic", #-- Arcane + Shadow + Frost + Nature + Fire + Holy
    127: "chaos", # Arcane + Shadow + Frost + Nature + Fire + Holy + Physical
}

UNUSUAL_SPELLS = {
    6: "holyfire", #-- Fire + Holy (Radiant)
    9: "stormstrike", #-- Nature + Physical
    10: "holystorm", #-- Nature + Holy
    18: "holyfrost", #-- Frost + Holy
    24: "froststorm", #-- Frost + Nature
    36: "shadowflame", #-- Shadow + Fire
    65: "spellstrike", #-- Arcane + Physical
    72: "spellstorm", #-- Arcane + Nature
    28: "elemental", #-- Frost + Nature + Fire
    124: "chromatic", #-- Arcane + Shadow + Frost + Nature + Fire
    126: "magic", #-- Arcane + Shadow + Frost + Nature + Fire + Holy
}

ENV_DAMAGE = {
    'FALLING': "90001",
    'LAVA': "90002",
    'DROWNING': "90003",
    'FIRE': "90004",
    'FATIGUE': "90005",
    'SLIME': "90006",
}

def running_time(f):
    def running_time_inner(*args, **kwargs):
        st = perf_counter()
        q = f(*args, **kwargs)
        fin = int((perf_counter() - st) * 1000)
        print(f'[PERFOMANCE] Done in {fin:>6,} ms with {f.__module__}.{f.__name__}')
        return q
    return running_time_inner

def sort_dict_by_value(d: dict):
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=True))


NIL_GUID = '0x0000000000000000'
def is_player(guid: str):
    return guid.startswith('0x0') and guid != NIL_GUID

def add_space(v):
    return f"{v:,}".replace(',', ' ')


def fix_extention(ext: str):
    if ext[0] == '.':
        return ext
    return f".{ext}"

def add_extention(path: str, ext=None):
    if ext is not None:
        ext = fix_extention(ext)
        if not path.endswith(ext):
            path = path.split('.')[0]
            return f"{path}{ext}"
    return path

def save_backup(path):
    if os.path.isfile(path):
        old = f"{path}.old"
        if os.path.isfile(old):
            os.remove(old)
        os.rename(path, old)

def json_read(path: str):
    path = add_extention(path, '.json')
    try:
        with open(path) as file:
            j: dict = json.load(file)
            return j
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}

def json_read_no_exception(path: str):
    path = add_extention(path, '.json')
    with open(path) as file:
        return json.load(file)

def json_write(path: str, data, indent=2):
    path = add_extention(path, '.json')
    save_backup(path)
    with open(path, 'w') as file:
        json.dump(data, file, default=sorted, indent=indent)


def bytes_read(path: str, ext=None):
    path = add_extention(path, ext)
    try:
        with open(path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        return b''

@running_time
def bytes_write(path: str, data: bytes, ext=None):
    path = add_extention(path, ext)
    with open(path, 'wb') as file:
        file.write(data)

@running_time
def file_read(path: str, ext=None):
    path = add_extention(path, ext)
    # try:
    #     raw = bytes_read(path, ext)
    #     return raw.decode()
    # except Exception as e:
    #     print(f"[file_read] {e}")

    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

@running_time
def file_write(path: str, data: str, ext=None):
    path = add_extention(path, ext)
    with open(path, 'w') as f:
        f.write(data)


def zlib_decompress(data: bytes):
    return zlib.decompress(data)

@running_time
def pickle_from_bytes(data: bytes):
    return pickle.loads(data)

@running_time
def zlib_pickle_read(path: str):
    path = add_extention(path, '.pickle.zlib')
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return pickle_from_bytes(data)

@running_time
def zlib_text_read(path: str):
    path = add_extention(path, '.zlib')
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return data.decode()


@running_time
def pickle_dumps(data):
    return pickle.dumps(data)

@running_time
def zlib_compress(__data, level=7):
    return zlib.compress(__data, level=level)

def zlib_pickle_make(data_raw):
    data_pickle = pickle_dumps(data_raw)
    comresesed = zlib_compress(data_pickle)
    return comresesed

@running_time
def zlib_pickle_write(data_raw, path: str):
    path = add_extention(path, '.pickle.zlib')
    zlib_pickle = zlib_pickle_make(data_raw)
    bytes_write(path, zlib_pickle)

def zlib_text_make(data_raw: str):
    data_enc = data_raw.encode()
    comresesed = zlib_compress(data_enc)
    return comresesed

# @running_time
# def zlib_text_write(data_raw: str, path: str, check_exists: bool=True):
#     path = add_extention(path, '.zlib')
#     zlib_text = zlib_text_make(data_raw)
#     if not check_exists:
#         bytes_write(path, zlib_text)
#         return
#     old_data = bytes_read(path)
#     exists = old_data == zlib_text
#     if not exists:
#         bytes_write(path, zlib_text)
#     return exists

def zlib_text_write(data_raw: str, path: str):
    path = add_extention(path, '.zlib')
    zlib_text = zlib_text_make(data_raw)
    bytes_write(path, zlib_text)


@running_time
def logs_splitlines(logs: str):
    return logs.splitlines()

def pickle_read(path: str):
    path = add_extention(path, '.pickle')
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print('[ERROR] FILE DOESNT EXISTS:', path)

def pickle_write(path: str, data):
    path = add_extention(path, '.pickle')
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def get_now():
    return datetime.now()

# Z = re.compile('(\d{1,2})/(\d{1,2}) (\d\d):(\d\d):(\d\d).(\d\d\d)')
def to_dt_closure(year=None):
    Z = re.compile('(\d+)')
    current = get_now()
    day = current.day
    month = current.month
    find_all = Z.findall
    if year is None:
        year = current.year
        def inner(s: str):
            q = list(map(int, find_all(s[:18])))
            q[-1] *= 1000
            if q[0] > month or q[0] == month and q[1] > day:
                return datetime(year-1, *q)
            return datetime(year, *q)
    else:
        def inner(s: str):
            q = list(map(int, find_all(s[:18])))
            q[-1] *= 1000
            return datetime(year, *q)
        
    return inner

to_dt = to_dt_closure()

def get_time_delta(s: str, f: str, _to_dt=to_dt):
    return _to_dt(f) - _to_dt(s)

def get_time_delta_wrap(_to_dt=to_dt):
    def inner(s: str, f: str):
        return _to_dt(f) - _to_dt(s)
    return inner

def get_fight_duration(s, f):
    return get_time_delta(s, f).total_seconds()

def convert_duration(t):
    milliseconds = int(t * 1000 % 1000)
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = t // 3600
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0<3}"

def convert_duration(t):
    return str(timedelta(seconds=t))

def get_folders(path) -> list[str]:
    return next(os.walk(path))[1]

def get_files(path) -> list[str]:
    return next(os.walk(path))[2]

def get_all_files(path=None, ext=None):
    if path is None:
        path = '.'
    files = get_files(path)
    if ext is None:
        return files
    ext = fix_extention(ext)
    return [file for file in files if file.endswith(ext)]
    
def redo_data(redo_func, multi=True, startfrom=None, end=None, proccesses=4):
    def get_index(z):
        return z if type(z) == int else folders.index(z)
    
    folders = get_folders('LogsDir')

    if startfrom:
        i = get_index(startfrom)
        folders = folders[i:]
    if end:
        i = get_index(end)
        folders = folders[:i]

    if multi and proccesses > 0:
        from multiprocessing import Pool
        with Pool(proccesses) as p:
            p.map(redo_func, folders)
    else:
        for x in folders:
            redo_func(x)


CLASSES = {
  "Death Knight": {
    "": "class_deathknight",
    "Blood": "spell_deathknight_bloodpresence",
    "Frost": "spell_deathknight_frostpresence",
    "Unholy": "spell_deathknight_unholypresence"
  },
  "Druid": {
    "": "class_druid",
    "Balance": "spell_nature_starfall",
    "Feral Combat": "ability_racial_bearform",
    "Restoration": "spell_nature_healingtouch"
  },
  "Hunter": {
    "": "class_hunter",
    "Beast Mastery": "ability_hunter_beasttaming",
    "Marksmanship": "ability_marksmanship",
    "Survival": "ability_hunter_swiftstrike"
  },
  "Mage": {
    "": "class_mage",
    "Arcane": "spell_holy_magicalsentry",
    "Fire": "spell_fire_firebolt02",
    "Frost": "spell_frost_frostbolt02"
  },
  "Paladin": {
    "": "class_paladin",
    "Holy": "spell_holy_holybolt",
    "Protection": "spell_holy_devotionaura",
    "Retribution": "spell_holy_auraoflight"
  },
  "Priest": {
    "": "class_priest",
    "Discipline": "spell_holy_wordfortitude",
    "Holy": "spell_holy_guardianspirit",
    "Shadow": "spell_shadow_shadowwordpain"
  },
  "Rogue": {
    "": "class_rogue",
    "Assassination": "ability_rogue_eviscerate",
    "Combat": "ability_backstab",
    "Subtlety": "ability_stealth"
  },
  "Shaman": {
    "": "class_shaman",
    "Elemental": "spell_nature_lightning",
    "Enhancement": "spell_nature_lightningshield",
    "Restoration": "spell_nature_magicimmunity"
  },
  "Warlock": {
    "": "class_warlock",
    "Affliction": "spell_shadow_deathcoil",
    "Demonology": "spell_shadow_metamorphosis",
    "Destruction": "spell_shadow_rainoffire"
  },
  "Warrior": {
    "": "class_warrior",
    "Arms": "ability_rogue_eviscerate",
    "Fury": "ability_warrior_innerrage",
    "Protection": "ability_warrior_defensivestance"
  }
}

CLASS_TO_HTML = {
    'Death Knight': 'death-knight',
    'Druid': 'druid',
    'Hunter': 'hunter',
    'Mage': 'mage',
    'Paladin': 'paladin',
    'Priest': 'priest',
    'Rogue': 'rogue',
    'Shaman': 'shaman',
    'Warlock': 'warlock',
    'Warrior': 'warrior'
}

CLASS_FROM_HTML = {
    "death-knight": "Death Knight",
    "druid": "Druid",
    "hunter": "Hunter",
    "mage": "Mage",
    "paladin": "Paladin",
    "priest": "Priest",
    "rogue": "Rogue",
    "shaman": "Shaman",
    "warlock": "Warlock",
    "warrior": "Warrior"
}


CLASSES_LIST = list(CLASSES)
# SPECS_LIST = {name: list(v) for name, v in CLASSES.items()}
# SPECS_LIST = [icon for v in CLASSES.values() for icon in v.values()]
SPECS_LIST = [(sname or cname, icon) for cname, v in CLASSES.items() for sname, icon in v.items()]




DATES_CACHE = {}

def get_dates():
    if not DATES_CACHE:
        dates = json_read("WarmaneBossFights/__dates")
        DATES_CACHE["DATES"] = dates
        DATES_CACHE["REVERSED"] = list(reversed(dates.items()))
    return DATES_CACHE

def find_date(report_id: int) -> str:
    dates: list[tuple[str, int]] = get_dates()["REVERSED"]
    for date, date_report_id in dates:
        if report_id > date_report_id:
            return date



def add_new_numeric_data(data_total: defaultdict, data_new: dict):
    for source, amount in data_new.items():
        data_total[source] += amount


def get_last_line(filename):
    with open(filename, 'rb') as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        return f.readline().decode()

def get_last_mod(file_name):
    return datetime.fromtimestamp(os.path.getmtime(file_name))

@running_time
def logs_edit_time(file_name):
    dt_last_edit = get_last_mod(file_name)
    _to_dt = to_dt_closure(dt_last_edit.year)
    last_line = get_last_line(file_name)
    dt_last_line = _to_dt(last_line)
    return abs(dt_last_edit-dt_last_line).total_seconds()


REPORTS_FILTER_FILES = {
    'allowed': os.path.join(DIR_PATH, "__allowed.txt"),
    'private': os.path.join(DIR_PATH, "__private.txt"),
}
FILTERED_LOGS = {}
def get_logs_filter(filter_type: str):
    if filter_type in FILTERED_LOGS:
        return FILTERED_LOGS[filter_type]
    data = FILTERED_LOGS[filter_type] = file_read(REPORTS_FILTER_FILES[filter_type]).split('\n')
    return data


UPLOADED_JSON = os.path.join(DIR_PATH, '_uploaded_data.json')
UPLOADED = json_read(UPLOADED_JSON)
def save_upload_cache():
    json_write(UPLOADED_JSON, UPLOADED)


MAX_PW_ATTEMPTS = 5
WRONG_PW_FILE = os.path.join(DIR_PATH, '_wrong_pw.json')
WRONG_PW = json_read(WRONG_PW_FILE)

def wrong_pw(ip):
    attempt = WRONG_PW.get(ip, 0) + 1
    WRONG_PW[ip] = attempt
    if attempt > MAX_PW_ATTEMPTS:
        json_write(WRONG_PW_FILE, WRONG_PW)

def banned(ip):
    return WRONG_PW.get(ip, 0) > MAX_PW_ATTEMPTS


