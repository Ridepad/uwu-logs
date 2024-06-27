'''
Removes lines with SPELL_CAST_FAILED
Removes lines with SPELL_DURABILITY_DAMAGE
Removes " from spells and names
Removes unit flags
Replaces gap after timestamp with ','
Changes lines with these flags to spell formatting
    - SWING_DAMAGE
    - SWING_MISSED
    - ENVIRONMENTAL_DAMAGE
    - ENCHANT_APPLIED
    - ENCHANT_REMOVED

Before:
6/25 21:04:15.468  SPELL_CAST_FAILED,0x060000000040F817,"Nomadra",0x511,0x0000000000000000,nil,0x80000000,48461,"Wrath",0x8,"Not yet recovered"
6/25 21:04:14.319  SPELL_CAST_SUCCESS,0x060000000040F817,"Nomadra",0x511,0x0000000000000000,nil,0x80000000,24858,"Moonkin Form",0x1
6/25 21:46:32.302  SPELL_DAMAGE,0x060000000040F817,"Nomadra",0x511,0xF130008F130004E9,"Rotface",0x10a48,48465,"Starfire",0x40,15783,0,64,3945,0,0,1,nil,nil
6/25 21:05:30.116  SWING_DAMAGE,0xF13000908F00007F,"Deathbound Ward",0x10a48,0x060000000040F817,"Nomadra",0x511,11748,0,1,0,0,0,1,nil,nil
6/25 22:43:00.924  SWING_MISSED,0xF13000910C00065E,"Ymirjar Battle-Maiden",0xa48,0x060000000040F817,"Nomadra",0x511,MISS
6/25 22:52:55.576  ENVIRONMENTAL_DAMAGE,0x0000000000000000,nil,0x80000000,0x060000000040F817,"Nomadra",0x511,FALLING,5587,0,1,0,0,0,nil,nil,nil
3/1  21:02:55.660  ENCHANT_APPLIED,0x0600000000490A26,"Tipme",0x514,0x0600000000490A26,"Tipme",0x514,"Earthliving 6",50734,"Royal Scepter of Terenas II"

After:
timestamp           flag                  source guid           source name              target guid           target name  spell id    spell name        school/dmg/etc
6/25 21:04:14.319,  SPELL_CAST_SUCCESS,   0x060000000040F817,   Nomadra,                 0x0000000000000000,   nil,         24858,      Moonkin Form,     0x1
6/25 21:46:32.302,  SPELL_DAMAGE,         0x060000000040F817,   Nomadra,                 0xF130008F130004E9,   Rotface,     48465,      Starfire,         0x40,15783,0,64,3945,0,0,1,nil,nil
6/25 21:05:30.116,  SWING_DAMAGE,         0xF13000908F00007F,   Deathbound Ward,         0x060000000040F817,   Nomadra,         1,      Melee,            0x1,11748,0,1,0,0,0,1,nil,nil
6/25 22:43:00.924,  SWING_MISSED,         0xF13000910C00065E,   Ymirjar Battle-Maiden,   0x060000000040F817,   Nomadra,         1,      Melee,            0x1,MISS
6/25 22:52:55.576,  ENVIRONMENTAL_DAMAGE, 0x0000000000000000,   nil,                     0x000000000062341F,   Nomadra,     90001,      FALLING,          0x1,5587,0,1,0,0,0,nil,nil,nil
3/1  21:02:55.660,  ENCHANT_APPLIED,      0x0600000000490A26,   Tipme,                   0x0600000000490A26,   Tipme,       50734,      Earthliving 6,    Royal Scepter of Terenas II

Added tabs and column names to visualize - in the end all lines look like this:
6/25 21:46:32.302,SPELL_DAMAGE,0x060000000040F817,Nomadra,0xF130008F130004E9,Rotface,48465,Starfire,0x40,15783,0,64,3945,0,0,1,nil,nil
'''

from h_debug import Loggers

LOGGER_UNUSUAL_SPELLS = Loggers.unusual_spells

NEW_LINE = b'\n'
SWING_FLAGS = {
    b"SWING_DAMAGE",
    b"SWING_MISSED",
}
LOST_SWING = [b"1", b"Melee", b"0x1"]
SKIP_FLAGS = {
    b"SPELL_CAST_FAILED",
    b"SPELL_DURABILITY_DAMAGE",
}
ENVIRONMENTAL_DAMAGE = b"ENVIRONMENTAL_DAMAGE"
ENV_DAMAGE_TYPES = {
    b"FALLING":  b"90001",
    b"LAVA":     b"90002",
    b"DROWNING": b"90003",
    b"FIRE":     b"90004",
    b"FATIGUE":  b"90005",
    b"SLIME":    b"90006",
}
ENCHANTS_FLAGS = {
    b"ENCHANT_REMOVED",
    b"ENCHANT_APPLIED",
}

def _add_new_env(env_type: bytes, school_hex: str):
    spell_id_str = str(int(max(ENV_DAMAGE_TYPES.values())) + 1)
    dbg = " | ".join((
        f"{spell_id_str:>5}",
        f"{school_hex:5}",
        env_type.decode(),
    ))
    LOGGER_UNUSUAL_SPELLS.debug(f"MISSING ENVIRONMENTAL DAMAGE: {dbg}")
    
    ENV_DAMAGE_TYPES[env_type] = spell_id_str.encode()

def _fix_env(_line: list[bytes]):
    env_type, dmg, ok, school, etc = _line.pop(-1).split(b",", 4)
    school_hex_str = hex(int(school))
    
    if env_type not in ENV_DAMAGE_TYPES:
        _add_new_env(env_type, school_hex_str)

    spell_id = ENV_DAMAGE_TYPES[env_type]
    school_hex = school_hex_str.encode()
    _line.extend((spell_id, env_type, school_hex, dmg, ok, school, etc))

def _fix_ench(line: list[bytes]):
    name, id, etc = line.pop(-1).split(b',', 2)
    line.extend((id, name, etc))

# 3.6sec 1200mb ram
def normalize(logs_slice: list[bytes]):
    _join = b','.join
    for line in logs_slice:
        if line.count(b'/') > 1:
            continue
        line = line.replace(b'  ', b',', 1).replace(b'"', b'').replace(b', ', b' ')
        _line_s = line.split(b',', 8)
        if _line_s[1] in SKIP_FLAGS:
            continue
        
        del _line_s[7], _line_s[4]
        if _line_s[1] in SWING_FLAGS:
            _line_s[6:6] = LOST_SWING
        elif _line_s[1] in ENCHANTS_FLAGS:
            _fix_ench(_line_s)
        elif _line_s[1] == ENVIRONMENTAL_DAMAGE:
            _fix_env(_line_s)
            
        yield _join(_line_s).rstrip()
    yield b""

#3.75 sec 800mb ram
def normalize_read_from_file(path):
    with open(path, "rb") as f:
        for line in normalize(f):
            yield line

# 7.6sec 950mb ram
def normalize_replace(logs_slice: list[str]):
    _join = b','.join
    to_del = []
    for index, line in enumerate(logs_slice):
        if line.count(b'/') > 1:
            to_del.append(index)
            continue
        line = line.replace(b'  ', b',', 1).replace(b'"', b'').replace(b', ', b' ')
        _line_s = line.split(b',', 8)
        if _line_s[1] in SKIP_FLAGS:
            to_del.append(index)
            continue
        
        del _line_s[7], _line_s[4]
        if _line_s[1] in SWING_FLAGS:
            _line_s[6:6] = LOST_SWING
        elif _line_s[1] in ENCHANTS_FLAGS:
            _fix_ench(_line_s)
        elif _line_s[1] == ENVIRONMENTAL_DAMAGE:
            _fix_env(_line_s)
        
        logs_slice[index] = _join(_line_s).rstrip()

    for index in reversed(to_del):
        del logs_slice[index]
    
    logs_slice.append(b"")
    return logs_slice
