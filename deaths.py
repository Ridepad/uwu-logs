from datetime import timedelta
from typing import List
import _main
import constants
import re
CDS = {
    '6940',  #Hand of Sacrifice
    '31821', #Aura Mastery
    '53601', #Sacred Shield - Aura
    '58597', #Sacred Shield - Shield
    '64205', #Divine Sacrifice
    '70940', #Divine Guardian
    '71586', #Hardened Skin
    '71638', #Aegis of Dalaran
    '45438', #Ice Block
    '47585', #Dispersion
    '642', #Divine Shield
    '51052', #Anti-Magic Zone
    '49222', #Bone Shield
    '51271', #Unbreakable Armor
    '5487', #Bear Form
    '9634', #Dire Bear Form
    '48575', #Cower
    '33206', #Pain Suppression
    '48066', #Power Word: Shield
    '54861', #Nitro Boosts
}
CDS |= { #DK
    '48707', #AMS
    '48792', #IBF
    '55233', #Vampiric Blood
    '64859', #Blade Barrier
    '70654', #Blood Armor
}
CDS |= { #PPal
    '498',   #Divine Protection
    '31884', #Avenging Wrath
    '48952', #Holy Shield
}
CDS |= { #Bear
    '5229',  #Enrage
    '22812', #Barkskin
    '22842', #Frenzied Regeneration
    '61336', #Survival Instincts
}
DEBUFFS = {
    '73799', #Soul Reaper
    '6788', #Weakened Soul
    '25771', #Forbearance
    '69762', #Unchained Magic
}
AURAS = CDS | DEBUFFS
DEATH_FLAGS = {"UNIT_DIED", "SPELL_INSTAKILL"}
HEALS = {"SPELL_HEAL", "SPELL_PERIODIC_HEAL"}
FLAGS = {'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SPELL_HEAL', 'SPELL_PERIODIC_HEAL', "SWING_DAMAGE"}
FLAGS_CUT = {
    'SPELL_DAMAGE': ('DAMAGE', 'SPELL'),
    'SPELL_PERIODIC_DAMAGE': ('DAMAGE', 'DoT'),
    'RANGE_DAMAGE': ('DAMAGE', 'RANGE'),
    'DAMAGE_SHIELD': ('DAMAGE', 'SHIELD'),
    'SPELL_HEAL': ('HEAL', 'HEAL'),
    'SPELL_PERIODIC_HEAL': ('HEAL', 'HoT'),
    'ENVIRONMENTAL_DAMAGE': ('DAMAGE', 'ENVR'),
    'SWING_DAMAGE': ('DAMAGE', 'SWING'),
    'SPELL_AURA_APPLIED': ('AURA', 'APPLIED'),
    'SPELL_AURA_REFRESH': ('AURA', 'REFRESH'),
    'SPELL_AURA_REMOVED': ('AURA', 'REMOVED'),
    'SPELL_AURA_APPLIED_DOSE': ('AURA', 'DOSE'),
    'UNIT_DIED': ('', 'DIED'),
    'SPELL_INSTAKILL': ('DIED', 'INSTAKILL'),
}
OTHER_FLAGS = {'SWING_DAMAGE', 'ENVIRONMENTAL_DAMAGE'}
ALL_FLAGS = {
    'SPELL_AURA_REFRESH', 'SPELL_ENERGIZE', 'SPELL_DAMAGE', 'SPELL_PERIODIC_DAMAGE', 'ENVIRONMENTAL_DAMAGE', 'SPELL_AURA_REMOVED',
    'SWING_DAMAGE', 'SPELL_AURA_APPLIED_DOSE', 'SPELL_HEAL', 'SWING_MISSED', 'UNIT_DIED', 'SPELL_DISPEL', 'SPELL_MISSED',
    'SPELL_PERIODIC_HEAL', 'SPELL_PERIODIC_MISSED', 'SPELL_CAST_SUCCESS', 'SPELL_RESURRECT', 'SPELL_AURA_APPLIED'}
AURA_FLAGS = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_AURA_REMOVED', 'SPELL_AURA_APPLIED_DOSE'}
TD = timedelta(seconds=120)
REM_BUFFS = timedelta(seconds=2)

def ffff(td, flag, source, action, arg1="", arg2=""):
    return f"{td} {flag:<25}{source:>20}{action:>30}{arg1:>9}{arg2:>9}"

def format_number(root: str, q: str):
    if not q or q == "0":
        return q
    sign = "+" if root == "HEAL" else "-"
    z = re.findall("(\d{1,3})", q[::-1])
    return sign + " ".join(z)[::-1]

def format_timestamp(timestamp):
    minutes, seconds = divmod(timestamp.seconds, 60)
    return f"-{minutes:02}:{seconds:02}.{timestamp.microseconds//1000:03}"

def format_line(line: list, flag: str, fullhp: bool):
    if flag in AURA_FLAGS and line[6] in AURAS:
        return line[7], line[9], ""
    elif fullhp:
        return
    if flag in FLAGS:
        return line[7], line[9], line[10]
    elif flag == 'ENVIRONMENTAL_DAMAGE':
        return line[6], line[7], line[8]
    elif flag == 'SPELL_INSTAKILL':
        return line[7], "", ""

def logs_guid_gen(logs: List[str], guid: str):
    for n, line in enumerate(logs):
        if guid not in line:
            continue
        line_s = line.split(',')
        if line_s[4] == guid:
            yield n, line_s

def look_back(logs: list, n: int, guid: str):
    fullhp = False
    last_line = logs[n].split(',')
    while last_line[1] not in FLAGS_CUT:
        print(last_line)
        n = n - 1
        last_line = logs[n].split(',')
    print(last_line)
    root, suffix = FLAGS_CUT[last_line[1]]
    yield "", "-00:00.000", suffix, last_line[5], "", "", ""
    st = constants.to_dt(last_line[0])
    logs = reversed(logs[:n])
    for c, line in logs_guid_gen(logs, guid):
        now = st - constants.to_dt(line[0])
        if now > TD:
            # print("2 MINUTES AT:", c)
            break
        flag = line[1]
        if not fullhp and flag in HEALS and line[10] != "0":
            fullhp = True
        z = format_line(line, flag, fullhp)
        if not z:
            continue
        timestamp = format_timestamp(now)
        root, suffix = FLAGS_CUT[flag]
        spell, v1, v2 = z
        if root == "AURA":
            css = v1.lower()
        else:
            css = root.lower()
            v1 = format_number(root, v1)
            v2 = format_number(root, v2)
        yield css, timestamp, suffix, line[3], spell, v1, v2

@constants.running_time
def unit_died(logs: list, guid: str):
    return any(("UNIT_DIED" in line or "SPELL_INSTAKILL" in line) and guid in line for line in logs)

@constants.running_time
def find_deaths(logs: list, guid: str):
    death_logs = {}
    buffs_removed = 0
    last_time = constants.to_dt(logs[0])

    for n, line in logs_guid_gen(logs, guid):
        if line[-1] == "BUFF" and line[1] == "SPELL_AURA_REMOVED":
            # print(line)
            timestamp = constants.to_dt(line[0])
            if timestamp - last_time > REM_BUFFS:
                buffs_removed = 0
            buffs_removed += 1
            last_time = timestamp
        # elif line[1] == "SPELL_INSTAKILL":
            # if not unit_died(logs[n:n+300], guid):
                # print('UNIT_DIED AFTER SPELL_INSTAKILL WTF')
            # print(line[0], 'unit alive, flag is:', line[1])
            # death_logs[line[0]] = look_back(logs, n, guid)
            # buffs_removed = 0
        elif line[1] == "UNIT_DIED":
            # print(line[0], 'flag is:', line[1])
            death_logs[line[0]] = look_back(logs, n, guid)
            buffs_removed = 0
        else:
            if line[1] == "SPELL_INSTAKILL" or buffs_removed > 7:
                if not unit_died(logs[n+1:n+300], guid):
                    death_logs[line[0]] = look_back(logs, n-1, guid)
            buffs_removed = 0
    return death_logs

if __name__ == "__main__":
    name = '210628-Passionne'
    LOGS = _main.THE_LOGS(name)

    logs = LOGS.get_logs()
    enc_data = LOGS.get_enc_data()
    s, f = enc_data["the_lich_king"][5]
    logs = logs[s:f]

    guid = '0x06000000002E50C8'

    for x in find_deaths(logs, guid):
        for line in x:
            print(len(line)==6)