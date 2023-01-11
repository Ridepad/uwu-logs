from collections import defaultdict
from datetime import timedelta
from constants import to_dt_simple


AURA_FLAGS = {
    "SPELL_AURA_APPLIED": 1,
    "SPELL_AURA_REMOVED": 0,
    "SPELL_AURA_REFRESH": -1,
    "SPELL_AURA_APPLIED_DOSE": -1,
    "SPELL_AURA_REMOVED_DOSE": -1,
}
class AurasMain:
    def __init__(self, logs_slice: list[str]) -> None:
        self.logs = logs_slice
        self.slice_start = to_dt_simple(logs_slice[0])
        self.slice_end = to_dt_simple(logs_slice[-1])
        self.slice_duration = (self.slice_end-self.slice_start).total_seconds()

    def to_prcnt(self, td: timedelta):
        d = td.total_seconds() / self.slice_duration * 100
        return round(d, 5)
    
    def combine_uptime(self, timings: dict[str, int]):
        timings_list = list(timings.items())
        timestamp, code = timings_list.pop(0)
        dt_last = to_dt_simple(timestamp)
        is_applied = code != 1
        percent = self.to_prcnt(dt_last - self.slice_start)
        uptime = [(is_applied, percent)]
        for timestamp, code in timings_list:
            if code == -1:
                if is_applied:
                    continue
                is_applied = True
            else:
                is_applied = code == 1
            
            dt_current = to_dt_simple(timestamp)
            percent = self.to_prcnt(dt_current - dt_last)
            uptime.append((not is_applied, percent))
            dt_last = dt_current
        
        percent = self.to_prcnt(self.slice_end - dt_last)
        uptime.append((is_applied, percent))
        return uptime

    def combine_spells(self, times: dict):
        return {
            spell_id: self.combine_uptime(timings)
            for spell_id, timings in times.items()
        }

    def combine_target(self, times: dict, is_player=True):
        if is_player:
            return self.combine_spells(times)
        return {
            target_guid: self.combine_spells(spells)
            for target_guid, spells in times.items()
        }

    def main(self, filter_guid):
        casts: dict[str, dict[str, list[tuple[bool, str]]]] = defaultdict(lambda: defaultdict(list))

        buffs: dict[str, list[tuple[bool, str]]] = defaultdict(dict)
        debuffs: dict[str, list[tuple[bool, str]]] = defaultdict(dict)

        spells: set[str] = set()
        
        for line in self.logs:
            if filter_guid not in line: continue
            if 'BUFF' not in line: continue
            if 'DISPEL' in line: continue
                
            timestamp, flag, source_guid, _, target_guid, _, spell_id, _, _, buff, *_ = line.split(',', 11)
            spell_id = int(spell_id)
            if target_guid == filter_guid:
                if buff == 'BUFF':
                    buffs[spell_id][timestamp] = AURA_FLAGS[flag]
                else:
                    debuffs[spell_id][timestamp] = AURA_FLAGS[flag]
                spells.add(spell_id)
            # elif source_guid == filter_guid and buff == 'DEBUFF':
            #     casts[target_guid][spell_id].append(z)
            #     spells.add(spell_id)
                # casts.setdefault(target_guid, {}).setdefault(spell_id, []).append(z)
        
        # casts = self.combine_target(casts, is_player=False)

        buffs = self.combine_spells(buffs)
        buffs_uptime = {}
        for spell_id, data in buffs.items():
            s = sum(y for x,y in data if x)
            buffs_uptime[spell_id] = f"{s:.2f}"

        debuffs = self.combine_spells(debuffs)
        debuffs_uptime = {}
        for spell_id, data in debuffs.items():
            s = sum(y for x,y in data if x)
            debuffs_uptime[spell_id] = f"{s:.2f}"

        return {
            "casts": casts,
            "buffs": buffs,
            "debuffs": debuffs,
            "spells": spells,
            "buffs_uptime": buffs_uptime,
            "debuffs_uptime": debuffs_uptime,
        }

    def combine_targets(self, casts):
        q: dict
        guid: str
        new_casts = {}
        for guid, spells in casts.items():
            guid = guid if guid.startswith('0x0') else guid[:-6]
            q = new_casts.setdefault(guid, {})
            q.setdefault("targets", []).append(guid)
            for spell, uptime in spells.items():
                q.setdefault("spells", {}).setdefault(spell, []).append(uptime)
        return new_casts

def __test():
    import logs_main
    report_id = '21-11-05--21-07--Nomadra'
    report = logs_main.THE_LOGS(report_id)
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    filter_guid = '0x060000000040F817'
    s, f = enc_data['The Lich King'][-2]
    logs_slice = logs[s:f]
    a = AurasMain(logs_slice)
    data = a.main(filter_guid)
    # print(data['buffs'])
    print(data['spells'])
    # casts = data['casts']
    # q = a.combine_target(casts, is_player=False)
    # print(q)
    # print(casts['0xF130008EF5000D6A']['Faerie Fire'])
    # print(q['0xF130008EF5000D6A']['Faerie Fire'])
    # print(q['CAST'])
    # for x, v in t.items():
    # uptime = sum(v)/dur*100
    # print(f'{x:>20} {uptime:6.1f}%')


if __name__ == "__main__":
    __test()