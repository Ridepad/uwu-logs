
# 4/30 22:56:07.414  SPELL_AURA_APPLIED      0x06000000001217CE          Pov ['58597', 'Sacred Shield', '0x2', 'BUFF']
# 4/30 22:56:07.416  SPELL_HEAL              0x06000000001217CE          Pov ['53654', 'Beacon of Light', '0x2', '22655', '0', '0', 'nil']
# 4/30 22:56:08.590  SPELL_PERIODIC_MISSED   0xF130008FF5000B81   Sindragosa ['70106', 'Chilled to the Bone', '0x10', 'ABSORB', '892']
# 4/30 22:56:09.191  SPELL_AURA_REMOVED      0x06000000001217CE          Pov ['58597', 'Sacred Shield', '0x2', 'BUFF']
# 4/30 22:56:09.191  SWING_DAMAGE            0xF130008FF5000B81   Sindragosa ['32303', '3010', '1', '0', '0', '3785', 'nil', 'nil', 'nil']

# 4/30 23:00:14.545  SPELL_MISSED,0xF130008FF5000B81,"Sindragosa",0xa48,0x06000000004613EE,"Nailyn",0x80514,73064,"Frost Breath",0x10,ABSORB,37726
from datetime import datetime, timedelta

def conv_to_dt(s):
    return datetime.strptime(s, '%m/%d %H:%M:%S.%f')

def logs_read(logs_path):
    with open(logs_path, 'r') as f:
        return f.readlines()

ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SWING_MISSED', 'SPELL_MISSED'}

DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
CAST_FLAGS = {'SPELL_AURA_APPLIED', 'SPELL_CAST_SUCCESS'}
# 5/8 01:03:01.471  SWING_DAMAGE,0xF130008EF5001491,"The Lich King",0x10a48,0x060000000024B74B,"Oroles",0x514,28206,0,1,0,0,4714,nil,nil,nil
# line.split('  ') == line

def main2(logs):
    active_sacred_shields = {}
    for line in logs:
        time, line = line.split('  ')
        flag, source_guid, source_name, _, target_guid, target_name, *other = line

def main(logs):
    active_sacred_shields = {}
    another_fucking_shield_list = []
    another_fucking_shield_list_temp = {}
    temp_absorb = 0
    ss_removed = {}
    ss_removed = False
    removed_from = ''
    duration = timedelta(seconds=6)
    for line in logs:
        time, line = line.split('  ')
        line = line.split(',')
        flag, source_guid, source_name, _, target_guid, target_name, *other = line
        
        if ss_removed:
            if flag in DMG_FLAGS and target_guid in active_sacred_shields:
                print('='*100)
                a = other[6]
                temp_absorb += int(a)
                print('final absorb:', a)
                ss = active_sacred_shields[target_guid]
                z = [ss['time_applied'], ss_removed[0], ss['caster'], ss_removed[1], ss['absorb']]
                print('final list:', z)
                another_fucking_shield_list.append(z)
                del active_sacred_shields[target_guid]
                print('='*100)
            if '"Protection of Ancient Kings"' not in other:
                ss_removed = False
            print("|")

        if '58597' in other:
            if flag in CAST_FLAGS:
                print(time, source_name, 'shield applied on', target_name)
                # active_sacred_shields.setdefault(target_guid, {})
                active_sacred_shields[target_guid] = {
                    'time_applied': conv_to_dt(time),
                    'time_exp': conv_to_dt(time) + duration,
                    'caster': source_guid,
                    'absorb': 0}
                print(active_sacred_shields)
            elif flag in 'SPELL_AURA_REMOVED':
                print(time, 'removed', source_name, 'shield from', target_name)
                ss_removed = (conv_to_dt(time), target_name)
        elif 'ABSORB' in other:
            if target_guid in active_sacred_shields:
            # if target_guid in another_fucking_shield_list_temp:
                # if conv_to_dt(time) > active_sacred_shields[target_guid]['time_exp']:
                    # remove
                a = int(other[5])
                print(time, 'adding', a, 'arsorb from ss to', target_name)
                ss = active_sacred_shields[target_guid]
                ss['absorb'] += a
                # another_fucking_shield_list_temp[target_guid][4] += a
        # elif flag in ABSORB_FLAGS:
    return another_fucking_shield_list

LOGS_NAME_SLICE = 'WoWCombatLogSindraIllu.txt'
logs = logs_read(LOGS_NAME_SLICE)
z = main(logs)
for x in z:
    print(x)