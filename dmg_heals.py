import constants

DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
HEAL_FLAGS = {'SPELL_PERIODIC_HEAL', 'SPELL_HEAL'}
MISS_FLAGS = {'RANGE_MISSED', 'SPELL_MISSED', 'SPELL_PERIODIC_MISSED', 'SWING_MISSED', }#'DAMAGE_SHIELD_MISSED'

def quick_sum(q) -> int:
    return sum(x[0] for x in q)

def get_only_spells(data: dict, source_filter=None):
    all_spells = {}
    for source_guid, targets in data.items():
        if source_filter is not None and source_guid not in source_filter:
            continue
        for spells in targets.values():
            for spell_name, values in spells.items():
                _spells = all_spells.setdefault(source_guid, {})
                _spells[spell_name] = _spells.get(spell_name, 0) + sum(values)
    spells_list = []
    for source_guid, spells in all_spells.items():
        __d = [(value, name) for name, value in spells.items()]
        __d = sorted(__d, reverse=True)
        spells_list.append((quick_sum(__d), source_guid, __d))
    # if not spells_list:
    #     spells_list = [("", "")]
    return sorted(spells_list, reverse=True)
###################################
def get_only_spells2(data: dict, source_filter=None):
    newshitfuck = {}
    if source_filter is not None:
        for source_guid in source_filter:
            if source_guid in data:
                _spells = {}
                for spells in data[source_guid].values():
                    for spell_name, values in spells.items():
                        _spells[spell_name] = _spells.get(spell_name, 0) + sum(values)
                ttl = sum(_spells.values())
                zzzzzzz = [
                    [v, v / ttl * 1000 // 1 / 10, spell_name]
                    for spell_name, v in _spells.items()
                ]
                zzzzzzz = sorted(zzzzzzz, reverse=True)
                zzzzzzz.append([ttl, 100.0, 'Total'])
                newshitfuck[source_guid] = zzzzzzz

    return newshitfuck
###################################
def make_spell_list(spells: dict):
    spell_list = [(sum(values), spell_name) for spell_name, values in spells.items()]
    return sorted(spell_list, reverse=True)

def make_target_list(targets: dict, target_filter, ignore_targets):
    target_list = []
    for target_guid, spells in targets.items():
        if target_filter is not None and \
            target_guid not in target_filter or \
            target_guid in ignore_targets:
            continue
        spell_list = make_spell_list(spells)
        s = quick_sum(spell_list)
        if s:
            target_list.append((s, target_guid, spell_list))
    return sorted(target_list, reverse=True)

def get_everything(data: dict, players=None, source_filter=None, target_filter=None):
    data_sorted = []
    if players is None:
        players = {}
    ignore_targets = set(players)
    for source_guid, targets in data.items():
        if source_filter is not None and source_guid not in source_filter:
            continue
        target_list = make_target_list(targets, target_filter, ignore_targets)
        s = quick_sum(target_list)
        if s:
            data_sorted.append((s, source_guid, target_list))
    return sorted(data_sorted, reverse=True)

###################################

@constants.running_time
def parse_dmg_heals(logs: list, guids: dict):
    ALL_FLAGS = DMG_FLAGS | HEAL_FLAGS
    dmg_heals = [{}, {}]
    for line in logs:
        timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line.split(',')
        if flag in ALL_FLAGS:
            if flag == 'SWING_DAMAGE':
                spell_name = 'Melee'
                value = int(other[0]) - int(other[1])
            else:
                spell_name = other[1]
                value = int(other[3]) - int(other[4])
            
            if value > 1:
                master_guid = guids[source_guid].get('master_guid')
                if master_guid:
                    pet_name = guids[source_guid]['name']
                    source_guid = guids.get(master_guid, {}).get('master_guid') or master_guid
                    spell_name = f'{spell_name} (Pet - {pet_name})'
                dmg_heals[flag in HEAL_FLAGS].setdefault(source_guid, {}).setdefault(target_guid, {}).setdefault(spell_name, []).append(value)
    return dmg_heals
#####################################
if 1:
    def pretty_print_everything(data, guids):
        for source_total, source_guid, targets in data:
            source_name = guids[source_guid]['name']
            print(f'{source_name:<50}{source_total:>10,}')
            for target_total, target_guid, spells in targets:
                target_name = guids[target_guid]['name']
                print(f'    {target_name:<46}{target_total:>10,}')
                for value, spell_name in spells:
                    print(f'        {spell_name:<42}{value:>10,}')

    def pretty_print_only_spells(data, guids):
        for source_total, source_guid, spells in data:
            name = guids[source_guid]['name']
            print(f'{name:<50}{source_total:>10,} {source_guid}')
            for value, spell_name in spells:
                print(f'    {spell_name:<46}{value:>10,}')

    def pretty_print_only_players(data, players):
        for source_total, source_guid, _ in data:
            player_name = players.get(source_guid)
            if player_name:
                print(f'{player_name:<13}{source_total:>10,}')
#####################################

@constants.running_time
def find_tanks(logs):
    dmg_taken = {}
    for line in logs:
        if 'SWING_DAMAGE' in line and '0xF130008EF5' in line:
            line = line.split(',')
            dmg_taken[line[4]] = dmg_taken.get(line[4], 0) + int(line[6])
    return sorted(dmg_taken.items(), key= lambda x: x[1], reverse=True)

if __name__ == '__main__':
    import _main
    name = '210624-Passionne'
    LOGS = _main.THE_LOGS(name)
    logs = LOGS.get_logs()
    enc_data = LOGS.get_enc_data()
    s,f = enc_data["the_lich_king"][0]
    logs = logs[s:f]
    guids, players = LOGS.get_guids()
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    q = find_tanks(logs)
    # for x, v in q:
    #     print(f'{guids[x]["name"]:<12} {v:>10,}')
    # s,f = enc_data['the_lich_kings'][0]
    # logs = logs[s:f]
    # print(s,f)
    # filter_guid = '0xF130008EF50009E8'
    # print(filter_guid=='0x060000000040F817')
    # dmg, _ = parse_dmg_heals(logs,guids)
    # print('0x060000000040F817' in dmg)
    # q = get_everything(dmg, source_filter={filter_guid, })
    # pretty_print_everything(q, guids)
    # filter_guids = {constants.get_guid(player_name, guids)}
    # damage, heal = parse_dmg_heals(logs, guids)
    # damage = get_only_spells(damage, source_filter=filter_guids)
    # pretty_print_only_spells(damage, guids)
    # for source_total, source_guid, spells in only_spells(heal):
    #     name = GUIDS[source_guid]['name']
    #     print(f'{name:<50}{source_total:>9}')
    #     for value, spell_name in spells:
    #         print(f'    {spell_name:<46}{value:>9}')
