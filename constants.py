import json
import logging
import os
import pickle
import re
import zlib
from collections import defaultdict
from datetime import datetime, timedelta
from time import perf_counter


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        # print('[CREATED FOLDER]', path)

def new_folder_path(root, name):
    new_folder = os.path.join(root, name)
    create_folder(new_folder)
    return new_folder

real_path = os.path.realpath(__file__)
PATH_DIR = os.path.dirname(real_path)
LOGS_DIR = new_folder_path(PATH_DIR, "LogsDir")
LOGS_RAW_DIR = new_folder_path(PATH_DIR, "LogsRaw")
UPLOADS_DIR = new_folder_path(PATH_DIR, "uploads")
UPLOADED_DIR = new_folder_path(UPLOADS_DIR, "uploaded")
TOP_DIR = new_folder_path(PATH_DIR, 'top')

LOGGING_FORMAT = f'[%(asctime)s] [%(levelname)s] "{PATH_DIR}\%(filename)s:%(lineno)s" | %(message)s'
LOGGING_FORMAT = f'[%(asctime)s] [%(levelname)s] "%(filename)s:%(lineno)s" | %(message)s'
def setup_logger(logger_name, log_file):
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter(LOGGING_FORMAT)
    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

LOGGER_MAIN_FILE = os.path.join(PATH_DIR,'_main.log')
LOGGER_MAIN = setup_logger('logger_main', LOGGER_MAIN_FILE)
LOGGER_LOGS_FILE = os.path.join(PATH_DIR,'_logs.log')
LOGGER_LOGS = setup_logger('logger_logs', LOGGER_LOGS_FILE)
UPLOAD_LOGGER_FILE = os.path.join(UPLOADS_DIR, 'upload.log')
UPLOAD_LOGGER = setup_logger('logger_upload', UPLOAD_LOGGER_FILE)

T_DELTA_2SEC = timedelta(seconds=2)
T_DELTA_15SEC = timedelta(seconds=15)
T_DELTA_1MIN = timedelta(minutes=1)
T_DELTA_2MIN = timedelta(minutes=2)
T_DELTA_5MIN = timedelta(minutes=5)
T_DELTA_10MIN = timedelta(minutes=10)
T_DELTA_15MIN = timedelta(minutes=15)
T_DELTA_20MIN = timedelta(minutes=20)
T_DELTA_30MIN = timedelta(minutes=30)

LOGS_CUT_NAME = "LOGS_CUT"
UPLOAD_STATUS_INFO = {}
ICON_CDN_LINK = "https://wotlk.evowow.com/static/images/wow/icons/large"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

FLAG_ORDER = [
    "SPELL_DISPEL", "SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE", "SPELL_HEAL",
    "SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_REMOVED",
    "SPELL_CAST_SUCCESS", "SPELL_EXTRA_ATTACKS", "SPELL_ENERGIZE",
    "SPELL_MISSED", "SPELL_CAST_START",
    "SPELL_AURA_APPLIED_DOSE", "SPELL_AURA_REMOVED_DOSE",
]

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
    "00815E": "Ignis the Furnace Master",
    "0081A2": "Razorscale",
    "00820D": "XT-002 Deconstructor",
    "008063": "Steelbreaker",
    "00809F": "Runemaster Molgeim",
    "008059": "Stormcaller Brundir",
    "0080A2": "Kologarn",
    "0082EB": "Auriaya",
    "00808A": "Freya",
    "00804D": "Hodir",
    "008246": "Mimiron",
    "008061": "Thorim",
    "0081F7": "General Vezax",
    "008208": "Yogg-Saron",
    "008067": "Algalon the Observer",

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

MULTIBOSSES = {
    "Halion": ['009BB7', '009CCE', '009CD2'],
    "Gunship": ['0092A4', '00915F'],
    "Blood Prince Council": ['009454', '009455', '009452'],
    "Northrend Beasts": ['0087EC', '008948', '0087EF', '0087ED'],
    "Faction Champions": list(TOC_CHAMPIONS),
    "Twin Val'kyr": ['0086C0', '0086C1'],
    "The Four Horsemen": ["003EBF", "007755", "003EC1", "003EC0"],
    "Mimiron": ["008246", "008208", "008373", "008386"],
    "Assembly of Iron": ["008063", "00809F", "008059"],
    "Kologarn": ["0080A2", "0080A5", "0080A6"],
    "XT-002 Deconstructor": ["00820D", "008231"],
    "Freya": ["00808A", "0081B3", "0081B2", "008096", "0081CC", "008094", "008097"],
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
    6: "holyfire", #-- Fire + Holy (Radiant)
    # 9: "stormstrike", #-- Nature + Physical
    # 10: "holystorm", #-- Nature + Holy
    12: "firestorm", #Nature + Fire
    17: "froststrike", #Frost + Physical
    # 18: "holyfrost", #-- Frost + Holy
    20: "frostfire", #Frost + Fire
    24: "froststorm", #-- Frost + Nature
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
    9: "stormstrike", #-- Nature + Physical
    10: "holystorm", #-- Nature + Holy
    18: "holyfrost", #-- Frost + Holy
    36: "shadowflame", #-- Shadow + Fire
    65: "spellstrike", #-- Arcane + Physical
    72: "spellstorm", #-- Arcane + Nature
    28: "elemental", #-- Frost + Nature + Fire
    124: "chromatic", #-- Arcane + Shadow + Frost + Nature + Fire
    126: "magic", #-- Arcane + Shadow + Frost + Nature + Fire + Holy
}

ENV_DAMAGE = {
    "FALLING":  "90001",
    "LAVA":     "90002",
    "DROWNING": "90003",
    "FIRE":     "90004",
    "FATIGUE":  "90005",
    "SLIME":    "90006",
}

SPELL_BOOK = {
    "49222": [0, "Bone Shield"],
    "49560": [0, "Death Grip"],
    "51735": [0, "Ebon Plague"],
    "55095": [0, "Frost Fever"],
    "57623": [0, "Horn of Winter"],
    "49016": [0, "Hysteria"],
    "49909": [0, "Icy Touch"],
    "51124": [0, "Killing Machine"],
    "66992": [0, "Plague Strike"],
    "50526": [0, "Wandering Plague"],
    "48468": [1, "Insect Swarm"],
    "24932": [1, "Leader of the Pack"],
    "48566": [1, "Mangle (Cat)"],
    "48422": [1, "Master Shapeshifter"],
    "48463": [1, "Moonfire"],
    "48574": [1, "Rake"],
    "48443": [1, "Regrowth"],
    "70691": [1, "Rejuvenation"],
    "52610": [1, "Savage Roar"],
    "48572": [1, "Shred"],
    "48465": [1, "Starfire"],
    "48562": [1, "Swipe (Bear)"],
    "62078": [1, "Swipe (Cat)"],
    "48438": [1, "Wild Growth"],
    "48461": [1, "Wrath"],
    "48466": [1, "Hurricane"],
    "33831": [1, "Force of Nature"],
    "48391": [1, "Owlkin Frenzy"],
    "22812": [1, "Barkskin"],
    "49050": [2, "Aimed Shot"],
    "53209": [2, "Chimera Shot"],
    "35079": [2, "Misdirection"],
    "49001": [2, "Serpent Sting"],
    "58433": [2, "Volley"],
    "36032": [3, "Arcane Blast"],
    "42921": [3, "Arcane Explosion"],
    "12042": [3, "Arcane Power"],
    "42938": [3, "Blizzard"],
    "42833": [3, "Fireball"],
    "12472": [3, "Icy Veins"],
    "12654": [3, "Ignite"],
    "44401": [3, "Missile Barrage"],
    "48827": [4, "Avenger\'s Shield"],
    "53654": [4, "Beacon of Light"],
    "48819": [4, "Consecration"],
    "642": [4, "Divine Shield"],
    "66922": [4, "Flash of Light"],
    "25898": [4, "Greater Blessing of Kings"],
    "25899": [4, "Greater Blessing of Sanctuary"],
    "48938": [4, "Greater Blessing of Wisdom"],
    "10308": [4, "Hammer of Justice"],
    "53595": [4, "Hammer of the Righteous"],
    "67485": [4, "Hand of Reckoning"],
    "48823": [4, "Holy Shock"],
    "20272": [4, "Illumination"],
    "58597": [4, "Sacred Shield"],
    "26017": [4, "Vindication"],
    "21084": [4, "Seal of Righteousness"],
    "25780": [4, "Righteous Fury"],
    "31884": [4, "Avenging Wrath"],
    "54172": [4, "Divine Storm"],
    "59578": [4, "The Art of War"],
    "35395": [4, "Crusader Strike"],
    "48089": [5, "Circle of Healing"],
    "47753": [5, "Divine Aegis"],
    "58381": [5, "Mind Flay"],
    "53000": [5, "Penance"],
    "25217": [5, "Power Word: Shield"],
    "25392": [5, "Prayer of Fortitude"],
    "48170": [5, "Prayer of Shadow Protection"],
    "32999": [5, "Prayer of Spirit"],
    "48068": [5, "Renew"],
    "48125": [5, "Shadow Word: Pain"],
    "15473": [5, "Shadowform"],
    "64085": [5, "Vampiric Touch"],
    "6788": [5, "Weakened Soul"],
    "22482": [6, "Blade Flurry"],
    "35548": [6, "Combat Potency"],
    "57993": [6, "Envenom"],
    "48668": [6, "Eviscerate"],
    "52874": [6, "Fan of Knives"],
    "48659": [6, "Feint"],
    "51637": [6, "Focused Attacks"],
    "8643": [6, "Kidney Shot"],
    "57842": [6, "Killing Spree"],
    "48638": [6, "Sinister Strike"],
    "1784": [6, "Stealth"],
    "57933": [6, "Tricks of the Trade"],
    "52759": [7, "Ancestral Awakening"],
    "51886": [7, "Cleanse Spirit"],
    "16246": [7, "Clearcasting"],
    "379": [7, "Earth Shield"],
    "16166": [7, "Elemental Mastery"],
    "51533": [7, "Feral Spirit"],
    "60043": [7, "Lava Burst"],
    "49238": [7, "Lightning Bolt"],
    "49279": [7, "Lightning Shield"],
    "16190": [7, "Mana Tide Totem"],
    "70806": [7, "Rapid Currents"],
    "61301": [7, "Riptide"],
    "32176": [7, "Stormstrike"],
    "53390": [7, "Tidal Waves"],
    "57961": [7, "Water Shield"],
    "25504": [7, "Windfury Attack"],
    "47813": [8, "Corruption"],
    "47893": [8, "Fel Armor"],
    "63321": [8, "Life Tap"],
    "47241": [8, "Metamorphosis"],
    "686": [8, "Shadow Bolt"],
    "25228": [8, "Soul Link"],
    "47843": [8, "Unstable Affliction"],
    "2457": [9, "Battle Stance"],
    "2458": [9, "Berserker Stance"],
    "29131": [9, "Bloodrage"],
    "23880": [9, "Bloodthirst"],
    "47440": [9, "Commanding Shout"],
    "59653": [9, "Damage Shield"],
    "12292": [9, "Death Wish"],
    "12721": [9, "Deep Wounds"],
    "71": [9, "Defensive Stance"],
    "47450": [9, "Heroic Strike"],
    "44949": [9, "Whirlwind"]
}

SPELL_BOOK_SPEC = {
    "death-knight": {
        "49016": 1, # Hysteria
        "55233": 1, # Vampiric Blood
        "49005": 1, # Mark of Blood
        "48982": 1, # Rune Tap
        "50449": 1, # Bloody Vengeance
        "70654": 1, # Blood Armor

        "55268": 2, # Frost Strike
        "51271": 2, # Unbreakable Armor
        "51411": 2, # Howling Blast
        "50401": 2, # Razor Frost
        "51714": 2, # Frost Vulnerability
        
        "49206": 3, # Summon Gargoyle
        "55271": 3, # Scourge Strike
        "50526": 3, # Wandering Plague
        "51735": 3, # Ebon Plague
        "66803": 3, # Desolation
    },
    "druid": {
        "60433": 1, # Earth and Moon
        "48468": 1, # Insect Swarm
        "48518": 1, # Eclipse (Lunar)
        "48517": 1, # Eclipse (Solar)
        "33831": 1, # Force of Nature
        "71023": 1, # Languish
        "70721": 1, # Omen of Doom
        "53195": 1, # Starfall
        "53227": 1, # Typhoon

        "50213": 2, # Tiger's Fury
        "62078": 2, # Swipe (Cat)
        "48572": 2, # Shred
        "52610": 2, # Savage Roar
        "62606": 2, # Savage Defense
        "49800": 2, # Rip
        "48574": 2, # Rake
        "48566": 2, # Mangle (Cat)
        "51178": 2, # King of the Jungle
        "17099": 2, # Furor
        "48577": 2, # Ferocious Bite
        "49376": 2, # Feral Charge - Cat
        "16857": 2, # Faerie Fire (Feral)
        "47468": 2, # Claw

        "53251": 3, # Wild Growth
        "48542": 3, # Revitalize
        "34123": 3, # Tree of Life
        "18562": 3, # Swiftmend
        "48504": 3, # Living Seed
    },
    "hunter": {
        "19574": 1, # Bestial Wrath
        "19577": 1, # Intimidation
        "53209": 2, # Chimera Shot
        "60053": 3, # Explosive Shot
    },
    "mage": {
        "44781": 1, # Arcane Barrage
        "12042": 1, # Arcane Power
        "55360": 2, # Living Bomb
        "48108": 2, # Hot Streak
        "28682": 2, # Combustion
        "11958": 3, # Cold Snap
        "12579": 3, # Winter's Chill
        "31687": 3, # Summon Water Elemental
        "44572": 3, # Deep Freeze
    },
    "paladin": {
        "53654": 1, # Beacon of Light
        "48825": 1, # Holy Shock
        "54149": 1, # Infusion of Light
        "31842": 1, # Divine Illumination

        "53595": 2, # Hammer of the Righteous
        "66233": 2, # Ardent Defender
        "48827": 2, # Avenger's Shield
        "20132": 2, # Redoubt
        "48952": 2, # Holy Shield
        "57319": 2, # Blessing of Sanctuary
        "70760": 2, # Deliverance
        
        "59578": 3, # The Art of War
        "35395": 3, # Crusader Strike
        "53385": 3, # Divine Storm
    },
    "priest": {
        "63944": 1, # Renewed Hope
        "47755": 1, # Rapture
        "52985": 1, # Penance
        "47753": 1, # Divine Aegis
        "59891": 1, # Borrowed Time
        "15359": 1, # Inspiration
        
        "63734": 2, # Serendipity
        "63544": 2, # Empowered Renew
        "63725": 2, # Holy Concentration
        "48089": 2, # Circle of Healing
        "47788": 2, # Guardian Spirit

        "48160": 3, # Vampiric Touch
        "63675": 3, # Improved Devouring Plague
        "59000": 3, # Improved Spirit Tap
        "48156": 3, # Mind Flay
        "33198": 3, # Misery
        "61792": 3, # Shadowy Insight
        "15290": 3, # Vampiric Embrace
        "15473": 3, # Shadowform
        "47585": 3, # Dispersion
    },
    "rogue": {
        "57993": 1, # Envenom
        "48666": 1, # Mutilate
        "14177": 1, # Cold Blood

        "48638": 2, # Sinister Strike
        "13750": 2, # Adrenaline Rush
        "13877": 2, # Blade Flurry
        "51690": 2, # Killing Spree

        "51713": 3, # Shadow Dance
        "36554": 3, # Shadowstep
        "14183": 3, # Premeditation
        "14185": 3, # Preparation
        "48660": 3, # Hemorrhage
    },
    "shaman": {
        "57722": 1, # Totem of Wrath
        "59159": 1, # Thunderstorm
        "16166": 1, # Elemental Mastery
        "49240": 1, # Lightning Bolt (Proc)
        "49269": 1, # Chain Lightning (Proc)

        "60103": 2, # Lava Lash
        "51533": 2, # Feral Spirit
        "30823": 2, # Shamanistic Rage
        "17364": 2, # Stormstrike
        "70829": 2, # Elemental Rage

        "379": 3, # Earth Shield
        "53390": 3, # Tidal Waves
        "52752": 3, # Ancestral Awakening
        "61301": 3, # Riptide
        "16190": 3, # Mana Tide Totem
        "51886": 3, # Cleanse Spirit
    },
    "warlock": {
        "59164": 1, # Haunt
        "47843": 1, # Unstable Affliction
        "64371": 1, # Eradication

        "71165": 2, # Molten Core
        "47241": 2, # Metamorphosis
        "63167": 2, # Decimation
        "47193": 2, # Demonic Empowerment

        "59172": 3, # Chaos Bolt
        "47847": 3, # Shadowfury
        "17962": 3, # Conflagrate
    },
    "warrior": {
        "7384": 1, # Overpower
        "47486": 1, # Mortal Strike
        "12328": 1, # Sweeping Strikes
        "52437": 1, # Sudden Death
        "60503": 1, # Taste for Blood

        "23881": 2, # Bloodthirst
        "12292": 2, # Death Wish

        "46968": 3, # Shockwave
        "47498": 3, # Devastate
    },
}

SERVERS = {
    "0x06": "Lordaeron",
    "0x07": "Icecrown",
    "0x0D": "Frostmourne3",
    "0x0C": "Frostmourne2",
    "0x0A": "Blackrock",
}

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

CLASSES_LIST = list(CLASSES)
SPECS_LIST = [(sname or cname, icon) for cname, v in CLASSES.items() for sname, icon in v.items()]

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

def get_ms(pc):
    if pc is None:
        return -1
    return int((perf_counter()-pc)*1000)

def running_time(f):
    def running_time_inner(*args, **kwargs):
        pc = perf_counter()
        q = f(*args, **kwargs)
        msg = f"[PERFOMANCE] Done in {get_ms(pc):>6,} ms with {f.__module__}.{f.__name__}"
        LOGGER_LOGS.debug(msg)
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
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}

def json_read_no_exception(path: str):
    path = add_extention(path, '.json')
    with open(path) as file:
        return json.load(file)

def json_write(path: str, data, backup=False, indent=2, sep=None):
    path = add_extention(path, '.json')
    if backup:
        save_backup(path)
    with open(path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, default=sorted, indent=indent, separators=sep)


def bytes_read(path: str, ext=None):
    path = add_extention(path, ext)
    try:
        with open(path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        return b''

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
def zlib_compress(__data: bytes, level=7):
    return zlib.compress(__data, level=level)

def zlib_pickle_make(data_raw, level=7):
    data_pickle = pickle_dumps(data_raw)
    comresesed = zlib_compress(data_pickle, level)
    return comresesed

@running_time
def zlib_pickle_write(data_raw, path: str, level=7):
    path = add_extention(path, '.pickle.zlib')
    zlib_pickle = zlib_pickle_make(data_raw, level)
    bytes_write(path, zlib_pickle)

def zlib_text_make(data_raw: str, level=7):
    data_enc = data_raw.encode()
    comresesed = zlib_compress(data_enc, level)
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

def zlib_text_bytes_write(data_raw: bytes, path: str, level=7):
    path = add_extention(path, '.zlib')
    zlib_text = zlib_compress(data_raw, level)
    bytes_write(path, zlib_text)


@running_time
def logs_splitlines(logs: str):
    return logs.splitlines()

@running_time
def prepare_logs(file_name):
    logs_raw = bytes_read(file_name)
    logs_raw_decoded = logs_raw.decode()
    return logs_splitlines(logs_raw_decoded)

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

__year = get_now().year
__p_bytes_fa = re.compile(b'(\d+)').findall
def to_dt_bytes(s, year=__year):
    q = list(map(int, __p_bytes_fa(s[:18])))
    dt = datetime(year, *q)
    if dt > get_now():
        return dt.replace(year=dt.year-1)
    return dt

def to_dt_bytes_wrap(year=None):
    if year is None:
        year = get_now().year
    findall = re.compile(b'(\d+)').findall
    def inner(s):
        q = list(map(int, findall(s[:18])))
        return datetime(year, *q)
    return inner

def get_time_delta(s: str, f: str, _to_dt=to_dt):
    return _to_dt(f) - _to_dt(s)

def get_time_delta_wrap(_to_dt=to_dt):
    def inner(s: str, f: str):
        return _to_dt(f) - _to_dt(s)
    return inner

def get_fight_duration(s, f):
    return get_time_delta(s, f).total_seconds()

def convert_duration(t):
    milliseconds = int(t % 1 * 1000)
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = t // 3600
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0<3}"

def get_folders(path) -> list[str]:
    return sorted(next(os.walk(path))[1])

def get_files(path) -> list[str]:
    return sorted(next(os.walk(path))[2])

def get_all_files(path=None, ext=None):
    if path is None:
        path = '.'
    files = get_files(path)
    if ext is None:
        return files
    ext = fix_extention(ext)
    return [file for file in files if file.endswith(ext)]

REPORTS_FILTER_FILES = {
    'allowed': os.path.join(PATH_DIR, "__allowed.txt"),
    'private': os.path.join(PATH_DIR, "__private.txt"),
}
FILTERED_LOGS = {}
def get_logs_filter(filter_type: str):
    if filter_type in FILTERED_LOGS:
        return FILTERED_LOGS[filter_type]
    data = file_read(REPORTS_FILTER_FILES[filter_type])
    data = data.splitlines()
    FILTERED_LOGS[filter_type] = data
    return data

def get_folders_filter(filter=None, public_only=True):
    folders = get_folders('LogsDir')
    if filter is not None:
        folders = [name for name in folders if filter in name]
    if public_only:
        filter_list = get_logs_filter('private')
        folders = [name for name in folders if name not in filter_list]
    return folders

def get_report_name_info(name: str):
    info = name.split('--')
    return {
        "date": info[0],
        "time": info[1],
        "name": info[2],
        "server": info[3],
    }


def add_new_numeric_data(data_total: defaultdict, data_new: dict):
    for source, amount in data_new.items():
        data_total[source] += amount


def get_last_line(filename, skip_lines=0):
    with open(filename, 'rb') as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            for _ in range(10000):
                f.seek(-2, os.SEEK_CUR)
                if f.read(1) == b'\n':
                    if skip_lines < 1:
                        break
                    skip_lines -= 1
        except OSError:
            f.seek(0)
        return f.readline().decode()

def get_last_mod(file_name):
    return datetime.fromtimestamp(os.path.getmtime(file_name))

def logs_edit_time(file_name):
    dt_last_edit = get_last_mod(file_name)
    _to_dt = to_dt_closure(dt_last_edit.year)
    try:
        last_line = get_last_line(file_name)
        dt_last_line = _to_dt(last_line)
    except Exception:
        last_line = get_last_line(file_name, skip_lines=1)
        dt_last_line = _to_dt(last_line)
    return abs(dt_last_edit-dt_last_line).total_seconds()


MAX_PW_ATTEMPTS = 5
WRONG_PW_FILE = os.path.join(PATH_DIR, '_wrong_pw.json')
WRONG_PW = json_read(WRONG_PW_FILE)

def wrong_pw(ip):
    attempt = WRONG_PW.get(ip, 0) + 1
    WRONG_PW[ip] = attempt
    if attempt >= MAX_PW_ATTEMPTS:
        json_write(WRONG_PW_FILE, WRONG_PW, backup=True)
    return MAX_PW_ATTEMPTS - attempt

def banned(ip):
    return WRONG_PW.get(ip, 0) >= MAX_PW_ATTEMPTS


