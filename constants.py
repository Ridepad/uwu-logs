
DEFAULT_SERVER_NAME = "Unknown"
LOGS_CUT_NAME = "LOGS_CUT.zstd"
LOGS_CUT_NAME_OLD = "LOGS_CUT.zlib"
TOP_FILE_NAME = "top.json"
PANDAS_COMPRESSION = "zstd"
NIL_GUID = '0x0000000000000000'
UNKNOWN_ICON = "inv_misc_questionmark"

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

SERVERS = {
    "0x06": "Lordaeron",
    "0x07": "Icecrown",
    "0x0D": "Frostmourne3",
    "0x0C": "Frostmourne2",
    "0x0A": "Blackrock",
    "0x0E": "Onyxia",
}

GEAR = {
    "LEFT": [     
        "head",
        "neck",
        "shoulder",
        "cloak",
        "chest",
        "shirt",
        "tabard",
        "wrist",
    ],
    "RIGHT": [
        "hands",
        "belt",
        "legs",
        "boots",
        "ring1",
        "ring2",
        "trinket1",
        "trinket2",
    ],
    "WEAPONS": [
        "main-hand",
        "off-hand",
        "backup",
    ],
}
