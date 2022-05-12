from typing import Dict, List, Set
import constants

# check if someone died mid pull

TLK = 'the_lich_king'
TLK = 'The Lich King'

ALL_FLAGS = {'SPELL_DAMAGE', 'SPELL_MISSED', 'SWING_DAMAGE', 'SWING_MISSED', 'RANGE_DAMAGE', 'RANGE_MISSED'}
ALL_FLAGS = ALL_FLAGS | {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH'}
# ALL_FLAGS = ALL_FLAGS | {'SPELL_PERIODIC_DAMAGE'}

LK = "0xF130008EF5"
VALK = "0xF150008F01"
# ALL_FLAGS = {'SPELL_DAMAGE', 'SPELL_MISSED', 'SWING_DAMAGE', 'SWING_MISSED', 'RANGE_DAMAGE', 'RANGE_MISSED', 'SPELL_AURA_APPLIED'}
# HEAL_FLAGS = {'SPELL_AURA_APPLIED', 'SPELL_HEAL'}
HEAL_FLAGS = {'SPELL_HEAL'}

BURST_SPELLS = [
    'Starfall', "Death and Decay", 'Immolation', 'Shadowflame', "Living Bomb", "Killing Spree",
    'Judgement of Light', 'Earth Shield', "Prayer of Mending", "Mark of Blood"]

def sort_dict_by_value(d: dict):
    return sorted(d.items(), key=lambda x: x[1], reverse=True)

def remove_last_wave(all_grabs):
    print(all_grabs)
    q = sum(wave[-1] == 0 for wave in all_grabs.values())
    if q > 5:
        return {guid:waves[:-1] for guid, waves in all_grabs.items()}
    return all_grabs

def get_valks_summon_time(logs_slice: List[str]):
    valks = {}
    for line in logs_slice:
        if '_SUMMON' in line and ",0xF150008F01" in line:
            timestamp, _, _, _, tguid, _ = line.split(',', 5)
            valks[timestamp] = tguid
    return valks
    # return [
    #     line.split(',', 1)[0]
    #     for line in logs_slice
    #     if '_SUMMON' in line and ",0xF150008F01" in line
    #     # if "Val'kyr Shadowguard" in line and 'SPELL_SUMMON' in line
    # ]

def find_tanks(logs_slice: List[str]):
    dmg_taken = {}
    for line in logs_slice[:10000]:
        if ',SWING_' not in line:
            continue
        _, _, sguid, _, tguid, _  = line.split(',', 5)
        if "008EF5" in sguid or "009342" in sguid or "008F5D" in sguid:
            dmg_taken[tguid] = dmg_taken.get(tguid, 0) + 1
    return list(dict(sort_dict_by_value(dmg_taken)))[:2]

def count_grabs(all_grabs: dict):
    grabs_num = {}
    for guid, activity in all_grabs.items():
        # grabs_threshold = max(y) // 3 + 1
        _activity = [x for x in activity if x!=-1]
        if not _activity:
            continue
        grabs_threshold = sum(_activity) / len(_activity) / 3

        grabs = [int(grab < grabs_threshold) if grab != -1 else -1 for grab in activity]
        grabs_sum = sum(grabs)
        if grabs_sum > 0:
            # grabs_num[guid] = grabs_sum
            grabs_num[guid] = [grabs_sum, grabs]
    return grabs_num

def slice_wave(valks_waves, x):
    timestamps, guids = zip(*valks_waves[x*3:(x+1)*3])
    return (max(timestamps), guids)

def combine_valk_waves(valks_times: dict):
    waves_amount = (len(valks_times)+2)//3
    valks_waves = list(valks_times.items())
    return [slice_wave(valks_waves, x) for x in range(waves_amount)]

def rounder(num):
    v = f"{num:,}" if type(num) == int else f"{num:,.1f}"
    return v.replace(",", " ")

def percentage_of_overall(activity, avg_activity):
    t = []
    for x in activity:
        if x != -1:
            x = x / avg_activity * 1000 // 1 / 10
        t.append(x)
    return t

def sort_dict_by_value(d: dict):
    return sorted(d.items(), key=lambda x: x[1], reverse=True)

def check_presence(logs_slice: List[str]):
    players = {}
    for line in logs_slice[:2000]:
        if "0x06" not in line:
            continue
        sguid = line.split(',', 4)[2]
        if "0x06" not in sguid:
            continue
        players[sguid] = players.get(sguid, 0) + 1
    return players

def find_lk(guids):
    for guid in guids:
        if "008EF5" in guid:
            return guid

class Valks:
    def __init__(self, report) -> None:
        self.report = report
        self.all_guids = report.get_all_guids()
        self.TLK = find_lk(self.all_guids)
        self.timestamp = report.get_timestamp()
        self.players_data = report.get_players_guids()
        self.logs = report.get_logs()
        self.RAID_START = constants.to_dt(self.logs[0])
        self.enc_data = report.get_enc_data()
        self.classes = report.get_classes()
        self.times_data = self.report.get_timestamp()
        
    def convert_to_names(self, d):
        return {
            self.players_data[guid]: data
            for guid, data in d.items()
        }
    
    def count_grabs(self, all_activity: Dict[str, List[int]]):
        grabs_num = {}
        full_activity = {}
        grabs: Dict[str, list] = {}
        for name, activity in all_activity.items():
            _activity = [x for x in activity if x != -1]
            if not _activity:
                continue

            third = len(_activity) // 3
            _a = sorted(_activity)[-third:]
            avg_activity = sum(_a) / (len(_a) or 1)
            # if self.classes[name] == 'warlock':
                # avg_activity = avg_activity * 4
            # else:
            #     grabs_threshold = avg_activity / 4

            # grabs = [int(grab <= grabs_threshold) if grab != -1 else -1 for grab in activity]
            # grabs_sum = grabs.count(1)
            # grabs_num[name] = grabs_sum
            # grabs.insert(0, 0)
            # activity.insert(0, f"{grabs_threshold:.1f}")
            # details[name] = zip(grabs, activity)
            full_activity[name] = percentage_of_overall(activity, avg_activity)
            grabs[name] = [-1 if grab == -1 else 0 for grab in activity]
        the_l = len(next(iter(full_activity.values())))
        for i in range(the_l):
            column = {name: x[i] for name,x in full_activity.items() if x[i] != -1}
            if not column: # all are -1
                continue
            column = sorted(column.items(), key=lambda x: x[1])[:3]
            for name, _ in column:
                grabs[name][i] = 1
        details = {}
        print(full_activity)
        for name, activity in full_activity.items():
            _grabs = grabs[name]
            grabs_num[name] = _grabs.count(1)
            details[name] = zip(_grabs, activity)

        return grabs_num, details

    @constants.running_time
    def main(self):
        # s,f = self.enc_data[TLK][-1]
        activity = {}
        for s,f in self.enc_data[TLK]:
            logs_slice = self.logs[s:f]
            activity_data = self.process_lk_attempt(logs_slice)
            for guid, data in activity_data.items():
                activity[guid] = activity.get(guid, []) + data + [-1]
            
        # all_grabs = self.waves(logs_slice)
        activity = self.convert_to_names(activity)
        all_grabs, details = self.count_grabs(activity)
        all_grabs = sort_dict_by_value(all_grabs)
        return all_grabs, details

    def process_lk_attempt(self, logs_slice):
        valk_waves = get_valks_summon_time(logs_slice)
        if not valk_waves:
            return {}
        tanks = find_tanks(logs_slice)
        present_players = check_presence(logs_slice)
        # present_players = set(present_players)
        valk_waves = combine_valk_waves(valk_waves)
        activity = self.check_activity(valk_waves)
        absent_players = set(self.players_data) - set(present_players)
        absent_players.update(tanks)
        activity = self.add_absence(activity, absent_players)
        return activity


    def slice_logs(self, wave_time):
        wave_time = constants.to_dt(wave_time)
        t = (wave_time-self.RAID_START).seconds
        try:
            start, finish = self.times_data[t-5], self.times_data[t+25]
        except:
            start, finish = self.times_data[t], self.times_data[-1]
        return self.logs[start:finish]

    def get_activity(self, logs_slice: List[str], valk_guids: Set[str]):
        _filter = set(valk_guids)
        _filter.add(self.TLK)
        print(_filter)
        activity = {}
        for line in logs_slice:
            if any(spell_name in line for spell_name in BURST_SPELLS):
                continue
            _, flag, source_guid, _, tguid, _, = line.split(',', 5)
            line = line.split(',')
            if source_guid not in self.players_data:
                continue
            if (
                flag == "SPELL_HEAL"
                or flag in ALL_FLAGS
                and tguid in _filter
            ):
                activity[source_guid] = activity.get(source_guid, 0) + 1
        print(activity)
        return activity

    def add_absence(self, all_activity, absent_players):
        activity_new = all_activity
        waves_count = len(max(activity_new.values(), key=len))
        print(waves_count)
        print()
        absence = [-1]*waves_count
        for guid in absent_players:
            activity_new[guid] = absence
        return activity_new
    
    def check_activity(self, valk_waves):
        all_activity = {guid:[] for guid in self.players_data}
        for wave_time, valk_guids in valk_waves:
            logs_slice = self.slice_logs(wave_time)
            activity = self.get_activity(logs_slice, valk_guids)
            for guid, data in all_activity.items():
                data.append(activity.get(guid, 0))
        return all_activity