from constants import running_time
from typing import List
import _main
import json

DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}
HEAL_FLAGS = {'SPELL_PERIODIC_HEAL', 'SPELL_HEAL'}
FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'SPELL_CAST_SUCCESS'}
ALL_FLAGS = DMG_FLAGS | HEAL_FLAGS
FLAGS = {
    'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_CAST_SUCCESS', 'SWING_DAMAGE',
    'SWING_MISSED', 'SPELL_HEAL', 'SPELL_MISSED', 'SPELL_DAMAGE'}
FLAGS = {
    'SPELL_CAST_SUCCESS', 'SPELL_AURA_REFRESH', 'SPELL_CREATE', 'SWING_MISSED', 'SPELL_AURA_REMOVED', 'SWING_DAMAGE',
    'SPELL_CAST_START', 'SPELL_SUMMON', 'SPELL_PERIODIC_HEAL', 'SPELL_AURA_APPLIED_DOSE', 'DAMAGE_SPLIT', 'SPELL_HEAL',
    'SPELL_AURA_APPLIED', 'SPELL_DISPEL', 'ENCHANT_APPLIED', 'SPELL_ENERGIZE'}
FLAGS = {
    'SPELL_CAST_SUCCESS', 'SPELL_AURA_REFRESH', 'SWING_MISSED', 'SWING_DAMAGE',
    'SPELL_CAST_START', 'SPELL_SUMMON', 'SPELL_HEAL', 'SPELL_AURA_APPLIED', 'SPELL_DISPEL'}
FLAGS = {'SPELL_CAST_SUCCESS', 'SPELL_HEAL', 'SPELL_DAMAGE', 'SPELL_MISSED', 'SWING_DAMAGE', 'SWING_MISSED', 'RANGE_DAMAGE', 'RANGE_MISSED'}
    
UWU = {'SPELL_PERIODIC_HEAL', 'SPELL_PERIODIC_DAMAGE', 'ENVIRONMENTAL_DAMAGE', 'SPELL_HEAL', 'RANGE_DAMAGE', 'SWING_DAMAGE', 'DAMAGE_SHIELD', 'SPELL_DAMAGE', 'DAMAGE_SPLIT'}
UWU = {'SPELL_PERIODIC_HEAL', 'SPELL_PERIODIC_DAMAGE', 'ENVIRONMENTAL_DAMAGE', 'RANGE_DAMAGE', 'SWING_DAMAGE', 'DAMAGE_SHIELD', 'SPELL_DAMAGE', 'DAMAGE_SPLIT'}
DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SWING_MISSED', 'SPELL_MISSED'}
AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_AURA_REMOVED'}
ALL_FLAGS = DMG_FLAGS | ABSORB_FLAGS | AURA_FLAG

@running_time
def filter_logs(logs: List[str]):
    s2 = set()
    s3 = {}
    for line in logs:
        line = line.split(',')
        if '0x06' not in line[2]:
            continue
        if '008F01' not in line[4]:
            continue
        try:
            # if line[12] != "0":
            print(f"{line[1]:>25} {line[3]:>12} {line[5]:>12} {line[9]:>20} {line[12]:>10} {line[14]:>10}")
        except IndexError:
            pass
    print(s3)

def filter_logs(logs):
    for line in logs:
        if 'Shadow Trap' not in line:
            continue
        line = line.split(',')
        print(f"{line[0]} {line[1]:>25} {line[3]:>12} {line[5]:>12} {line[7]:>20} {line[9]:>20}")

# def filter_logs(logs):
#     for line in logs:
#         if 'Ice Pulse' not in line:
#             continue
#         if 'DAMAGE' not in line:
#             continue
#         # if 'AURA' in line:
#         #     continue
#         # if 'Thoodhun' not in line[5]:
#         #     continue
#         line = line.split(',')
#         print(f"{line[0]} {line[1]:>25} {line[3]:>12} {line[5]:>12} {line[7]:>20} {line[9]:>20} {line[12]:>10} {line[14]:>10}")
#         # print(line)

@running_time
def filter_logs2(logs):
    s = {}
    last_abom = {}
    
    for line in logs:
        # if "70308" in line or "958D" in line and "958D" in line[:55] and "958D" in line[55:]:
        if "70308" in line or "958D" in line:
            timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
            if other[0] == '70308': # Mutated Transformation
                last_abom = {
                    'name': name,
                    'master_name': source_name,
                    'master_guid': source_guid
                }
            elif last_abom and source_guid == target_guid: # Mutated Abomination
                s[source_guid] = last_abom
                last_abom = {}

    print(s)


def filter_logs(logs):
    s = set()
    for line in logs:
        if 'DEBUFF' not in line:
            continue
        if '0x06' not in line:
            continue
        line = line.split(',')
        if "0x06" in line[4]:
            s.add((int(line[6]), line[7]))
    
    for x,y in sorted(s):
        print(f"{x:>5} {y}")

def filter_logs_mana(logs):
    s = set()
    s = {}
    for line in logs:
        if 'SPELL_ENERGIZE' not in line:
            continue
        # print(line)
        timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
        s.setdefault(source_name, {})[other[1]] = int(other[0])
        # s.add(line.split(',',10)[9])
        # if 'BUFF' not in line:
        #     continue
        # line = line.split(',')
        # if '0xF130008EF5' in line[4]:
        #     try:
        #         s.add((line[6], line[7]))
        #     except IndexError:
        #         pass

        # if line[3] == "Kalkkunax":
        #     try:
        #         s.add((line[6], line[7]))
        #     except IndexError:
        #         pass
    print(s)
    import json
    print(json.dumps(s))
    # for x,y in s:
    #     print(f"{x:>5}",y)

def filter_logs(logs: list[str]):
    s = set()
    for line in logs:
        if 'Zpevacik' not in line:
            continue
        timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
        if 'Zpevacik' not in source_name:
            continue
        # if source_name == "Baltharus the Warborn":
            # s.add(source_guid)
        # if source_guid.startswith('0x06'):
            # continue
        # if "Fire Nova" in other or "Flame Breath" in other:
        #     print(line)
        #     break
        # if target_name == "Baltharus the Warborn":
        if other:
            if other[0] == '1':
                continue
            s.add((source_name, other[0], other[1]))
    print(sorted(s))

def filter_logs_source_spells(logs: list[str], sGUID):
    s = set()
    for line in logs:
        if sGUID not in line:
            continue
        _line = line.split(',', 11)
        if _line[2] != sGUID:
            continue
        try:
            s.add((int(_line[6]), _line[7]))
        except IndexError:
            pass

    d = dict(sorted(s))
    print(json.dumps(d, indent=2))

def filter_logs_npc_spells(logs: list[str]):
    s = set()
    for line in logs:
        timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
        if source_guid.startswith('0x06'):
            continue
        try:
            spell = (source_name, int(other[0]), other[1])
            s.add(spell)
        except IndexError:
            continue
    print(sorted(s))
    

s = {
    # 'Freezing Slash',
    "Pursued by Anub'arak",
    'Penetrating Cold',
    'Acid-Drenched Mandibles',
    'Spider Frenzy',
    'Impale',
    # 'Permafrost',
    'Leeching Swarm',
    "Anub'arak Scarab Achievement 10",
    # 'Expose Weakness',
    'Submerge'
}

def filter_spells(logs):
    for line in logs:
        timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
        for spell in s:
            if spell in other:
                print(line)
                return

def filter_flags(logs):
    s = set()
    for line in logs:
        timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
        s.add(flag)
    print(sorted(s))

def main():
    name = '22-01-25--10-31--Volken'
    name = '22-01-08--15-28--Napnap'
    name = '21-11-06--19-52--Gotfai'
    name = '22-02-16--13-27--Naap'
    name = '22-02-17--18-03--Gotfire'
    name = '22-05-04--18-39--Lismee'
    name = '22-02-25--19-48--Xtan'
    name = '22-04-29--21-04--Nomadra'
    name = '21-10-01--20-47--Stanicenemy'
    name = '22-05-07--20-13--Piscolita'
    name = '22-05-07--20-13--Piscolita'
    name = '21-11-21--15-53--Matzumoto'
    name = '22-05-04--14-06--Piscolita'
    name = '22-05-06--21-05--Nomadra'
    name = '21-12-06--21-11--Solarstoned'
    report = _main.THE_LOGS(name)
    s, f = None, None
    # enc_data = report.get_enc_data()
    # s,f = enc_data["Anub'arak"][-1]
    logs = report.get_logs(s, f)
    # filter_logs_npc_spells(logs)
    # filter_spells(logs)
    # filter_flags(logs)
    print(len(logs))
    # filter_logs_source_spells(logs, "0x0600000000584358")

main()