import json

def get_logs(name):
    with open(LOGS_NAME_SLICE, 'r') as f:
        logs = f.read()
    logs = logs.replace('"', '')
    for line in logs.splitlines():
        yield line.split('  ')
# 4/30 22:56:07.414  SPELL_AURA_APPLIED      0x06000000001217CE          Pov ['58597', 'Sacred Shield', '0x2', 'BUFF']
# 4/30 22:56:07.416  SPELL_HEAL              0x06000000001217CE          Pov ['53654', 'Beacon of Light', '0x2', '22655', '0', '0', 'nil']
# 4/30 22:56:08.590  SPELL_PERIODIC_MISSED   0xF130008FF5000B81   Sindragosa ['70106', 'Chilled to the Bone', '0x10', 'ABSORB', '892']
# 4/30 22:56:09.191  SPELL_AURA_REMOVED      0x06000000001217CE          Pov ['58597', 'Sacred Shield', '0x2', 'BUFF']
# 4/30 22:56:09.191  SWING_DAMAGE            0xF130008FF5000B81   Sindragosa ['32303', '3010', '1', '0', '0', '3785', 'nil', 'nil', 'nil']

# 4/30 23:00:04.090  SPELL_PERIODIC_HEAL     0x06000000002E04FB        Morja ['61301', 'Riptide', '0x8', '1352', '932', '0', 'nil']
# 4/30 23:00:04.090  SPELL_AURA_APPLIED      0x06000000002E04FB        Morja ['64413', 'Protection of Ancient Kings', '0x8', 'BUFF']
# 4/30 23:00:04.174  SWING_MISSED            0xF130008FF5000B81   Sindragosa ['PARRY']
# 4/30 23:00:04.301  DAMAGE_SHIELD_MISSED    0x06000000004C3CEB     Shoggoth ['70106', 'Chilled to the Bone', '0x10', 'RESIST', '0']
# 4/30 23:00:04.301  SPELL_PERIODIC_HEAL     0x0600000000230080    Arthemiis ['20267', 'Judgement of Light', '0x2', '1304', '1304', '0', 'nil']
# 4/30 23:00:06.698  SPELL_AURA_REMOVED      0x0600000000024B94  Shadowmight ['47753', 'Divine Aegis', '0x2', 'BUFF']
# 4/30 23:00:06.698  SPELL_AURA_REMOVED      0x06000000002E04FB        Morja ['64413', 'Protection of Ancient Kings', '0x8', 'BUFF']
# 4/30 23:00:06.698  SPELL_PERIODIC_DAMAGE   0xF130008FF5000B81   Sindragosa ['71052', 'Frost Aura', '0x10', '4053', '0', '16', '5697', '0', '4493', 'nil']

#                                                                                                                dmg                resist        abosrb
# 4/30 22:56:11.465  SPELL_DAMAGE            0xF130008FF5000B81   Sindragosa ['71058', 'Frost Breath', '0x10', '12327', '0', '16', '20525', '0', '18462', 'nil']
# 10 dmg 13 resist 15 absorb
# 4/30 22:54:30.330  SWING_DAMAGE,0xF130008FF5000B81,"Sindragosa",0xa48,0x06000000004C3CEB,"Shoggoth",0x40514,16314,0,1,0,0,5325,nil,nil,nil

def do_shit(line):
    CACHE.pop(0)
    CACHE.append(line)

def more_shit(line, file=None):
    if file is None:
        print(line)
    else:
        file.write(line+'\n')
# 4/30 22:58:24.355 SPELL_HEAL                 Shadowmight 4767
# 4/30 22:58:24.416 SPELL_AURA_APPLIED         Shadowmight Divine Aegis
# 4/30 22:58:24.416 SPELL_AURA_APPLIED         Shadowmight Power Word: Shield
# 4/30 22:58:24.666 SPELL_AURA_REMOVED         Shadowmight Divine Aegis
# 4/30 22:58:24.666 SPELL_PERIODIC_MISSED       Sindragosa  4884
# 4/30 22:58:24.922 SPELL_PERIODIC_MISSED       Sindragosa  1017
# 4/30 22:58:25.234 SPELL_AURA_REMOVED         Shadowmight Power Word: Shield
# 4/30 22:58:25.234 SWING_DAMAGE                Sindragosa 14649

# 4/30 22:58:25.234  SWING_DAMAGE,0xF130008FF5000B81,"Sindragosa",0x10a48,0x06000000004C3CEB,"Shoggoth",0x40514,19693,0,1,0,0,14649,nil,nil,nil

# 1430.1
# 4884 1017 14649
# Sacred Shield ~ 4665 4674 4664

#      PWS    DAegi  Morja  Artem  PovSa  ArtSa   
zzz = [False, False, False, False, False, False]
zzz2 = ['Power Word: Shield', 'Divine Aegis', 'Protection of Ancient Kings', 'Protection of Ancient Kings', 'Sacred Shield', 'Sacred Shield']
zzz3 = ['PW:Sh', 'DAegi', 'PAKMo', 'PAKAr', 'PovSS', 'ArtSS']

def qqq(n, z):
    if z:
        return zzz3[n]
    return '_____'

# ims
# spell deflection
# other absorb
# pok

# [19:56:55.110] Morja Earthliving Shoggoth +288 (O: 805) = 0 absorbs?

d = {}
CACHE = ['','','','','']
AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_AURA_REMOVED'}

AURAS_NAME = {'Protection of Ancient Kings', 'Power Word: Shield', 'Divine Aegis', 'Sacred Shield', 'Hardened Skin', 'Anti-Magic Shell', 'Savage Defense'}
ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SWING_MISSED', 'SPELL_MISSED'}

DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
HEAL_FLAGS = {'SPELL_PERIODIC_HEAL', 'SPELL_HEAL'}
ALL_FLAGS = ABSORB_FLAGS | DMG_FLAGS | HEAL_FLAGS
LOGS_NAME_SLICE = 'WoWCombatLogSindraIllu.txt'
SOURCE_GUIDS = {'0x06000000002E04FB', '0x0600000000230080', '0x0600000000024B94'}
VALANYR = 'Protection of Ancient Kings'

def valanyr_users(logs_name):
    logs = get_logs(logs_name)
    return {line.split(',')[1] for _, line in logs if VALANYR in line}

def PoAK(valanyr_users):
    AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH'}
    logs = get_logs(LOGS_NAME_SLICE)
    t = {}
    absorbs = {}
    for time, line in logs:
        line = line.split(',')
        flag, source_guid, source_name, _, target_guid, target_name, _, *other = line
        if source_guid in valanyr_users:
            if flag in HEAL_FLAGS and 'Twilight Renewal' not in other:
                t.setdefault(source_guid, {})[target_guid] = [time, target_guid, other[3], line]
            elif VALANYR in other and flag in AURA_FLAG:
                last_time, last_target, last_heal, last_line = t[source_guid][target_guid]

                if target_guid == last_target:
                    absorbs.setdefault(source_guid, {}).setdefault(target_guid, []).append(last_heal)
    return absorbs


def filter_absorbs(absorbs, filter_guid=None):
    source = []
    for source_guid, targets in absorbs.items():
        if filter_guid and filter_guid in targets:
            source.append((sum(map(int, targets[filter_guid]))*15//100, source_guid, []))
        else:
            target_ = []
            for target_guid, raw_list in targets.items():
                target_.append((sum(map(int, raw_list))*15//100, target_guid, raw_list))
            target_ = sorted(target_, reverse=True)
            source.append((sum(x[0] for x in target_), source_guid, target_))
    return sorted(source, reverse=True)

GUIDS_FILE_NAME = 'GUIDS.txt'
with open(GUIDS_FILE_NAME, 'r') as f:
    GUIDS = json.load(f)

v = valanyr_users(LOGS_NAME_SLICE)
raw_absorbs = PoAK(v)
for s, source_guid, targets in filter_absorbs(raw_absorbs, '0x06000000004C3CEB'):
    print(f"{GUIDS[source_guid]['name']:<34}{s:>9}")
    for s2, target_guid, raw_list in targets:
        print(f"    {GUIDS[target_guid]['name']:<30}{s2:>9}")

def pretty_parse(logs_name):
    logs = get_logs(logs_name)
    open('qweqweqwe.txt', 'w').close()
    THE_FILE = open('qweqweqwe.txt', 'a+')
    for time, line in logs:
        line = line.split(',')
        flag, source_guid, source_name, _, target_guid, _, _, *other = line

        if target_guid == '0x06000000004C3CEB':
            add_line = ' '.join(f'{qqq(n, z):6}' for n, z in enumerate(zzz))
            if 'ABSORB' in line:
                line = f"{time} | {flag:<24}|{source_name:>13} | {other[4]:>6}{add_line:>80}"
                more_shit(line, THE_FILE)
            elif flag in DMG_FLAGS:
                if flag != 'SWING_DAMAGE':
                    other = other[3:]
                absorb = int(other[5])
                if absorb > 0:
                    line = f"{time} | {flag:<24}|{source_name:>13} | {absorb:>6}{other[0]:>6}{add_line:>74}"
                    more_shit(line, THE_FILE)
            elif flag in AURA_FLAG:
                aura = other[1]
                if aura in AURAS_NAME:
                    line = f"{time} | {flag:<24}|{source_name:>13} | {aura:<45}{add_line}"
                    more_shit(line, THE_FILE)
                    if aura in zzz2:
                        i = zzz2.index(aura) + (source_name == 'Arthemiis')
                        zzz[i] = flag != 'SPELL_AURA_REMOVED'
            elif flag in HEAL_FLAGS and source_guid == '0x0600000000230080':
            # elif flag in HEAL_FLAGS and source_guid in SOURCE_GUIDS:
                    line = f"{time} | {flag:<24}|{source_name:>13} | {other[3]:>6}{add_line:>80}"
                    more_shit(line, THE_FILE)

# pretty_parse(LOGS_NAME_SLICE)