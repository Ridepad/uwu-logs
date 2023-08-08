from collections import defaultdict
from typing import TypedDict

HIT_TYPE = ["spells_hit", "spells_crit", "dot_hit", "dot_crit"]
PERIODIC = {'SPELL_PERIODIC_DAMAGE', 'SPELL_PERIODIC_HEAL'}
FLAGS_FILTER_DAMAGE = {
    "SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE",
    "SPELL_MISSED",
    "SWING_DAMAGE", "SWING_MISSED",
    "RANGE_DAMAGE", "RANGE_MISSED",
    "SPELL_CAST_SUCCESS",
    "SPELL_CAST_START",
    "DAMAGE_SHIELD", "DAMAGE_SHIELD_MISSED",
}
FLAGS_FILTER_HEAL = {
    "SPELL_HEAL", "SPELL_PERIODIC_HEAL",
    "SPELL_CAST_SUCCESS",
    "SPELL_CAST_START",
}
FLAGS_DAMAGE = {
    "SPELL_DAMAGE",
    "SWING_DAMAGE",
    "RANGE_DAMAGE",
    "DAMAGE_SHIELD",
    "SPELL_PERIODIC_DAMAGE",
}
FLAG_MISS = {
    "SWING_MISSED",
    "RANGE_MISSED",
    "SPELL_MISSED",
    "DAMAGE_SHIELD_MISSED",
}
FLAGS_HEAL = {
    "SPELL_HEAL",
    "SPELL_PERIODIC_HEAL",
}
FLAGS_CAST = {
    "SPELL_CAST_SUCCESS",
    "SPELL_CAST_START",
}
HIT_TYPE_DICT = {
    "SPELL_PERIODIC_DAMAGE": "PERIODIC",
    "SPELL_DAMAGE": "HIT",
    "SPELL_PERIODIC_HEAL": "PERIODIC",
    "SPELL_HEAL": "HIT",
    "SPELL_DAMAGE": "HIT",
    "SWING_DAMAGE": "HIT",
    "DAMAGE_SHIELD": "HIT",
    "RANGE_DAMAGE": "HIT",
}


class BreakdownType(TypedDict):
    OTHER: defaultdict[str, defaultdict[str, defaultdict[str, defaultdict[str, int]]]]
    DAMAGE: defaultdict[str, defaultdict[str, defaultdict[str, defaultdict[str, list[int]]]]]

class BreakdownTypeExtended(BreakdownType):
    SPELLS: dict[str, dict[str, str]]
    TARGETS: set[str]


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
    
def get_avgs(hits: list):
    if not hits:
        return "", []

    hits = sorted(hits)
    _len = len(hits)
    len10 = _len//10 or 1
    len50 = _len//2 or 1
    avgs = [
        sum(hits) // _len,
        max(hits),
        sum(hits[-len10:]) // len10,
        sum(hits[-len50:]) // len50,
        sum(hits[:len50]) // len50,
        sum(hits[:len10]) // len10,
        min(hits),
    ]
    avg, *other = map(separate_thousands, avgs)
    return avg, other

def format_percent(hit, crit):
    if crit == 0:
        return ""
    percent = crit/(hit+crit)*100
    percent = separate_thousands(percent)
    return f"{percent}%"

def format_hits_data(hits, crits):
    hits_count = len(hits)
    crits_count = len(crits)
    percent = format_percent(hits_count, crits_count)
    hit_avg, hits_avg = get_avgs(hits)
    crit_avg, crits_avg = get_avgs(crits)
    return {
        "total": separate_thousands(hits_count+crits_count),
        "hits": separate_thousands(hits_count),
        "crits": separate_thousands(crits_count),
        "percent": percent,
        "hit_avg": hit_avg,
        "hits_avg": hits_avg,
        "crit_avg": crit_avg,
        "crits_avg": crits_avg,
    }

def format_hits(hits: dict[str, list[int]]):
    hit_hit, hit_crt, dot_hit, dot_crt = [hits.get(x, []) for x in HIT_TYPE]
    return {
        "HIT": format_hits_data(hit_hit, hit_crt),
        "DOT": format_hits_data(dot_hit, dot_crt),
    }

def hits_data(data: dict[int, dict[str, list[int]]]):
    return {spell_id: format_hits(hits) for spell_id, hits in data.items()}


def given(logs_slice: list[str], controlled_units: set[str], heal=False) -> BreakdownType:
    '''{'sGUID': {'tGUID': {'spell_id': {'type': 0}}}}'''
    if heal:
        flags_filter = FLAGS_FILTER_HEAL
    else:
        flags_filter = FLAGS_FILTER_DAMAGE

    other = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    damage = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    
    for line in logs_slice:
        _, flag, sGUID, etc1 = line.split(',', 3)
        if sGUID not in controlled_units:
            continue
        if flag not in flags_filter:
            continue
        
        _, tGUID, _, spell_id, etc2 = etc1.split(',', 4)
        if flag in FLAGS_CAST:
            type = "CAST"
        elif flag in FLAGS_DAMAGE:
            type = HIT_TYPE_DICT[flag]
            _, _, dmg, over, _, res, _, absrb, crit, glanc, _ = etc2.split(',', 10)
                
            _value = int(dmg)
            
            _spell = other[tGUID][sGUID][spell_id]
            if absrb != "0":
                _spell["ABSORBED"] += int(absrb)
            if res != "0":
                _spell["RESISTED"] += int(res)
            if glanc == "1":
                _spell["GLANCING"] += int(_value/3)
            if over != 0:
                over = int(over)
                _value = _value - over
                _spell["OVERKILL"] += over
            
            _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
            damage[tGUID][sGUID][spell_id][HIT_TYPE[_hit_type]].append(_value)
        elif flag in FLAGS_HEAL:
            type = HIT_TYPE_DICT[flag]
            _, _, dmg, over, _, crit = etc2.split(',')
        
            _value = int(dmg)
            if over != "0":
                over = int(over)
                _value = _value - over
                other[tGUID][sGUID][spell_id]["OVERHEAL"] += over
            
            _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
            damage[tGUID][sGUID][spell_id][HIT_TYPE[_hit_type]].append(_value)
        else:
            __miss = etc2.split(',')
            try:
                v = int(__miss[-1])
                type = __miss[-2]
                other[tGUID][sGUID][spell_id][f"{type}ED"] += v
            except ValueError:
                type = __miss[-1]

        other[tGUID][sGUID][spell_id][type] += 1

    return {
        "OTHER": other,
        "DAMAGE": damage,
    }

def taken(logs_slice: list[str], target_guid: str, heal=False) -> BreakdownType:
    '''{'sGUID': {'tGUID': {'spell_id': {'type': 0}}}}'''

    if heal:
        flags_filter = FLAGS_FILTER_HEAL
    else:
        flags_filter = FLAGS_FILTER_DAMAGE

    other = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    damage = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    
    for line in logs_slice:
        _, flag, etc1 = line.split(',', 2)
        if flag not in flags_filter:
            continue
        
        sGUID, _, tGUID, _, spell_id, etc2 = etc1.split(',', 5)
        if target_guid not in tGUID:
            continue
        if flag in FLAGS_CAST:
            type = "CAST"
        elif flag in FLAGS_DAMAGE:
            type = HIT_TYPE_DICT[flag]
            _, _, dmg, over, _, res, _, absrb, crit, glanc, _ = etc2.split(',', 10)
                
            _value = int(dmg)
            
            _spell = other[sGUID][tGUID][spell_id]
            if absrb != "0":
                _spell["ABSORBED"] += int(absrb)
            if res != "0":
                _spell["RESISTED"] += int(res)
            if glanc == "1":
                _spell["GLANCING"] += int(_value/3)
            if over != 0:
                over = int(over)
                _value = _value - over
                _spell["OVERKILL"] += over
            
            _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
            damage[sGUID][tGUID][spell_id][HIT_TYPE[_hit_type]].append(_value)
        elif flag in FLAGS_HEAL:
            type = HIT_TYPE_DICT[flag]
            _, _, dmg, over, _, crit = etc2.split(',')
        
            _value = int(dmg)
            if over != "0":
                over = int(over)
                _value = _value - over
                other[sGUID][tGUID][spell_id]["OVERHEAL"] += over
            
            _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
            damage[sGUID][tGUID][spell_id][HIT_TYPE[_hit_type]].append(_value)
        else:
            __miss = etc2.split(',')
            try:
                v = int(__miss[-1])
                type = __miss[-2]
                other[sGUID][tGUID][spell_id][f"{type}ED"] += v
            except ValueError:
                type = __miss[-1]

        other[sGUID][tGUID][spell_id][type] += 1

    return {
        "OTHER": other,
        "DAMAGE": damage,
    }
