import constants
from datetime import timedelta

CNVRT = constants.to_dt


class AurasMain:
    def __init__(self, logs_slice: list[str]) -> None:
        self.logs = logs_slice
        self.slice_start = CNVRT(logs_slice[0].split(',')[0])
        self.slice_end = CNVRT(logs_slice[-1].split(',')[0])
        self.slice_duration = (self.slice_end-self.slice_start).total_seconds()

    def to_prcnt(self, td: timedelta):
        # rounds to 3 after dec point
        d = td.total_seconds() / self.slice_duration * 100
        return float(f"{d:.5f}")
    
    def combine_uptime(self, timings: list[tuple[bool, str]]):
        is_applied_last, timestamp = timings.pop(0)
        dt_last = CNVRT(timestamp)
        uptime = [(is_applied_last, dt_last - self.slice_start), ]
        for is_applied_current, timestamp in timings:
            if is_applied_last != is_applied_current:
                dt_current = CNVRT(timestamp)
                uptime.append((is_applied_current, dt_current - dt_last))
                dt_last, is_applied_last = dt_current, is_applied_current
        uptime.append((not is_applied_last, self.slice_end - dt_last))
        return [(applied, self.to_prcnt(td)) for applied, td in uptime]
        # return [(applied, self.to_prcnt(td)) for applied, td in uptime]

    def combine_spells(self, times: dict):
        return {
            spell_name: self.combine_uptime(timings)
            for spell_name, timings in times.items()
        }

    def combine_target(self, times: dict, is_player=True):
        if is_player:
            return self.combine_spells(times)
        return {
            target_guid: self.combine_spells(spells)
            for target_guid, spells in times.items()
        }

    @constants.running_time
    def main(self, filter_guid):
        casts: dict[str, dict[str, list[tuple[bool, str]]]] = {}

        buffs: dict[str, list[tuple[bool, str]]] = {}
        debuffs: dict[str, list[tuple[bool, str]]] = {}

        spells: set[str] = set()
        
        for line in self.logs:
            if filter_guid not in line: continue
            if 'BUFF' not in line: continue
            if 'DISPEL' in line: continue
                
            timestamp, flag, source_guid, _, target_guid, _, spell_id, _, _, buff, *_ = line.split(',', 11)
            spell_id = int(spell_id)
            z = (flag == 'SPELL_AURA_REMOVED', timestamp)
            if target_guid == filter_guid:
                if buff == 'BUFF':
                    buffs.setdefault(spell_id, []).append(z)
                else:
                    debuffs.setdefault(spell_id, []).append(z)
                spells.add(spell_id)
            elif source_guid == filter_guid and buff == 'DEBUFF':
                casts.setdefault(target_guid, {}).setdefault(spell_id, []).append(z)
                spells.add(spell_id)
        
        casts = self.combine_target(casts, is_player=False)
        buffs = self.combine_target(buffs)
        debuffs = self.combine_target(debuffs)
        buffs_uptime = {}
        for spell_id, data in buffs.items():
            s = sum(y for x,y in data if x)
            buffs_uptime[spell_id] = f"{s:.2f}"

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