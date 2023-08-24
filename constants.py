import logging
import os
import re
from datetime import datetime, timedelta
from time import perf_counter

import file_functions


DEFAULT_SERVER_NAME = "Unknown"
LOGS_CUT_NAME = "LOGS_CUT.zlib"
TOP_FILE_NAME = "top.json"
PANDAS_COMPRESSION = "zstd"
NIL_GUID = '0x0000000000000000'

REPORT_NAME_STRUCTURE = ("date", "time", "author", "server")

real_path = os.path.realpath(__file__)
PATH_DIR = os.path.dirname(real_path)
LOGS_DIR = file_functions.new_folder_path(PATH_DIR, "LogsDir")
LOGS_RAW_DIR = file_functions.new_folder_path(PATH_DIR, "LogsRaw")
TOP_DIR = file_functions.new_folder_path(PATH_DIR, 'top')
UPLOADS_DIR = file_functions.new_folder_path(PATH_DIR, "uploads")
UPLOADED_DIR = file_functions.new_folder_path(UPLOADS_DIR, "uploaded")
UPLOADS_TEXT = file_functions.new_folder_path(UPLOADS_DIR, "0archive_pending")
LOGGERS_DIR = file_functions.new_folder_path(PATH_DIR, "_loggers")
STATIC_DIR = file_functions.new_folder_path(PATH_DIR, 'static')
REPORTS_ALLOWED = os.path.join(PATH_DIR, "__allowed.txt")
REPORTS_PRIVATE = os.path.join(PATH_DIR, "__private.txt")
SPELL_ICONS_DB = os.path.join(PATH_DIR, "x_spells_icons.json")

LOGGING_FORMAT_DEFAULT = '''%(asctime)s | %(levelname)-5s | %(filename)18s:%(lineno)-4s | %(message)s'''
LOGGING_FORMAT = {
    "connections" : '''%(asctime)s | %(message)s''',
}
def setup_logger(logger_name):
    log_file = os.path.join(LOGGERS_DIR, f'{logger_name}.log')
    logger = logging.getLogger(logger_name)
    _format = LOGGING_FORMAT.get(logger_name, LOGGING_FORMAT_DEFAULT)
    formatter = logging.Formatter(_format)
    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

LOGGER_CONNECTIONS = setup_logger('connections')
LOGGER_REPORTS = setup_logger('reports')
LOGGER_UPLOADS = setup_logger('uploads')
LOGGER_UNUSUAL_SPELLS = setup_logger('unusual_spells')
LOGGER_MEMORY = setup_logger('memory')


T_DELTA = {
    "2SEC": timedelta(seconds=2),
    "15SEC": timedelta(seconds=15),
    "30SEC": timedelta(seconds=30),
    "1MIN": timedelta(minutes=1),
    "2MIN": timedelta(minutes=2),
    "3MIN": timedelta(minutes=3),
    "5MIN": timedelta(minutes=5),
    "10MIN": timedelta(minutes=10),
    "15MIN": timedelta(minutes=15),
    "20MIN": timedelta(minutes=20),
    "30MIN": timedelta(minutes=30),
    "14H": timedelta(hours=14),
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

FLAG_ORDER = [
    "SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_REMOVED",
    "SPELL_AURA_APPLIED_DOSE", "SPELL_AURA_REMOVED_DOSE",
    "SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE",
    "SPELL_HEAL", "SPELL_PERIODIC_HEAL",
    "SPELL_MISSED", "SPELL_PERIODIC_MISSED",
    "SWING_DAMAGE", "SWING_MISSED",
    "RANGE_DAMAGE", "RANGE_MISSED",
    "SPELL_CAST_START", "SPELL_CAST_SUCCESS",
    "SPELL_DISPEL", "SPELL_DISPEL_FAILED", "SPELL_STOLEN",
    "SPELL_SUMMON", "SPELL_CREATE",
    "SPELL_ENERGIZE", "SPELL_PERIODIC_ENERGIZE",
    "DAMAGE_SHIELD", "DAMAGE_SHIELD_MISSED", "DAMAGE_SPLIT",
    "UNIT_DIED", "SPELL_INSTAKILL", "PARTY_KILL", "SPELL_RESURRECT",
    "SPELL_INTERRUPT",
    "SPELL_EXTRA_ATTACKS",
    "ENVIRONMENTAL_DAMAGE",
    "SPELL_DRAIN",
    "SPELL_PERIODIC_LEECH",
    "ENCHANT_APPLIED",
    "ENCHANT_REMOVED",
]

ICONS = {
    "naxx": "achievement_dungeon_naxxramas_10man",
    "maly": "achievement_dungeon_nexusraid_heroic",
    "os": "achievement_dungeon_coablackdragonflight_heroic",
    "voa": "inv_essenceofwintergrasp",
    "uld": "spell_shadow_shadesofdarkness",
    "toc": "achievement_reputation_argentchampion",
    "icc": "achievement_zone_icecrown_01",
    "rs": "spell_shadow_twilight",
}

BOSSES_GUIDS = {
    "007F23": "Highlord's Nemesis Trainer",
    "0079AA": "Heroic Training Dummy",
    
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
    "009CCE": "Halion",
    
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
    
    # "008159": "Flame Leviathan",
    "00815E": "Ignis the Furnace Master",
    "0081A2": "Razorscale",
    "00820D": "XT-002 Deconstructor",
    "008231": "Heart of the Deconstructor",
    "00809F": "Runemaster Molgeim",
    "008059": "Stormcaller Brundir",
    "008063": "Steelbreaker",
    "0080A2": "Kologarn",
    "0082EB": "Auriaya",
    "00808A": "Freya",
    "00804D": "Hodir",
    "008061": "Thorim",
    "008246": "Mimiron",
    "008298": "Leviathan Mk II",
    "008373": "VX-001",
    "008386": "Aerial Command Unit",
    "0081F7": "General Vezax",
    "008208": "Yogg-Saron",
    "008067": "Algalon the Observer",

    # Magtheridon's Lair
    "004369": "Magtheridon",
    # Karazhan
    "003F33": "Shadikith the Glider",
    "003F34": "Rokad the Ravager",
    "003F35": "Hyakiss the Lurker",
    "003D48": "Terestian Illhoof",
    "003D49": "Netherspite",
    "003D4A": "Prince Malchezaar",
    "003D4B": "The Curator",
    "003F18": "Attumen the Huntsman",
    "00408C": "Shade of Aran",
    "004049": "Maiden of Virtue",
    "004349": "Nightbane",
    "003D47": "Moroes",
    "00426F": "Lady Keira Berrybuck",
    "004DA0": "Lady Catriona Von'Indi",
    "004DA1": "Lord Crispin Ference",
    "004DA2": "Baron Rafe Dreuger",
    "004DA3": "Baroness Dorothea Millstipe",
    "004DA4": "Lord Robin Daris",
    # Opera House
    "00447F": "Dorothee",
    "00448C": "Tito",
    "00448A": "Roar",
    "004487": "Strawman",
    "00448B": "Tinhead",
    "0046F8": "The Crone",
    "004471": "The Big Bad Wolf",
    "00447D": "Julianne",
    "00447E": "Romulo",
    # Gruul"s Lair
    "004A64": "Gruul the Dragonkiller",
    "00498F": "High King Maulgar",
    "004990": "Krosh Firehand",
    "004992": "Olm the Summoner",
    "004993": "Kiggler the Crazed",
    "004994": "Blindeye the Seer",
    # Serpentshrine Cavern
    "0052E0": "Hydross the Unstable",
    "0052E1": "The Lurker Below",
    "0052DF": "Leotheras the Blind",
    "0052DE": "Fathom-Lord Karathress",
    "0055CE": "Fathom-Guard Sharkkis",
    "0055CD": "Fathom-Guard Tidalvess",
    "0055CC": "Fathom-Guard Caribdis",
    "0052DD": "Morogrim Tidewalker",
    "0052DC": "Lady Vashj",
    # The Eye
    "004C3A": "Al'ar",
    "004C3C": "Void Reaver",
    "004975": "High Astromancer Solarian",
    "004CA6": "Kael'thas Sunstrider",
    "004E5C": "Lord Sanguinar",
    "004E5E": "Grand Astromancer Capernian",
    "004E5F": "Master Engineer Telonicus",
    "004E60": "Thaladred the Darkener",
    # Black Temple
    "005967": "High Warlord Naj'entus",
    "005972": "Supremus",
    "005939": "Shade of Akama",
    "005957": "Teron Gorefiend",
    "0059A4": "Gurtogg Bloodboil",
    "005948": "Reliquary of Souls",
    "005B7A": "Essence of Suffering",
    "005B7B": "Essence of Desire",
    "005B7C": "Essence of Anger",
    "0059A3": "Mother of Shahraz",
    # Illidari Council
    "0059A5": "High Nethermancer Zerevor",
    "0059A6": "Gathios the Shatterer",
    "0059A7": "Lady Malande",
    "0059A8": "Veras Darkshadow",
    "005985": "Illidan",
    # Mount Hyjal
    "004567": "Rage Winterchill",
    "004590": "Anetheron",
    "0045E0": "Kaz'rogal",
    "0045B2": "Azgalor",
    "004630": "Archimonde",
    # Zul"Aman
    "005C16": "Akil'zon",
    "005C18": "Nalorakk",
    "005C1A": "Jan'alai",
    "005C19": "Halazzi",
    "005EAF": "Hex Lord Malacrass",
    "005D37": "Zul'jin",
    #Sunwell Plateau
    "006112": "Kalecgos",
    "00613C": "Sathrovarr the Corruptor",
    "006132": "Brutallus",
    "0061CE": "Felmyst",
    "00624E": "Grand Warlock Alythess",
    "00624D": "Lady Sacrolash",
    "00648D": "M'uru",
    "0064F0": "Entropius",
    "0062E3": "Kil'jaeden"
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
MULTIBOSSES = {
    "Halion": ["009BB7", "009CCE", "009CD2"],
    "Gunship": ["0092A4", "00915F"],
    "Blood Prince Council": ["009454", "009455", "009452"],
    "Northrend Beasts": ["0087EC", "008948", "0087EF", "0087ED"],
    "Faction Champions": list(TOC_CHAMPIONS),
    "Twin Val'kyr": ["0086C0", "0086C1"],
    "The Four Horsemen": ["003EBF", "007755", "003EC1", "003EC0"],
    "Mimiron": ["008246", "008298", "008373", "008386"],
    "Assembly of Iron": ["008063", "00809F", "008059"],
    # "Kologarn": ["0080A2", "0080A5", "0080A6"],
    "XT-002 Deconstructor": ["00820D", "008231"],
    "Yogg-Saron": ["008208", "008170", "0084C1", "0084BF"],
    "Razorscale": ["0081A2", "00826C", "008436", "0082AD"],

    "Servant Quarters": ["003F33", "003F34", "003F35"],
    "Moroes": ["003D47", "00426F", "004DA0", "004DA1", "004DA2", "004DA3", "004DA4"],
    "Opera House": ["00447F", "00448C", "00448A", "004487", "00448B", "0046F8", "004471", "00447D", "00447E"],
    "Fathom-Lord Karathress": ["0052DE", "0055CE", "0055CD", "0055CC"],
    "Kael'thas Sunstrider": ["004CA6", "004E5C", "004E5E", "004E5F", "004E60"],
    "Reliquary of Souls": ["005948", "005B7A", "005B7B", "005B7C"],
    "Illidari Council": ["0059A5", "0059A6", "0059A7", "0059A8"],
    "Kalecgos": ["006112", "00613C"],
    "Eredar Twins": ["00624E", "00624D"],
    "M'uru": ["00648D", "0064F0"],
}

def convert_to_html_name(name: str):
    return name.lower().replace(' ', '-').replace("'", '')

ALL_FIGHT_NAMES = set(BOSSES_GUIDS.values()) | set(MULTIBOSSES)
BOSSES_FROM_HTML = {
    convert_to_html_name(name): name
    for name in ALL_FIGHT_NAMES
}

BOSSES_GUIDS.update(TOC_CHAMPIONS)

ENCOUNTER_NAMES = {
    boss_guid: encounter_name
    for encounter_name, boss_guids in MULTIBOSSES.items()
    for boss_guid in boss_guids
}

def convert_to_fight_name(boss_id: str):
    if len(boss_id) == 18:
        boss_id = boss_id[6:-6]
    if boss_id in ENCOUNTER_NAMES:
        return ENCOUNTER_NAMES[boss_id]
    if boss_id in BOSSES_GUIDS:
        return BOSSES_GUIDS[boss_id]
    
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
    9: "stormstrike", #-- Nature + Physical
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
    10: "holystorm", #-- Nature + Holy
    18: "holyfrost", #-- Frost + Holy
    36: "shadowflame", #-- Shadow + Fire
    65: "spellstrike", #-- Arcane + Physical
    72: "spellstorm", #-- Arcane + Nature
    28: "elemental", #-- Frost + Nature + Fire
    124: "chromatic", #-- Arcane + Shadow + Frost + Nature + Fire
    126: "magic", #-- Arcane + Shadow + Frost + Nature + Fire + Holy
}

COMBINE_SPELLS = {
    "29131":  "2687", # Bloodrage
    "58567":  "7386", # Sunder Armor",
    "20253": "20252", # Intercept",
    "23885": "23881", # Bloodthirst
    "22858": "20230", # Retaliation
    
    "58381": "48156", # Mind Flay
    "53022": "53023", # Mind Sear
    
    "36032": "42897", # Arcane Blast",
    "42938": "42940", # Blizzard",
    
    "22482": "13877", # Blade Flurry",
    "57841": "51690", # Killing Spree",
    
    "34075": "34074", # Aspect of the Viper",
    "58433": "58434", # Volley",
    "49065": "49067", # Explosive Trap",
    
    "50590": "50589", # Immolation Aura",
    "47834": "47836", # Seed of Corruption",
    "47818": "47820", # Rain of Fire",
    "61291": "61290", # Shadowflame",
    "63321": "57946", # Life Tap",
    "31818": "57946", # Life Tap",
    
    "53195": "53201", # Starfall",
    "48466": "48467", # Hurricane",
    "53506": "24858", # Moonkin Form",
    
    "49088": "48707", # Anti-Magic Shell",
    "47632": "49895", # Death Coil",
    "52212": "49938", # Death and Decay",

    "33110": "48113", # Prayer of Mending",
    "64844": "64843", # Divine Hymn",
    "48076": "48078", # Holy Nova",

    "49279": "49281", # Lightning Shield",
    "61654": "61657", # Fire Nova",

    "53739": "53736", # Seal of Corruption",
    "20424": "20375", # Seal of Command",
    "67485": "62124", # Hand of Reckoning",
    "54158": "20271", # Judgement of Light",
    "20267": "20271", # Judgement of Light",
    "48821": "48825", # Holy Shock",

    "64442": "64440", # Blade Warding",
}

CUSTOM_SPELL_NAMES = {
    "42925": "Flamestrike (Rank 8)",
    "49240": "Lightning Bolt (Proc)",
    "49269": "Chain Lightning (Proc)",
    "53190": "Starfall (AoE)",
    "55360": "Living Bomb (DoT)",
    # Off Hand
    "66974": "Obliterate (Off Hand)",
    "66962": "Frost Strike (Off Hand)",
    "61895": "Blood-Caked Strike (Off Hand)",
    "66992": "Plague Strike (Off Hand)",
    "44949": "Whirlwind (Off Hand)",
    "52874": "Fan of Knives (Off Hand)",
    "57842": "Killing Spree (Off Hand)",
    "66217": "Rune Strike (Off Hand)",
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
    "42842": [3, "Frostbolt"],
    "47610": [3, "Frostfire Bolt"],
    "42873": [3, "Fire Blast"],
    "48827": [4, "Avenger's Shield"],
    "53654": [4, "Beacon of Light"],
    "48819": [4, "Consecration"],
    "642": [4, "Divine Shield"],
    "66922": [4, "Flash of Light"],
    "25898": [4, "Greater Blessing of Kings"],
    "48938": [4, "Greater Blessing of Wisdom"],
    "10308": [4, "Hammer of Justice"],
    "53595": [4, "Hammer of the Righteous"],
    "67485": [4, "Hand of Reckoning"],
    "48823": [4, "Holy Shock"],
    "20272": [4, "Illumination"],
    "58597": [4, "Sacred Shield"],
    "26017": [4, "Vindication"],
    "21084": [4, "Seal of Righteousness"],
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
        "34471": 1, # The Beast Within
        "53257": 1, # Cobra Strikes
        "57475": 1, # Kindred Spirits
        "75447": 1, # Ferocious Inspiration
        "53209": 2, # Chimera Shot
        "53301": 3, # Explosive Shot (Rank 1)
        "60051": 3, # Explosive Shot (Rank 2)
        "60052": 3, # Explosive Shot (Rank 3)
        "60053": 3, # Explosive Shot (Rank 4)
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
        "58757": 3, # Healing Stream Totem
    },
    "warlock": {
        "59161": 1, # Haunt (Rank 2)
        "59164": 1, # Haunt (Rank 4)
        "30405": 1, # Unstable Affliction (Rank 3)
        "47843": 1, # Unstable Affliction (Rank 5)
        "64368": 1, # Eradication (Rank 2)
        "64371": 1, # Eradication (Rank 3)

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
    "Arms": "ability_warrior_savageblow",
    "Fury": "ability_warrior_innerrage",
    "Protection": "ability_warrior_defensivestance"
  }
}

SPECS_LIST = [
    (sname or cname, icon)
    for cname, v in CLASSES.items()
    for sname, icon in v.items()
]

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

SERVERS = {
    "0x06": "Lordaeron",
    "0x07": "Icecrown",
    "0x0D": "Frostmourne3",
    "0x0C": "Frostmourne2",
    "0x0A": "Blackrock",
}

def get_ms(timestamp):
    if timestamp is None:
        return -1
    return int((perf_counter()-timestamp)*1000)

def get_ms_str(timestamp):
    return f"{get_ms(timestamp):>7,} ms"

def running_time(f):
    def running_time_inner(*args, **kwargs):
        timestamp = perf_counter()
        q = f(*args, **kwargs)
        msg = f"{get_ms_str(timestamp)} | {f.__module__}.{f.__name__}"
        LOGGER_REPORTS.debug(msg)
        return q
    
    return running_time_inner

def sort_dict_by_value(d: dict):
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=True))


def is_player(guid: str):
    return guid.startswith('0x0') and guid != NIL_GUID

def separate_thousands(num, precision=None):
    try:
        num + 0
    except TypeError:
        return ""
    
    if not num:
        return ""
    
    if precision is None:
        precision = 1 if isinstance(num, float) else 0
    
    return f"{num:,.{precision}f}".replace(',', ' ')


def get_now():
    return datetime.now()

def to_dt_closure(year=None):
    re_find_all = re.compile('(\d+)').findall
    CURRENT = get_now()
    CURRENT_SHIFT = CURRENT + T_DELTA["14H"]

    if year is None:
        year = CURRENT.year
        def inner(s: str):
            q = list(map(int, re_find_all(s[:18])))
            q[-1] *= 1000
            dt = datetime(year, *q)
            if dt > CURRENT_SHIFT:
                dt = dt.replace(year=year-1)
            return dt
    else:
        def inner(s: str):
            q = list(map(int, re_find_all(s[:18])))
            q[-1] *= 1000
            return datetime(year, *q)
        
    return inner

CURRENT_YEAR = get_now().year
RE_FIND_ALL = re.compile("(\d+)").findall
RE_FIND_ALL_BYTES = re.compile(b'(\d+)').findall

def to_dt_simple(s: str):
    return datetime(CURRENT_YEAR, *map(int, RE_FIND_ALL(s[:18])))

def to_dt_simple_precise(s: str):
    q = list(map(int, RE_FIND_ALL(s[:18])))
    q[-1] *= 1000
    return datetime(CURRENT_YEAR, *q)

def get_delta(current, previous):
    return to_dt_simple(current) - to_dt_simple(previous)

def get_delta_simple_precise(current, previous):
    return to_dt_simple_precise(current) - to_dt_simple_precise(previous)

def to_dt_year(s: str, year: int):
    return datetime(year, *map(int, RE_FIND_ALL(s[:18])))

def to_dt_year_precise(s: str, year: int):
    q = list(map(int, RE_FIND_ALL(s[:18])))
    q[-1] *= 1000
    return datetime(year, *q)

def to_dt_simple_bytes(s: bytes):
    return datetime(CURRENT_YEAR, *map(int, RE_FIND_ALL_BYTES(s[:18])))

def to_dt_year_bytes(s: bytes, year: int):
    return datetime(year, *map(int, RE_FIND_ALL_BYTES(s[:18])))

def to_dt_bytes_closure(year: int=None):
    if year is None:
        year = get_now().year

    def inner(s: str):
        return datetime(year, *map(int, RE_FIND_ALL_BYTES(s[:18])))
        
    return inner

def to_dt_bytes_year_fix(s, year: int=None):
    if year is None:
        year = get_now().year
    
    dt = datetime(year, *map(int, RE_FIND_ALL_BYTES(s[:18])))
    CURRENT_SHIFTED = get_now() + T_DELTA["14H"]
    if dt > CURRENT_SHIFTED:
        dt = dt.replace(year=year-1)
    return dt

def duration_to_string(t: float):
    milliseconds = t % 1 * 1000
    if milliseconds < 1:
        milliseconds = milliseconds * 1000
    
    t = int(t)
    hours = t // 3600
    minutes = t // 60 % 60
    seconds = t % 60
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0>3.0f}"


def get_report_name_info(report_id: str):
    _report_id = report_id.split('--')
    while len(_report_id) < len(REPORT_NAME_STRUCTURE):
        _report_id.append("")
    return dict(zip(REPORT_NAME_STRUCTURE, _report_id))

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
        return f.readline().strip(b"\x00").decode()

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
