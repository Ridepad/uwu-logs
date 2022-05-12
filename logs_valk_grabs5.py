import constants

PLAYERS = {
    "0x06000000004544FD": "Jengo",
    "0x060000000001D680": "Arcanestorm",
    "0x06000000003CDC89": "Dezu",
    "0x060000000002CCBC": "Zahazku",
    "0x0600000000455A74": "Padgodx",
    "0x060000000030C2B6": "Chaooxx",
    "0x060000000004B154": "Grubby",
    "0x06000000003E84B8": "Starblaze",
    "0x0600000000070912": "Riujin",
    "0x060000000024F806": "Zpevak",
    "0x06000000003C4B9A": "Melomaniac",
    "0x060000000040C6F9": "Briyana",
}


def get_valks_summon_time(logs_slice: list[str]):
    valks = {}
    for n, line in enumerate(logs_slice):
        if '_SUMMON' in line and ",0xF150008F01" in line:
            timestamp, _, _, _, tguid, _ = line.split(',', 5)
            valks[tguid] = n
    return valks

def life_syph(logs: list[str]):
    valks = {}
    for n, line in enumerate(logs):
        if 'Life Siphon' not in line:
            continue
        _, flag, sguid, _, tguid, *a = line.split(',')
        if sguid not in valks:
            valks[sguid] = n
        # print(flag, sguid, tguid, a)
    return valks

# SPELL_AURA_APPLIED 0xF130008EF50001C0 0xF130008EF50001C0 74272 Remorseless Winter
# SPELL_AURA_REMOVED 0xF130008EF50001C0 0xF130008EF50001C0 ['The Lich King', '74272', 'Remorseless Winter', '0x10', 'BUFF']
# SPELL_CAST_START 0xF130008EF50001C0 0x0000000000000000 ['nil', '72262', 'Quake', '0x1']
def winter(logs: list[str]):
    for n, line in enumerate(logs):
        if '0xF130008EF5' not in line:
            continue
        _, flag, sguid, _, tguid, _, spellID, spellName, *_ = line.split(',')
        if '0xF130008EF5' not in sguid:
            continue
        if 'SPELL_AURA' not in flag:
            continue
        if spellName != "Remorseless Winter":
            continue
        return n

FLAGS = ['SPELL_DAMAGE', 'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_MISSED']
def mages(logs: list[str]):
    z = {}
    for line in logs:
        if '0xF130008EF5' not in line:
            continue
        _, flag, sguid, sname, tguid, _, spellID, spellName, *_ = line.split(',')
        if flag in FLAGS and sguid in PLAYERS:
            z[sguid] = z.get(sguid, 0) + 1
            # print(f"{flag:<20} | {sname:<12} | {spellID:>5} | {spellName}")
    return z
# 73784', 'Life Siphon

def main():
    LOGS_DIR = "LogsDir/22-03-05--20-56--Nomadra"
    LOGS_DIR = "LogsDir/22-03-12--21-04--Nomadra"
    path = f"{LOGS_DIR}/LOGS_CUT"
    logs_raw = constants.zlib_text_read(path)
    logs = constants.logs_splitlines(logs_raw)
    ts = constants.json_read(f"{LOGS_DIR}/ENCOUNTER_DATA")
    lk = ts['The Lich King']

    GRABS = {}
    for s,f in lk:
        print()
        _slice = logs[s:f]
        _slice_len = len(_slice)
        valks_syph = life_syph(_slice)
        valks_syph_items = list(valks_syph.items())
        f2 = max(valks_syph.values(), default=_slice_len)
        print(valks_syph)
        _winter = winter(_slice[f2:])
        print(_winter)

        valks = get_valks_summon_time(_slice)
        print(valks)
        valks_items = list(valks.items())
        print(valks_items)

        for x in range(0, len(valks_items), 3):
            s1 = valks_items[x][1]
            f1 = min((q[1] for q in valks_syph_items[x:x+3]), default=_slice_len)
            print(s1, f1)
            # s1, f1 = 45402, 49121
            _slice_wave = logs[s1:f1-500]
            wave_after = mages(_slice_wave)
            wave_before = mages(logs[s1-2000:s1])
            print(sorted(wave_after.items()))
            print(sorted(wave_before.items()))
            print(set(wave_before) - set(wave_after))
        # break
    # for s,f in 
    # print(ts)

main()