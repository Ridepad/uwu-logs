from collections import defaultdict

# 1/19 19:45:07.755,SPELL_DAMAGE,0xF13000954E00020A,Vengeful Shade,0x06000000005D571D,Sana,72012,Vengeful Blast,0x30,14156,11970,48,6066,0,0,nil,nil,nil
# 1/19 19:44:53.770,SWING_MISSED,0xF13000954E000205,Vengeful Shade,0x060000000048D30F,Tayoka,1,Melee,0x1,PARRY
# 1/19 19:44:45.628,SWING_DAMAGE,0xF13000954E000203,Vengeful Shade,0x060000000031E4BD,Ubal,1,Melee,0x1,385,385,1,0,0,0,nil,nil,nil
# 10/14 00:58:25.231,SPELL_AURA_APPLIED,0xF13000954E000336,Vengeful Shade,0x060000000042C8A5,Smashandash,1604,Dazed,0x1,DEBUFF
# 1/19 19:50:30.060,SPELL_MISSED,0xF13000954E000281,Vengeful Shade,0x060000000058EEA6,Nerd,72012,Vengeful Blast,0x30,IMMUNE

KEY_LADY_POPED_BY = "by"
KEY_LADY_DAMAGE = "damage"
KEY_LADY_PREVENTED = "prevented"
KEY_LADY_TARGETS = "targets"
SPIRIT_EXPLOSION_IDS = {
    "71544", # 10N
    "72010", # 25N
    "72011", # 10H
    "72012", # 25H
}

def format_data(combined_dict: dict[str, dict], source_guid):
    _poped_by = combined_dict[KEY_LADY_POPED_BY].get(source_guid)
    targets = sorted(combined_dict[KEY_LADY_TARGETS][source_guid])
    if not _poped_by:
        _poped_by = "nil"
        if len(targets) == 1:
            _poped_by = targets[0]
    
    return {
        KEY_LADY_DAMAGE: combined_dict[KEY_LADY_DAMAGE][source_guid],
        KEY_LADY_PREVENTED: combined_dict[KEY_LADY_PREVENTED][source_guid],
        KEY_LADY_POPED_BY: _poped_by,
        KEY_LADY_TARGETS: targets,
    }

def filter_spirits(logs_slice: list[str]):
    damage_done = defaultdict(int)
    damage_targets = defaultdict(set)
    damage_prevented = defaultdict(int)
    poped_by = {}
    for line in logs_slice:
        if "00954E" not in line:
            continue
        
        _, flag, source_guid, other = line.split(",", 3)
        if source_guid[6:-6] != "00954E":
            continue
        
        _, target_guid, _, spell_id, _, _, *dmg = other.split(',')
        
        if spell_id not in SPIRIT_EXPLOSION_IDS:
            poped_by[source_guid] = target_guid
            continue
        
        if not target_guid.startswith("0x0"):
            continue
      
        damage_targets[source_guid].add(target_guid)
      
        if "_DAMAGE" in flag:
            damage_done[source_guid] += int(dmg[0])
            damage_prevented[source_guid] += int(dmg[3])
            damage_prevented[source_guid] += int(dmg[5])
            continue
        try:
            damage_prevented[source_guid] += int(dmg[1])
        except IndexError:
            pass

    combined_dict = {
        KEY_LADY_DAMAGE: damage_done,
        KEY_LADY_PREVENTED: damage_prevented,
        KEY_LADY_POPED_BY: poped_by,
        KEY_LADY_TARGETS: damage_targets,
    }
    
    return [
        format_data(combined_dict, source_guid)
        for source_guid in damage_targets
    ]


def test1():
    import logs_main
    report = logs_main.THE_LOGS("23-10-14--00-23--Kikusumo--Lordaeron")
    encdata = report.get_enc_data()
    report.LOGS
    players = report.get_players_guids()
    for s, f in encdata["Lady Deathwhisper"]:
        print()
        logs_slice = report.LOGS[s:f]
        q = filter_spirits(logs_slice)
        for x in q:
            guid = x['by']
            name = players.get(guid, guid)
            print(f"{name:12} | {len(x['targets']):>2} | {x['damage']:>9_} |  {x['prevented']:>9_}")


if __name__ == "__main__":
    test1()
