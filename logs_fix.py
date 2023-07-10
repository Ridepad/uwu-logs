import os

from constants import ENV_DAMAGE, LOGGER_UNUSUAL_SPELLS, running_time

SWING_FLAGS = {b"SWING_DAMAGE", b"SWING_MISSED"}
LOST_SWING = [b"1", b"Melee", b"0x1"]
CAST_FAILED = b"SPELL_CAST_FAILED"
ENVIRONMENTAL_DAMAGE = b"ENVIRONMENTAL_DAMAGE"

NULL = b'\x00'
JUMP_NULL = NULL * 1024 * 2 ** 6
JUMP_LEN = len(JUMP_NULL)

def env_f(_line: bytes):
    line = _line.decode().split(',', 12)
    del line[7], line[4]

    spell_name = line[6]
    school_hex = hex(int(line[9]))
    if spell_name in ENV_DAMAGE:
        spell_id = ENV_DAMAGE[spell_name]
    else:
        spell_id = str(int(max(ENV_DAMAGE.values())) + 1)
        ENV_DAMAGE[spell_id] = spell_name
        LOGGER_UNUSUAL_SPELLS.debug(f"MISSING ENVIRONMENTAL DAMAGE: {spell_id:>5} | {school_hex:<5} | {spell_name}")
        
    line[6:7] = [spell_id, spell_name, school_hex]
    return [x.encode() for x in line]

def trim_logs(fname: str):
    new_logs = []
    _l_a = new_logs.append
    _join = b','.join

    with open(fname, 'rb') as f:
        for _line in f:
            if _line.count(b'/') > 1:
                continue
            try:
                _line = _line.replace(b'  ', b',', 1).replace(b'"', b'').replace(b', ', b' ')
                line = _line.split(b',', 8)
                if line[1] == CAST_FAILED:
                    continue
                if line[1] == ENVIRONMENTAL_DAMAGE:
                    line = env_f(_line)
                else:
                    del line[7], line[4]
                    if line[1] in SWING_FLAGS:
                        line[6:6] = LOST_SWING

                _l_a(_join(line).rstrip())

            except IndexError:
                pass
    
    return new_logs


@running_time
def has_null_bug(fname: str):
    with open(fname, "rb") as f:
        current = f.read(JUMP_LEN)
        while current:
            if current == JUMP_NULL:
                return True
            current = f.read(JUMP_LEN)
    return False

@running_time
def remove_null(fname: str):
    noext = fname.rsplit('.', 1)[0]
    temp_file = f"{noext}.tmp"
    
    with open(fname, "rb") as file_input:
        previous = b""
        current = file_input.read(JUMP_LEN)
        with open(temp_file, "wb") as file_output:
            while current:
                if current == JUMP_NULL:
                    previous = previous.replace(NULL, b"")
                    file_output.write(previous)
                    while current == JUMP_NULL:
                        current = file_input.read(JUMP_LEN)
                    
                    previous = current.replace(NULL, b"")
                    current = file_input.read(JUMP_LEN)
                    continue
                
                file_output.write(previous)
                previous = current
                current = file_input.read(JUMP_LEN)
            
            file_output.write(previous)
    
    if os.path.isfile(fname):
        os.remove(fname)
    os.rename(temp_file, fname)
    return None

def check_null_bug(fname):
    if has_null_bug(fname):
        remove_null(fname)
