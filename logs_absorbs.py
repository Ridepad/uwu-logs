from collections import defaultdict

import logs_base
from constants import get_delta_simple_precise, running_time

# THIS IS A FUCKING DISASTER

DAEGIS = "47753"
VALANYR = "64413"
HEAL_FLAGS = {
    "SPELL_HEAL", "SPELL_PERIODIC_HEAL",
}
MISSED = {
    "DAMAGE_SHIELD_MISSED",
    "RANGE_MISSED",
    "SPELL_BUILDING_MISSED",
    "SPELL_MISSED",
    "SPELL_PERIODIC_MISSED",
    "SWING_MISSED"
}
AURA_FLAGS = {
    "SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_REMOVED",
    "SPELL_AURA_APPLIED_DOSE", "SPELL_AURA_REMOVED_DOSE",
}
ABS_FLAGS = {
    "SWING_DAMAGE",
    "RANGE_DAMAGE",
    "SPELL_DAMAGE",
    "SPELL_PERIODIC_DAMAGE",
    "DAMAGE_SHIELD",
    "ENVIRONMENTAL_DAMAGE",
    "SWING_MISSED",
    "RANGE_MISSED",
    "SPELL_MISSED",
    "SPELL_PERIODIC_MISSED",
    "DAMAGE_SHIELD_MISSED",
}

PRIEST_DIVINE_AEGIS = { # Divine Aegis
    "47509",
    "47511",
    "47515",
    DAEGIS,
    "54704"
}
MAGE_FROST_WARD = { # Frost Ward
    "6143",
    "8461",
    "8462",
    "10177",
    "28609",
    "32796",
    "43012"
}
MAGE_FIRE_WARD = { # Fire Ward
    "543",
    "8457",
    "8458",
    "10223",
    "10225",
    "27128",
    "43010"
}
MAGE_ICE_BARRIER = { # Ice Barrier
    "11426",
    "13031",
    "13032",
    "13033",
    "27134",
    "33405",
    "43038",
    "43039"
}
WARLOCK_SHADOW_WARD = { # Shadow Ward
    "6229",
    "11739",
    "11740",
    "28610",
    "47890",
    "47891"
}
WARLOCK_SACRIFICE = { # Sacrifice
    "7812",
    "19438",
    "19440",
    "19441",
    "19442",
    "19443",
    "27273",
    "47985",
    "47986"
}

ABS_ORDER = [
    "6940",
    "25228",
    "64205",
    # VALANYR, # Protection of Ancient Kings
    "48707", # Anti-Magic Shell
    "65686",
    "65684",
    *MAGE_FROST_WARD,
    *MAGE_FIRE_WARD,
    *WARLOCK_SHADOW_WARD,
    "58597",
    "28527",
    *PRIEST_DIVINE_AEGIS,
    *MAGE_ICE_BARRIER,
    *WARLOCK_SACRIFICE,
    # "48066",
    "43020",
    # "48707", # Anti-Magic Shell
    "52286",
    "66233",
    "71586",
]


IGNORED_MAX_VALUES = {
    "6940",
    "25228",
    "48707",
    # "48066",
    DAEGIS,
    "64205",
}

IGNORED_MAX_VALUES2 = {
    "48707",
}

IDKSHIELDS = {
    DAEGIS, # Divine Aegis
    VALANYR, # Protection of Ancient Kings
    "58597", # Sacred Shield
    "48066", # Power Word
    "47891", # Shadow Ward
}

DMG_SPLIT = {
    "6940",
    "25228",
    "64205",
}

APPLY_ON_DMG = {
    "58597", # Sacred Shield
}

VALANYR_IGNORED = {
    "52000", # Earthliving
}

ABSORB_SPELLS = {
    "48707": {"school": 0x20, "dur": 5}, # Anti-Magic Shell (rank 1)
    "51052": {"school": 0x20, "dur": 10}, # Anti-Magic Zone( (rank 1)
    "52286": {"school": 0x01, "dur": 86400}, # Will of the Necropolis
    "49497": {"school": 0x01, "dur": 86400}, # Spell Deflection
    "62606": {"school": 0x08, "dur": 10, "avg": 1600, "cap": 2500}, # Savage Defense
    "11426": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 1)
    "13031": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 2)
    "13032": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 3)
    "13033": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 4)
    "27134": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 5)
    "33405": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 6)
    "43038": {"school": 0x10, "dur": 60}, # Ice Barrier (rank 7)
    "43039": {"school": 0x10, "dur": 60, "avg": 6500, "cap": 8300}, # Ice Barrier (rank 8)
    "6143": {"school": 0x10, "dur": 30}, # Frost Ward (rank 1)
    "8461": {"school": 0x10, "dur": 30}, # Frost Ward (rank 2)
    "8462": {"school": 0x10, "dur": 30}, # Frost Ward (rank 3)
    "10177": {"school": 0x10, "dur": 30}, # Frost Ward (rank 4)
    "28609": {"school": 0x10, "dur": 30}, # Frost Ward (rank 5)
    "32796": {"school": 0x10, "dur": 30}, # Frost Ward (rank 6)
    "43012": {"school": 0x10, "dur": 30, "avg": 5200, "cap": 7000}, # Frost Ward (rank 7)
    "1463": {"school": 0x40, "dur": 60}, # Mana shield (rank 1)
    "8494": {"school": 0x40, "dur": 60}, # Mana shield (rank 2)
    "8495": {"school": 0x40, "dur": 60}, # Mana shield (rank 3)
    "10191": {"school": 0x40, "dur": 60}, # Mana shield (rank 4)
    "10192": {"school": 0x40, "dur": 60}, # Mana shield (rank 5)
    "10193": {"school": 0x40, "dur": 60}, # Mana shield (rank 6)
    "27131": {"school": 0x40, "dur": 60}, # Mana shield (rank 7)
    "43019": {"school": 0x40, "dur": 60}, # Mana shield (rank 8)
    "43020": {"school": 0x40, "dur": 60, "avg": 4500, "cap": 6300}, # Mana shield (rank 9)
    "543": {"school": 0x04, "dur": 30}, # Fire Ward (rank 1)
    "8457": {"school": 0x04, "dur": 30}, # Fire Ward (rank 2)
    "8458": {"school": 0x04, "dur": 30}, # Fire Ward (rank 3)
    "10223": {"school": 0x04, "dur": 30}, # Fire Ward (rank 4)
    "10225": {"school": 0x04, "dur": 30}, # Fire Ward (rank 5)
    "27128": {"school": 0x04, "dur": 30}, # Fire Ward (rank 6)
    "43010": {"school": 0x04, "dur": 30, "avg": 5200, "cap": 7000}, # Fire Ward (rank 7)
    "58597": {"school": 0x02, "dur": 6, "avg": 2800, "cap": 5500}, # Sacred Shield
    "66233": {"school": 0x02, "dur": 86400}, # Ardent Defender
    "31230": {"school": 0x01, "dur": 86400}, # Cheat Death
    "17": {"school": 0x02, "dur": 30}, # Power Word: Shield (rank 1)
    "592": {"school": 0x02, "dur": 30}, # Power Word: Shield (rank 2)
    "600": {"school": 0x02, "dur": 30}, # Power Word: Shield (rank 3)
    "3747": {"school": 0x02, "dur": 30}, # Power Word: Shield (rank 4)
    "6065": {"school": 0x02, "dur": 30}, # Power Word: Shield (rank 5)
    "6066": {"school": 0x02, "dur": 30}, # Power Word: Shield (rank 6)
    "10898": {"school": 0x02, "dur": 30, "avg": 721, "cap": 848}, # Power Word: Shield (rank 7)
    "10899": {"school": 0x02, "dur": 30, "avg": 898, "cap": 1057}, # Power Word: Shield (rank 8)
    "10900": {"school": 0x02, "dur": 30, "avg": 1543, "cap": 1816}, # Power Word: Shield (rank 9)
    "10901": {"school": 0x02, "dur": 30, "avg": 3643, "cap": 4288}, # Power Word: Shield (rank 10)
    "25217": {"school": 0x02, "dur": 30, "avg": 5436, "cap": 6398}, # Power Word: Shield (rank 11)
    "25218": {"school": 0x02, "dur": 30, "avg": 7175, "cap": 8444}, # Power Word: Shield (rank 12)
    "48065": {"school": 0x02, "dur": 30, "avg": 9596, "cap": 11293}, # Power Word: Shield (rank 13)
    "48066": {"school": 0x02, "dur": 30, "avg": 10000, "cap": 11769}, # Power Word: Shield (rank 14)
    "47509": {"school": 0x02, "dur": 12}, # Divine Aegis (rank 1)
    "47511": {"school": 0x02, "dur": 12}, # Divine Aegis (rank 2)
    "47515": {"school": 0x02, "dur": 12}, # Divine Aegis (rank 3)
    DAEGIS: {"school": 0x02, "dur": 12, "cap": 10000}, # Divine Aegis (rank 1)
    "54704": {"school": 0x02, "dur": 12, "cap": 10000}, # Divine Aegis (rank 1)
    "47788": {"school": 0x02, "dur": 10}, # Guardian Spirit
    "7812": {"school": 0x20, "dur": 30, "cap": 305}, # Sacrifice (rank 1)
    "19438": {"school": 0x20, "dur": 30, "cap": 510}, # Sacrifice (rank 2)
    "19440": {"school": 0x20, "dur": 30, "cap": 770}, # Sacrifice (rank 3)
    "19441": {"school": 0x20, "dur": 30, "cap": 1095}, # Sacrifice (rank 4)
    "19442": {"school": 0x20, "dur": 30, "cap": 1470}, # Sacrifice (rank 5)
    "19443": {"school": 0x20, "dur": 30, "cap": 1905}, # Sacrifice (rank 6)
    "27273": {"school": 0x20, "dur": 30, "cap": 2855}, # Sacrifice (rank 7)
    "47985": {"school": 0x20, "dur": 30, "cap": 6750}, # Sacrifice (rank 8)
    "47986": {"school": 0x20, "dur": 30, "cap": 8350}, # Sacrifice (rank 9)
    "6229": {"school": 0x20, "dur": 30, "cap": 290}, # Shadow Ward (rank 1)
    "11739": {"school": 0x20, "dur": 30, "cap": 470}, # Shadow Ward (rank 2)
    "11740": {"school": 0x20, "dur": 30, "avg": 675}, # Shadow Ward (rank 3)
    "28610": {"school": 0x20, "dur": 30, "avg": 875}, # Shadow Ward (rank 4)
    "47890": {"school": 0x20, "dur": 30, "avg": 2750}, # Shadow Ward (rank 5)
    "47891": {"school": 0x20, "dur": 30, "avg": 5300, "cap": 8300}, # Shadow Ward (rank 6)
    "25228": {"school": 0x20, "dur": 86400}, # Soul Link
    "29674": {"school": 0x40, "dur": 86400, "cap": 1000}, # Lesser Ward of Shielding
    "29719": {"school": 0x40, "dur": 86400, "cap": 4000}, # Greater Ward of Shielding
    "29701": {"school": 0x40, "dur": 86400, "cap": 4000}, # Greater Shielding
    "28538": {"school": 0x02, "dur": 120, "avg": 3400, "cap": 4000}, # Major Holy Protection Potion
    "28537": {"school": 0x20, "dur": 120, "avg": 3400, "cap": 4000}, # Major Shadow Protection Potion
    "28536": {"school": 0x04, "dur": 120, "avg": 3400, "cap": 4000}, # Major Arcane Protection Potion
    "28513": {"school": 0x08, "dur": 120, "avg": 3400, "cap": 4000}, # Major Nature Protection Potion
    "28512": {"school": 0x10, "dur": 120, "avg": 3400, "cap": 4000}, # Major Frost Protection Potion
    "28511": {"school": 0x04, "dur": 120, "avg": 3400, "cap": 4000}, # Major Fire Protection Potion
    "7233": {"school": 0x04, "dur": 120, "avg": 1300, "cap": 1625}, # Fire Protection Potion
    "7239": {"school": 0x10, "dur": 120, "avg": 1800, "cap": 2250}, # Frost Protection Potion
    "7242": {"school": 0x20, "dur": 120, "avg": 1800, "cap": 2250}, # Shadow Protection Potion
    "7245": {"school": 0x02, "dur": 120, "avg": 1800, "cap": 2250}, # Holy Protection Potion
    "7254": {"school": 0x08, "dur": 120, "avg": 1800, "cap": 2250}, # Nature Protection Potion
    "53915": {"school": 0x20, "dur": 120, "avg": 5100, "cap": 6000}, # Mighty Shadow Protection Potion
    "53914": {"school": 0x08, "dur": 120, "avg": 5100, "cap": 6000}, # Mighty Nature Protection Potion
    "53913": {"school": 0x10, "dur": 120, "avg": 5100, "cap": 6000}, # Mighty Frost Protection Potion
    "53911": {"school": 0x04, "dur": 120, "avg": 5100, "cap": 6000}, # Mighty Fire Protection Potion
    "53910": {"school": 0x04, "dur": 120, "avg": 5100, "cap": 6000}, # Mighty Arcane Protection Potion
    "17548": {"school": 0x20, "dur": 120, "avg": 2600, "cap": 3250}, # Greater Shadow Protection Potion
    "17546": {"school": 0x08, "dur": 120, "avg": 2600, "cap": 3250}, # Greater Nature Protection Potion
    "17545": {"school": 0x02, "dur": 120, "avg": 2600, "cap": 3250}, # Greater Holy Protection Potion
    "17544": {"school": 0x10, "dur": 120, "avg": 2600, "cap": 3250}, # Greater Frost Protection Potion
    "17543": {"school": 0x04, "dur": 120, "avg": 2600, "cap": 3250}, # Greater Fire Protection Potion
    "17549": {"school": 0x04, "dur": 120, "avg": 2600, "cap": 3250}, # Greater Arcane Protection Potion
    "28527": {"school": 0x02, "dur": 15, "avg": 1000, "cap": 1250}, # Fel Blossom
    "29432": {"school": 0x04, "dur": 3600, "avg": 2000, "cap": 2500}, # Frozen Rune (Fire Protection)
    "36481": {"school": 0x40, "dur": 4, "cap": 100000}, # Arcane Barrier (TK Kael'Thas) Shield
    "17252": {"school": 0x01, "dur": 1800, "cap": 500}, # Mark of the Dragon Lord (LBRS epic ring)
    "25750": {"school": 0x02, "dur": 15, "avg": 151, "cap": 302}, # Defiler's Talisman/Talisman of Arathor
    "25747": {"school": 0x02, "dur": 15, "avg": 344, "cap": 378}, # Defiler's Talisman/Talisman of Arathor
    "25746": {"school": 0x02, "dur": 15, "avg": 435, "cap": 478}, # Defiler's Talisman/Talisman of Arathor
    "23991": {"school": 0x02, "dur": 15, "avg": 550, "cap": 605}, # Defiler's Talisman/Talisman of Arathor
    "30997": {"school": 0x04, "dur": 300, "avg": 1800, "cap": 2700}, # Pendant of Frozen Flame (Fire Absorption)
    "31002": {"school": 0x40, "dur": 300, "avg": 1800, "cap": 2700}, # Pendant of the Null Rune (Arcane Absorption)
    "30999": {"school": 0x08, "dur": 300, "avg": 1800, "cap": 2700}, # Pendant of Withering (Nature Absorption)
    "30994": {"school": 0x10, "dur": 300, "avg": 1800, "cap": 2700}, # Pendant of Thawing (Frost Absorption)
    "31000": {"school": 0x40, "dur": 300, "avg": 1800, "cap": 2700}, # Pendant of Shadow's End (Shadow Absorption)
    "23506": {"school": 0x02, "dur": 20, "avg": 1000, "cap": 1250}, # Arena Grand Master (Aura of Protection)
    "12561": {"school": 0x04, "dur": 60, "avg": 400, "cap": 500}, # Goblin Construction Helmet (Fire Protection)
    "31771": {"school": 0x02, "dur": 20, "cap": 440}, # Runed Fungalcap (Shell of Deterrence)
    "21956": {"school": 0x02, "dur": 10, "cap": 500}, # Mark of Resolution (Physical Protection)
    "29506": {"school": 0x02, "dur": 20, "cap": 900}, # The Burrower's Shell
    "4057": {"school": 0x04, "dur": 60, "cap": 500}, # Flame Deflector (Fire Resistance)
    "4077": {"school": 0x10, "dur": 60, "cap": 600}, # Ice Deflector (Frost Resistance)
    "39228": {"school": 0x02, "dur": 20, "cap": 1150}, # Argussian Compass
    "27779": {"school": 0x02, "dur": 30, "cap": 350}, # Divine Protection (Priest dungeon set 1/2)
    "11657": {"school": 0x01, "dur": 20, "avg": 70, "cap": 85}, # Jang'thraze
    "10368": {"school": 0x02, "dur": 15, "cap": 200}, # Uther's Light Effect
    "37515": {"school": 0x02, "dur": 15, "cap": 200}, # Blade Turning
    "42137": {"school": 0x01, "dur": 86400, "cap": 400}, # Greater Rune of Warding
    "26467": {"school": 0x01, "dur": 30, "cap": 1000}, # Scarab Brooch (Persistent Shield)
    "26470": {"school": 0x08, "dur": 8, "cap": 1000}, # Persistent Shield
    "27539": {"school": 0x01, "dur": 6, "avg": 300, "cap": 500}, # Thick Obsidian Breatplate (Obsidian Armor)
    "28810": {"school": 0x02, "dur": 30, "cap": 500}, # Faith Set Proc (Armor of Faith)
    "55019": {"school": 0x01, "dur": 12, "cap": 1100}, # Sonic Shield
    VALANYR: {"school": 0x08, "dur": 8, "cap": 20000}, # Protection of Ancient Kings (Val'anyr, Hammer of Ancient Kings)
    "40322": {"school": 0x10, "dur": 30, "avg": 12000, "cap": 12600}, # Teron's Vengeful Spirit Ghost - Spirit Shield
    "71586": {"school": 0x02, "dur": 10, "cap": 6400}, # Hardened Skin (Corroded Skeleton Key)
    "60218": {"school": 0x02, "dur": 10, "avg": 140, "cap": 4000}, # Essence of Gossamer
    "57350": {"school": 0x01, "dur": 6, "cap": 1500}, # Illusionary Barrier (Darkmoon Card: Illusion)
    "70845": {"school": 0x01, "dur": 10, "cap": 16000}, # Stoicism
    "65874": {"school": 0x20, "dur": 15, "cap": 175000}, # Twin Val'kyr's: Shield of Darkness
    "67257": {"school": 0x20, "dur": 15, "cap": 300000}, # Twin Val'kyr's: Shield of Darkness
    "67256": {"school": 0x20, "dur": 15, "cap": 700000}, # Twin Val'kyr's: Shield of Darkness
    "67258": {"school": 0x20, "dur": 15, "cap": 1200000}, # Twin Val'kyr's: Shield of Darkness
    "65858": {"school": 0x04, "dur": 15, "cap": 175000}, # Twin Val'kyr's: Shield of Lights
    "67260": {"school": 0x04, "dur": 15, "cap": 300000}, # Twin Val'kyr's: Shield of Lights
    "67259": {"school": 0x04, "dur": 15, "cap": 700000}, # Twin Val'kyr's: Shield of Lights
    "67261": {"school": 0x04, "dur": 15, "cap": 1200000}, # Twin Val'kyr's: Shield of Lights
    "65686": {"school": 0x01, "dur": 86400, "cap": 1000000}, # Twin Val'kyr: Light Essence
    "65684": {"school": 0x01, "dur": 86400, "cap": 1000000}, # Twin Val'kyr: Dark Essence
}

# passive shields that are applied by default.
PASSIVE_SHIELDS = {
    "31230", # Cheat Death
    "49497", # Spell Deflection
    "52286", # Will of the Necropolis
    "66233", # Ardent Defender
}

WTFKEK = {
    "70940",
    "70654",
}

SHILD_IDS = set(ABSORB_SPELLS) | set(PRIEST_DIVINE_AEGIS)
SHILD_IDS |= set(MAGE_FROST_WARD) | set(MAGE_FIRE_WARD) | set(MAGE_ICE_BARRIER)
SHILD_IDS |= set(WARLOCK_SHADOW_WARD) | set(WARLOCK_SACRIFICE)

@running_time
def parse_absorb_related(logs: list[str], discos: set[str]=None):
    if discos is None:
        discos = set()
    valanyrs = set()
    events = defaultdict(list)
    for line in logs:
        try:
            timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, *etc = line.split(',')
            if flag == "DAMAGE_SPLIT":
                if spell_id == "25228":
                    events[source_guid].append((timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, etc[1], 0, 0, etc[0]))
                else:
                    events[source_guid].append((timestamp, flag, target_guid, target_name, source_guid, source_name, spell_id, spell_name, etc[1], 0, 0, etc[0]))
            elif flag in HEAL_FLAGS:
                if source_guid in valanyrs:
                    if spell_id not in VALANYR_IGNORED:
                        events[target_guid].append((timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, etc[1], 0, 0, 0))
                elif source_guid in discos and etc[-1] == "1":
                    events[target_guid].append((timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, etc[1], 0, 0, 0))
            elif spell_id == "64411":
                valanyrs.add(target_guid)
                if flag == "SPELL_AURA_REMOVED":
                    valanyrs.remove(target_guid)
            elif spell_id in SHILD_IDS:
                if flag == "SPELL_CAST_SUCCESS":
                    continue
                events[target_guid].append((timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, 0, 0, 0, 0))
            else:
                try:
                    if flag in MISSED:
                        if etc[-2] == "ABSORB":
                            events[target_guid].append((timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, etc[-1], etc[-2], 0, etc[0]))
                    elif etc[6] != "0":
                        events[target_guid].append((timestamp, flag, source_guid, source_name, target_guid, target_name, spell_id, spell_name, etc[6], etc[1], etc[4], etc[0]))
                except IndexError:
                    continue
        except ValueError:
            continue

    return events

def get_delta_simple_precise_wrap(c, last=None):
    if last is None:
        return -1
    return get_delta_simple_precise(c, last).total_seconds()

def getabsorderindex(spid, offset=0):
    try:
        return ABS_ORDER.index(spid)
    except ValueError:
        return 1000+offset
    
def to_int(v):
    try:
        return int(v)
    except ValueError:
        return 0
    
def prettyprint(msg, absrb, src, spell):
    print(f'{msg:15} | {absrb:6} | {src:12} | {spell}')
    
def prettyprint2(msg, d, current_shield_id, spell, other=None):
    print(f'{msg:15} | {d:>5.2f}s | {current_shield_id:>6} | {spell} | {other}')

def new_shield(id, sGUID, sName):
    return {
        "sGUID": sGUID,
        "sName": sName,
        "remain": 0,
    } | ABSORB_SPELLS.get(id, {})


SPELLS_NAMES = {
    DAEGIS: "Divine Aegis",
    VALANYR: "Protection of Ancient Kings",
}

def proccess_absorb(lines, discos, is_bdk=False):
    CURRENT_SHIELDS = {}
    CURRENT_MAX_SHIELD = {}
    ABSORBS = defaultdict(lambda: defaultdict(int))
    ABSORBS_DETAILS = []
    for ts, flag, sGUID, sName, tGUID, tName, _id, spell_name, _ABSORB, _DAMAGE, res, sch in lines:
        _ABSORB = to_int(_ABSORB)
        _DAMAGE = to_int(_DAMAGE)
        # res = int(res)
        SPELLS_NAMES[_id] = spell_name
        _line = f"{ts:18} | {flag:21} | {sGUID} | {sName:30} | {tGUID} | {tName:30} | {_id:>5} | {spell_name:30}"
        if _ABSORB and _ABSORB != "0":
            _line = f"{_line} | {_ABSORB:>6} | {_DAMAGE:>6} | {res:>6} | {sch:>6}"
        if _ABSORB:
            ABSORBS_DETAILS.append((ts, flag, sName, spell_name, _ABSORB, _DAMAGE+_ABSORB))
        else:
            ABSORBS_DETAILS.append((ts, flag, sName, spell_name, "", ""))
        # print(_line)
            
        if flag == "DAMAGE_SPLIT":
            if _id in DMG_SPLIT:
                CURRENT_SHIELDS[_id] = {
                    "sGUID": sGUID,
                    "sName": sName,
                    "remain": _ABSORB,
                    "ts": ts,
                    "transient": True,
                }
        elif flag in HEAL_FLAGS:
            if sGUID in discos:
                __shield = CURRENT_SHIELDS.get(DAEGIS)
                if not __shield or __shield.get("transient"):
                    __shield = CURRENT_SHIELDS[DAEGIS] = new_shield(_id, sGUID, sName)
                __shield["ts"] = ts
                __shield["remain"] = min(10000, __shield.get("remain", 0) + int(_ABSORB *.3))
            else:
                __shield = CURRENT_SHIELDS.get(VALANYR)
                if not __shield or __shield.get("transient"):
                    __shield = CURRENT_SHIELDS[VALANYR] = new_shield(_id, sGUID, sName)
                __shield["ts"] = ts
                __shield["remain"] = min(20000, __shield.get("remain", 0) + int(_ABSORB *.15))

        elif flag in AURA_FLAGS:
            __shield = CURRENT_SHIELDS.get(_id)
            if not __shield or __shield.get("transient") or get_delta_simple_precise_wrap(ts, __shield.get("tsrem")) > 0.5:
                __shield = new_shield(_id, sGUID, sName)
                if _id in CURRENT_MAX_SHIELD:
                    __shield["cap"] = CURRENT_MAX_SHIELD[_id]
                
            if flag == "SPELL_AURA_REMOVED":
                __shield["transient"] = True
                __shield["tsrem"] = ts
            else:
                __shield["ts"] = ts
            
            CURRENT_SHIELDS[_id] = __shield
            
        elif flag in ABS_FLAGS:
            
            # sort shields by prio  
            shields_list = list(CURRENT_SHIELDS)
            # print([getabsorderindex(x, shields_list.index(x)) for x in CURRENT_SHIELDS])
            CURRENT_SHIELD_IDS = sorted(CURRENT_SHIELDS, key=lambda x: getabsorderindex(x, shields_list.index(x)))
            if VALANYR in CURRENT_SHIELDS:
                if CURRENT_SHIELDS[VALANYR].get("transient"):
                    CURRENT_SHIELD_IDS.insert(0, CURRENT_SHIELD_IDS.pop(CURRENT_SHIELD_IDS.index(VALANYR)))

                # print(shields_list)
                # print(CURRENT_SHIELD_IDS)
            # for current_shield_id, shieild_ts in sorted(shields.items(), key=getabsorderindex):
            _filtered_shit = {
                s_id: CURRENT_SHIELDS[s_id]
                for s_id in CURRENT_SHIELD_IDS
                if s_id not in IGNORED_MAX_VALUES
            }
            # print(_filtered_shit.keys())
            
            if is_bdk:
                _max_cap = sum(
                    CURRENT_SHIELDS[x].get("remain") or CURRENT_MAX_SHIELD.get(x) or CURRENT_SHIELDS[x].get("cap") or 0
                    for x in CURRENT_SHIELD_IDS
                )
                _max_avg = sum(
                    CURRENT_SHIELDS[x].get("remain") or CURRENT_SHIELDS[x].get("avg") or 0
                    for x in CURRENT_SHIELD_IDS
                )
                if _max_cap < _ABSORB:
                    ratio = _ABSORB / (_ABSORB + _DAMAGE) * 100
                    # print("0"*100, "WTF", ratio)
                    if int(45 - ratio) == 0:
                        if flag != "SWING_DAMAGE":
                            ABSORBS[tGUID]["49497"] += _ABSORB
                            ABSORBS_DETAILS.append((ts, "ADDED_sd1", tName, "Spell Deflection", _ABSORB, ""))
                            _ABSORB = 0
                            # prettyprint("++++??sd1 ADDED", _ABSORB, "Spell Deflection", tName)
                    elif int(15 - ratio) == 0:
                        ABSORBS[tGUID]["52286"] += _ABSORB
                        ABSORBS_DETAILS.append((ts, "ADDED_wn1", tName, "Will of the Necropolis", _ABSORB, ""))
                        _ABSORB = 0
                        # prettyprint("++++??wn0 ADDED", _ABSORB, "Will of the Necropolis", tName)
                    elif ratio > 45:
                        _rem_abs = _ABSORB - (_ABSORB + _DAMAGE) * .45 - _DAMAGE * 3
                        # print(CURRENT_SHIELDS)
                        # print(_max_cap)
                        # print(_max_avg)
                        # print(_rem_abs)
                        if "48707" in CURRENT_SHIELDS:
                            if _max_cap and _rem_abs > _max_cap - 15 :
                                _abs = int((_ABSORB + _DAMAGE) * .15)
                                _ABSORB = _ABSORB - _abs
                                ABSORBS[tGUID]["52286"] += _abs
                                ABSORBS_DETAILS.append((ts, "ADDED_wn2", tName, "Will of the Necropolis", _abs, ""))
                                # prettyprint("++++??wn2 ADDED", _abs, "Will of the Necropolis", tName)
                            elif _rem_abs > _max_avg - 15:
                                _abs = int((_ABSORB + _DAMAGE) * .45)
                                _ABSORB = _ABSORB - _abs
                                ABSORBS[tGUID]["49497"] += _abs
                                ABSORBS_DETAILS.append((ts, "ADDED_sd2", tName, "Spell Deflection", _abs, ""))
                                # prettyprint("++++??sd2 ADDED", _abs, "Spell Deflection", tName)
                            elif abs(_DAMAGE * 3 - _ABSORB) > 10:
                                _abs = int((_ABSORB + _DAMAGE) * .15)
                                _ABSORB = _ABSORB - _abs
                                ABSORBS[tGUID]["52286"] += _abs
                                ABSORBS_DETAILS.append((ts, "ADDED_wn3", tName, "Will of the Necropolis", _abs, ""))
                                # prettyprint("++++??wn3 ADDED", _abs, "Will of the Necropolis", tName)
                            # elif _rem_abs < 0:
                            # else:
                            #     _abs = int((_ABSORB + _DAMAGE) * .15)
                            #     # prettyprint("++++??wn4 ADDED", _abs, "Will of the Necropolis", tName)
                            #     _ABSORB = _ABSORB - _abs
                            
                        elif flag != "SWING_DAMAGE" and _ABSORB > _max_cap + 500:
                            _rem_abs = int((_ABSORB + _DAMAGE) * .45)
                            _ABSORB = _ABSORB - _rem_abs
                            ABSORBS[tGUID]["49497"] += _rem_abs
                            ABSORBS_DETAILS.append((ts, "ADDED_sd3", tName, "Spell Deflection", _rem_abs, ""))
                            # prettyprint("++++??sd3 ADDED", _abs, "Spell Deflection", tName)
                    elif ratio > 15 and _ABSORB > _max_cap + 500:
                        _rem_abs = int((_ABSORB + _DAMAGE) * .15)
                        _ABSORB = _ABSORB - _rem_abs
                        ABSORBS[tGUID]["52286"] += _rem_abs
                        ABSORBS_DETAILS.append((ts, "ADDED_wnx4", tName, "Will of the Necropolis", _rem_abs, ""))
                        # prettyprint("++++??wn1 ADDED", _abs, "Will of the Necropolis", tName)

            for current_shield_id in CURRENT_SHIELD_IDS:
                CURR_SHIELD = CURRENT_SHIELDS[current_shield_id]
                transient = CURR_SHIELD.get("transient")
                if transient:
                    d = get_delta_simple_precise_wrap(ts, CURR_SHIELD.get("tsrem"))
                    del CURRENT_SHIELDS[current_shield_id]
                    # prettyprint2("------- REMOVED", d, SPELLS_NAMES[current_shield_id], current_shield_id, CURR_SHIELD)
                    if d > 0.5:
                        if current_shield_id in _filtered_shit:
                            del _filtered_shit[current_shield_id]
                        # prettyprint2("------1 IGNORED", d, SPELLS_NAMES[current_shield_id], current_shield_id, CURR_SHIELD)
                        continue

                if current_shield_id in APPLY_ON_DMG and ts == CURR_SHIELD.get("ts"):
                    d = get_delta_simple_precise_wrap(ts, CURR_SHIELD.get("ts"))
                    # prettyprint2("------2 IGNORED", d, SPELLS_NAMES[current_shield_id], current_shield_id, CURR_SHIELD)
                    continue
                    
                d = get_delta_simple_precise_wrap(ts, CURR_SHIELD.get("ts"))
                # prettyprint2("======== SHIELD", d, SPELLS_NAMES[current_shield_id], current_shield_id, CURR_SHIELD)
                if current_shield_id == "48707": # Anti-Magic Shell
                    if sch != "0x1":
                        # print(CURRENT_SHIELDS)
                        _abs = _DAMAGE * 3
                        if len(CURRENT_SHIELDS) < 2:
                            _abs = _ABSORB
                            _ABSORB = 0
                        else:
                            _ABSORB = _ABSORB - _abs
                        # prettyprint("+++++++++ ADDED", _abs, SPELLS_NAMES[current_shield_id], CURR_SHIELD["sName"])
                        ABSORBS[CURR_SHIELD["sGUID"]]["48707"] += _abs
                        ABSORBS_DETAILS.append((ts, "ADDED", CURR_SHIELD["sName"], SPELLS_NAMES[current_shield_id], _abs, ""))
                
                elif current_shield_id in DMG_SPLIT:
                    _abs = CURR_SHIELD["remain"]
                    _ABSORB = _ABSORB - _abs
                    # prettyprint("+++++++++ ADDED", _abs, SPELLS_NAMES[current_shield_id], CURR_SHIELD["sName"])
                    ABSORBS[CURR_SHIELD["sGUID"]][current_shield_id] += _abs
                    ABSORBS_DETAILS.append((ts, "ADDED", CURR_SHIELD["sName"], SPELLS_NAMES[current_shield_id], _abs, ""))

                elif current_shield_id in IDKSHIELDS:
                    if current_shield_id == DAEGIS and "ts" in CURR_SHIELD:
                        d = get_delta_simple_precise_wrap(ts, CURR_SHIELD["ts"])
                        if 0 < d < 0.1 and CURRENT_SHIELDS:
                            # prettyprint2("------3 IGNORED", d, SPELLS_NAMES[current_shield_id], current_shield_id)
                            continue
                        
                    currv = CURR_SHIELD.get("remain") or CURRENT_MAX_SHIELD.get(current_shield_id)
                    if not currv:
                        if len(CURRENT_SHIELDS) == 1 or current_shield_id == CURRENT_SHIELD_IDS[-1]:
                            currv = CURR_SHIELD.get("cap")
                        if not currv:
                            currv = CURR_SHIELD.get("avg") or CURR_SHIELD.get("cap") or 0
                        
                    if currv > _ABSORB:
                        _abs = _ABSORB
                        CURR_SHIELD["remain"] = currv - _ABSORB
                        _ABSORB = 0
                            # if transient:
                            #     _cur = CURRENT_MAX_SHIELD.get(current_shield_id, 0)
                            #     _max_default = ABSORB_SPELLS.get(current_shield_id, {}).get("avg", 0)
                            #     if _cur:
                            #         CURRENT_MAX_SHIELD[current_shield_id] = max(_cur, abs(_cur - CURR_SHIELD["remain"]))
                            #     else:
                            #         CURRENT_MAX_SHIELD[current_shield_id] = abs(_max_default - CURR_SHIELD["remain"])
                            #     # prettyprint("......2 NEW MAX", CURRENT_MAX_SHIELD[current_shield_id], CURR_SHIELD["sName"], SPELLS_NAMES[current_shield_id])
                    else:
                        _abs = currv
                        CURR_SHIELD["remain"] = 0
                        _ABSORB = _ABSORB - currv
                    # prettyprint("+++++++++ ADDED", _abs, SPELLS_NAMES[current_shield_id], CURR_SHIELD["sName"])
                    ABSORBS[CURR_SHIELD["sGUID"]][current_shield_id] += _abs
                    ABSORBS_DETAILS.append((ts, "ADDED", CURR_SHIELD["sName"], SPELLS_NAMES[current_shield_id], _abs, ""))
                else:
                    pass
                    # prettyprint("++++++??? ADDED", _ABSORB, SPELLS_NAMES[current_shield_id], CURR_SHIELD["sName"])
                # prettyprint2("======== SHIELD", d, SPELLS_NAMES[current_shield_id], current_shield_id, CURR_SHIELD)

                # if _ABSORB > 0 and current_shield_id not in IGNORED_MAX_VALUES:
                #     _LAST_SHIELD = CURR_SHIELD
                #     _LAST_SHIELD_ID = current_shield_id
            
            if _ABSORB < 1:
                continue
            # print(_filtered_shit.keys())
            try:
                _LAST_SHIELD_ID, _LAST_SHIELD = _filtered_shit.popitem()
                # _LAST_SHIELD_ID = _filtered_shit[-1]
                # _LAST_SHIELD = CURRENT_SHIELDS[_LAST_SHIELD_ID]
                # print("LAST SHIELD:", CURRENT_SHIELD_IDS[-1])
            except Exception:
                _LAST_SHIELD_ID = None
                _LAST_SHIELD = None
            # print("LAST SHIELD", _LAST_SHIELD)
            if _LAST_SHIELD is None:
                continue
            # prettyprint(">>>>>>>> REMAIN", _ABSORB, _LAST_SHIELD["sName"], SPELLS_NAMES[_LAST_SHIELD_ID])
            ABSORBS_DETAILS.append((ts, "REMAIN", "nil", str(_filtered_shit), _ABSORB, ""))
            if _LAST_SHIELD_ID in IGNORED_MAX_VALUES2:
                continue
            
            ABSORBS[_LAST_SHIELD["sGUID"]][_LAST_SHIELD_ID] += _ABSORB
            if _LAST_SHIELD_ID in CURRENT_MAX_SHIELD:
                CURRENT_MAX_SHIELD[_LAST_SHIELD_ID] += _ABSORB
            else:
                _max_default = ABSORB_SPELLS.get(_LAST_SHIELD_ID, {}).get("avg", 0)
                CURRENT_MAX_SHIELD[_LAST_SHIELD_ID] = _max_default + _ABSORB
            # prettyprint("....... NEW MAX", CURRENT_MAX_SHIELD[_LAST_SHIELD_ID], CURR_SHIELD["sName"], SPELLS_NAMES[_LAST_SHIELD_ID])
    return ABSORBS, ABSORBS_DETAILS


class Absorbs(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def _get_absorbs(self, s, f):
        if not s or not f:
            return {}, {}

        logs_slice = self.LOGS[s:f]
        specs = self.get_players_specs_in_segments(s, f)
        discos = {guid for guid, spec in specs.items() if spec == 21}
        events = parse_absorb_related(logs_slice, discos=discos)
        ABSORBS: dict[str, dict[str, dict[str, int]]] = {}
        DETAILS = {}
        
        for target, lines in events.items():
            _absorbs, _details = proccess_absorb(lines, discos, specs.get(target) == 1)
            ABSORBS[target] = _absorbs
            DETAILS[target] = _details

        return ABSORBS, DETAILS
    
    def get_absorbs(self, s, f):
        return self._get_absorbs(s, f)[0]
    
    def get_absorbs_details(self, s, f):
        return self._get_absorbs(s, f)[1]
    
    def get_absorbs_details_wrap(self, segments: list, target: str):
        if not target.startswith("0x0"):
            target = self.name_to_guid(target)

        if not target:
            return []
        
        DETAILS = []
        for s, f in segments:
            _a = self.get_absorbs_details(s, f)
            if target in _a:
                DETAILS.extend(self.get_absorbs_details(s, f)[target])
        return DETAILS

    def get_absorbs_by_source(self, s, f):
        _abs = defaultdict(int)
        _data = self.get_absorbs(s, f)
        for target, sources in _data.items():
            for source, spells in sources.items():
                for spell_id, value in spells.items():
                    _abs[source] += value
        return _abs
    
    def get_absorbs_by_source_spells_wrap(self, segments: list, source_filter: str, target_filter: str=None):
        ABSORBS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for s, f in segments:
            _data = self.get_absorbs(s, f)
            for _target, sources in _data.items():
                for _source, spells in sources.items():
                    for spell_id, value in spells.items():
                        ABSORBS[_source]["Total"][spell_id] += value
                        ABSORBS[_source][_target][spell_id] += value
        
        if not target_filter:
            target_filter = "Total"
        return ABSORBS[source_filter][target_filter]
    
    def get_absorbs_by_target_wrap(self, segments, target_filter, source_filter=None):
        _abs = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for s, f in segments:
            _data = self.get_absorbs(s, f)
            for _target, sources in _data.items():
                for _source, spells in sources.items():
                    # print(_source, spells)
                    for spell_id, value in spells.items():
                        # _abs[source][spell_id] += value
                        _abs[_target]["Total"][spell_id] += value
                        _abs[_target][_source][spell_id] += value
        if not source_filter:
            source_filter = "Total"
        return _abs[target_filter][source_filter]


def _test():
    report = Absorbs("23-07-10--16-00--Praystation--Lordaeron")
    encdata = report.get_enc_data()
    players = report.get_players_guids()
    # s, f = encdata["Deathbringer Saurfang"][-1]
    s, f = encdata["The Lich King"][-2]
    specs = report.get_players_specs_in_segments(s, f)
    # print(specs["0x060000000061945A"])
    # return
    # x = report.find_index(s, 15)
    # beforepull15sec = report.LOGS[x:s]

    # FIRST_LINE = report.LOGS[s].split(",", 1)[0]
    discos = {guid for guid, spec in specs.items() if spec == 21}
    # discos = {"0x060000000061945A", }
    events = parse_absorb_related(report.LOGS[s:f], discos=discos)


    ABSORBS = defaultdict(lambda: defaultdict(int))
    ABSORBS2 = {}
    ABSORBS_DETAILS = {}
    z = report.name_to_guid("Deadrockk")
    for target, lines in events.items():
        if target != z:
            continue
        is_bdk = specs.get(target) == 1
        print()
        print(target)
        # continue
        sources = {players[sguid] for _, flag, sguid, *_ in lines if sguid in players and flag in AURA_FLAGS}
        print(len(sources), sources)
        print(lines[0])
        # continue
        _absorbs, _details = proccess_absorb(lines, discos, is_bdk)
        ABSORBS2[target] = _absorbs
        ABSORBS_DETAILS[target] = _details
        # print(_absorbs)
        for source, spells in _absorbs.items():
            for spell_id, value in spells.items():
                ABSORBS[source][spell_id] += value

    print(ABSORBS)
    return ABSORBS2, ABSORBS_DETAILS


if __name__ == "__main__":
    _test()
