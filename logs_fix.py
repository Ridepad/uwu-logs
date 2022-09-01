from constants import ENV_DAMAGE, LOGGER_UNUSUAL_SPELLS

SWING_FLAGS = {b"SWING_DAMAGE", b"SWING_MISSED"}
LOST_SWING = [b"1", b"Melee", b"0x1"]
CAST_FAILED = b"SPELL_CAST_FAILED"
ENVIRONMENTAL_DAMAGE = b"ENVIRONMENTAL_DAMAGE"

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

def trim_logs(fname):
    new_logs = []
    _l_a = new_logs.append
    _join = b','.join

    with open(fname, 'rb') as f:
        for _line in f:
            if _line.count(b'/') > 1:
                continue
            try:
                _line = _line.replace(b'  ', b',', 1).replace(b'"', b'').replace(b'\x00', b'').replace(b', ', b' ')
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


def __test1():
    import zlib
    from time import perf_counter
    from constants import get_ms_str, bytes_write

    fname = r"F:\Python\uwulogs\uploads\test3\WoWCombatLog.txt"
    for _ in range(2):
        pc = perf_counter()
        logs = trim_logs(fname)
        print(get_ms_str(pc))
    logs = b'\n'.join(logs)
    print(get_ms_str(pc))
    _len = len(logs)
    print(_len)
    assert _len == 272824032
    # logs = zlib.compress(logs, level=7)
    # print(f'{get_ms(pc)} ms')
    # bytes_write(r"F:\Python\uwulogs\uploads\test3\cut1.zlib", logs)
    # print(f'{get_ms(pc)} ms')

if __name__ == '__main__':
    __test1()
