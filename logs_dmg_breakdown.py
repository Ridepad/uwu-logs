from collections import defaultdict

HIT_TYPE = ["spells_hit", "spells_crit", "dot_hit", "dot_crit"]
PERIODIC = {'SPELL_PERIODIC_DAMAGE', 'SPELL_PERIODIC_HEAL'}
AURA_APPLIED = {"SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH"}

def group_targets(targets: set[str]):
    target_ids = {guid[:-6] for guid in targets}
    return {
        target_id: {guid for guid in targets if target_id in guid}
        for target_id in target_ids
    }

def parse_logs(logs_slice: list[str], player_GUID: str, controlled_units: set[str], filter_guids=None, target_filter=None):
    '''absolute = { spell_id: sum }
    useful = { spell_id: {
        "spells_hit": [],
        "spells_crit": [],
        "dot_hit": [],
        "dot_crit": [] } }'''
    targets = set()

    overkill = defaultdict(int)
    reduced = defaultdict(int)
    actual: defaultdict[int, defaultdict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for line in logs_slice:
        if "DAMAGE" not in line:
            continue
        try:
            _, flag, sGUID, _, tGUID, _, sp_id, _, _, dmg, over, _, res, _, absrb, crit, glanc, _ = line.split(',', 17)
        except ValueError:
            # DAMAGE_SHIELD_MISSED
            continue
        if flag == "DAMAGE_SPLIT":
            continue
        if sGUID not in controlled_units:
            continue

        targets.add(tGUID)

        if target_filter:
            if target_filter not in tGUID:
                continue
        elif tGUID in filter_guids:
            continue
        
        dmg_raw = int(dmg)
        spell_id = int(sp_id) if sGUID == player_GUID else -int(sp_id)
        over = int(over)
        dmg_actual = dmg_raw - over
        overkill[spell_id] += over
        _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
        actual[spell_id][HIT_TYPE[_hit_type]].append(dmg_actual)
        
        if over != "0":
            reduced[spell_id] += int(over)
        if res != "0":
            reduced[spell_id] += int(res)
        if glanc == "1":
            reduced[spell_id] += int(dmg_raw/3)
        
    return {
        "targets": targets,
        "actual": actual,
        "overkill": overkill,
        "reduced": reduced,
    }

def casts(logs_slice: list[str], player_GUID: str, controlled_units: set[str], filter_guids=None, target_filter=None):
    spells = defaultdict(int)
    for line in logs_slice:
        if "_SUCCESS" not in line:
            continue

        try:
            _, flag, sGUID, _, tGUID, _, sp_id, _ = line.split(',', 7)
        except ValueError:
            continue

        if sGUID not in controlled_units:
            continue

        if target_filter:
            if target_filter not in tGUID:
                continue
        elif tGUID in filter_guids:
            continue

        spell_id = int(sp_id) if sGUID == player_GUID else -int(sp_id)
        spells[spell_id] += 1
    
    return spells

def misses(logs_slice: list[str], player_GUID: str, controlled_units: set[str], filter_guids=None, target_filter=None):
    spells = defaultdict(int)
    for line in logs_slice:
        if player_GUID not in line:
            continue
        if "_MISSED" not in line:
            continue

        try:
            _, flag, sGUID, _, tGUID, _, sp_id, _ = line.split(',', 7)
        except ValueError:
            continue

        if flag == "SPELL_PERIODIC_MISSED":
            continue

        if sGUID not in controlled_units:
            continue

        if target_filter:
            if target_filter not in tGUID:
                continue
        elif tGUID in filter_guids:
            continue

        spell_id = int(sp_id) if sGUID == player_GUID else -int(sp_id)
        spells[spell_id] += 1
    
    return spells

def auras(logs_slice: list[str], player_GUID: str, controlled_units: set[str], filter_guids=None, target_filter=None):
    spells = defaultdict(int)
    for line in logs_slice:
        if "_AURA_" not in line:
            continue

        try:
            _, flag, sGUID, _, tGUID, _, sp_id, _ = line.split(',', 7)
        except ValueError:
            continue

        if flag not in AURA_APPLIED:
            continue

        if sGUID not in controlled_units:
            continue

        if target_filter:
            if target_filter not in tGUID:
                continue
        elif tGUID in filter_guids:
            continue

        spell_id = int(sp_id) if sGUID == player_GUID else -int(sp_id)
        spells[spell_id] += 1
    
    return spells

def rounder(num):
    if not num:
        return ""
    v = f"{num:,}" if type(num) == int else f"{num:,.1f}"
    return v.replace(",", " ")

def get_avgs(hits: list):
    if not hits:
        return []
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
    return list(map(rounder, avgs))

def format_percent(hit, crit):
    if crit == 0:
        return ""
    percent = crit/(hit+crit)*100
    percent = rounder(percent)
    return f"{percent}%"

def format_hits_data(hits, crits):
    hits_count = len(hits)
    crits_count = len(crits)
    percent = format_percent(hits_count, crits_count)
    hits_avg = get_avgs(hits)
    crits_avg = get_avgs(crits)
    hits_count = rounder(hits_count)
    crits_count = rounder(crits_count)
    return ((hits_count, hits_avg), (crits_count, crits_avg)), percent

def format_hits(hits: dict[str, list[int]]):
    hit_hit, hit_crt, dot_hit, dot_crt = [hits.get(x, []) for x in HIT_TYPE]
    return format_hits_data(hit_hit, hit_crt), format_hits_data(dot_hit, dot_crt)

def hits_data(data: dict[int, dict[str, list[int]]]):
    return {spell_id: format_hits(hits) for spell_id, hits in data.items()}
