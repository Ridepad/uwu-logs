from constants import running_time
from logs_units_guid import logs_parser
import logs_main

@running_time
def find_summon_timing(logs: list, guid):
    for line in logs:
        if guid in line:
            return logs.index(line)

def count_udk_actions(logs: list, udk_guids):
    actions = {}
    for line in logs:
        line = line.split(',')
        source_guid = line[2]
        if source_guid in udk_guids and "SPELL_AURA" not in line[1]:
            actions[source_guid] = actions.get(source_guid, 0) + 1
    return actions

@running_time
def pair_gargoyles(logs: list, gargoyles: list, unholy_DKs):
    n = 0
    paired_gargoyles = {}
    udk_guids = dict(unholy_DKs).keys()
    for guid in gargoyles:
        n = find_summon_timing(logs[n:], guid) + n
        actions = count_udk_actions(logs[n-100:n+100], udk_guids)
        paired_gargoyles[guid] = max(actions.items(), key=lambda x: x[1])[0]
    return paired_gargoyles

def lost_gargoyles(everything):
    # if 1 udk - combines unaccounted Ebon Gargoyles
    return [
        guid
        for guid, y in everything.items()
        if guid.startswith('0xF130006CB5') and not y.get('master_guid')
    ]

if __name__ == "__main__":
    name = '210621-Passionne'
    LOGS = logs_main.THE_LOGS(name)

    logs = LOGS.get_logs()

    everything, players, pets_data, unholy_DKs, unholy_DK_pets = logs_parser(logs)

    print(unholy_DKs)
    gargoyles = lost_gargoyles(everything)
    if gargoyles:
        print(gargoyles)
        p = {}
        for guid, master_guid in pair_gargoyles(logs, gargoyles, unholy_DKs).items():
            p[guid] = {'name': 'Ebon Gargoyle', 'master_name': players[master_guid], 'master_guid': master_guid}
        print(p)