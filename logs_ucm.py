from collections import defaultdict
from constants import (
    running_time,
    separate_thousands,
    separate_thousands_dict,
    sort_dict_by_value,
)

import logs_base

# 1/19 21:49:03.234,SPELL_AURA_APPLIED_DOSE,0x0600000000526D6E,Keppori,0x0600000000526D6E,Keppori,69766,Instability,0x40,DEBUFF,8
# 1/19 21:49:08.266,SPELL_AURA_REMOVED,0x0600000000526D6E,Keppori,0x0600000000526D6E,Keppori,69766,Instability,0x40,DEBUFF
# 1/19 21:49:08.269,SPELL_DAMAGE,0x0600000000526D6E,Keppori,0x0600000000526D6E,Keppori,71046,Backlash,0x40,22349,0,64,5587,0,0,nil,nil,nil


def sec_to_str(s: float):
    return f"{int(s/60)}:{int(s%60):>02}.{int(s*10%10)}"

def parse_ucm_damage(logs_slice: list[str], spell_id="71046"):
    dmg = defaultdict(list)
    for line in logs_slice:
        if spell_id not in line:
            continue
        try:
            t, _, source_guid, _, target_guid, _, *spell = line.split(',')
            dmg[source_guid].append((t, target_guid, spell[3:9]))
        except:
            pass
    return dmg

@running_time
def parse_ucm(logs_slice: list[str]):
    stacks = defaultdict(list)
    for line in logs_slice:
        if "69766" not in line:
            continue
        try:
            t, flag, source_guid, _, _, _, *spell = line.split(',')
            stacks[source_guid].append((t, flag, spell[-1]))
        except:
            pass
    
    dmg = parse_ucm_damage(logs_slice)
    if not dmg:
        dmg = parse_ucm_damage(logs_slice, spell_id="71045")

    return {
        "dmg": dmg,
        "stacks": stacks,
    }

def count_dmg(a:list):
    line: list[str]
    pets = defaultdict(int)
    full = defaultdict(int)
    prevented = defaultdict(int)
    actual = defaultdict(int)
    overkill = defaultdict(int)
    for _, target, line in a:
        is_pet = target[:3] != "0x0"
        if is_pet:
            try:
                pets[target] += int(line[0])
            except:
                pass
            continue

        try:
            s_hit, s_overkill, _, s_absorb, _, s_resist = line
            _hit = int(s_hit)

            full[target] += _hit
            if s_overkill == "0":
                actual[target] += _hit
            else:
                _overkill = int(s_overkill)
                overkill[target] += _overkill
                actual[target] += _hit - _overkill
            
            if s_absorb != "0":
                _absorb = int(s_absorb)
                full[target] += _absorb
                prevented[target] += _absorb
            
            if s_resist != "0":
                _resist = int(s_resist)
                full[target] += _resist
                prevented[target] += _resist

        except ValueError:
            try:
                prevented[target] += int(line[1])
            except (IndexError, ValueError):
                pass
    

    return {
        "pets": pets,
        "full": full,
        "actual": actual,
        "prevented": prevented,
        "overkill": overkill,
    }

def stacks_to_int(s):
    try:
        return int(s)
    except:
        return 1

def get_stacks(a: list):
    stacks = {}
    for q, w in zip(a, a[1:]):
        if w[1] != "SPELL_AURA_REMOVED":
            continue
        if q[1] == "SPELL_AURA_REMOVED":
            continue
        stacks[w[0]] = stacks_to_int(q[-1])
    return stacks


class UCM(logs_base.THE_LOGS):
    def find_same_time_stacks_drop(self, t1, stacks):
        for t2, _stacks in list(stacks.items()):
            dt = abs(self.get_timedelta(t2, t1)).total_seconds()
            if dt < 4:
                return _stacks
        return 0

    def group_explosions(self, x: list[tuple[str]]):
        groupped = []
        t_prev = x[0][0]
        qqq = []
        groupped.append(qqq)
        for q in x:
            t_now = q[0]
            d = self.get_timedelta(t_prev, t_now).total_seconds()
            if d > 1:
                qqq = []
                groupped.append(qqq)
            t_prev = t_now
            qqq.append(q)
        
        return {
            group[0][0]: group
            for group in groupped
        }

    @logs_base.cache_wrap
    def parse_slice(self, s, f):
        logs_slice = self.LOGS[s:f]
        _start = logs_slice[0]
        
        _ucm = parse_ucm(logs_slice)
        
        times = []
        sources = sorted(set(_ucm["stacks"]) | set(_ucm["dmg"]))
        for source in sources:
            dmg = _ucm["dmg"].get(source, [])
            if not dmg:
                continue
            dmg = self.group_explosions(dmg)
            stacks = _ucm["stacks"].get(source, {})
            stacks = get_stacks(stacks)
            for t1, _dmg_dict in dmg.items():
                explosion = {}
                _dmg = count_dmg(_dmg_dict)
                for q, w in _dmg.items():
                    explosion[f"{q}_total"] = separate_thousands(sum(w.values()))
                    explosion[q] = separate_thousands_dict(sort_dict_by_value(w))
                explosion["players_hit"] = len(explosion["actual"])
                explosion["stacks"] = self.find_same_time_stacks_drop(t1, stacks)
                t = self.get_timedelta(_start, t1).total_seconds()
                explosion['timestamp'] = sec_to_str(t)
                explosion['source'] = source
                times.append(explosion)
        return times

    def parse_ucm_wrap(self, segments):
        z = []
        for s, f in segments:
            q = self.parse_slice(s, f)
            q = sorted(q, key=lambda x: x["timestamp"])
            z.append(q)
        specs = self.get_slice_spec_info(*segments[0])
        return {
            "UCM": z,
            "SPECS": specs,
            "guid_to_name": self.guid_to_name,
        }

def test1():
    report = UCM("24-02-09--20-49--Meownya--Lordaeron")
    encdata = report.get_enc_data()
    report.LOGS
    for s, f in encdata["Sindragosa"][-1:]:
        a = report.parse_slice(s, f)
        for x in a:
            print()
            print(x)
        break


if __name__ == "__main__":
    test1()
