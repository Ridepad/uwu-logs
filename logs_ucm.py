from collections import defaultdict
from typing import TypedDict

import logs_base
from h_debug import running_time
from h_other import (
    separate_thousands,
    separate_thousands_dict,
    sort_dict_by_value,
)

# 1/19 21:49:03.234,SPELL_AURA_APPLIED_DOSE,0x0600000000526D6E,Keppori,0x0600000000526D6E,Keppori,69766,Instability,0x40,DEBUFF,8
# 1/19 21:49:08.266,SPELL_AURA_REMOVED,0x0600000000526D6E,Keppori,0x0600000000526D6E,Keppori,69766,Instability,0x40,DEBUFF
# 1/19 21:49:08.269,SPELL_DAMAGE,0x0600000000526D6E,Keppori,0x0600000000526D6E,Keppori,71046,Backlash,0x40,22349,0,64,5587,0,0,nil,nil,nil

class ParsedUCM(TypedDict):
    dmg: defaultdict[str, list[str, str, list]]
    stacks: defaultdict[str, list[str, str, str]]


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
def parse_ucm(logs_slice: list[str]) -> ParsedUCM:
    stacks = defaultdict(list)
    for line in logs_slice:
        if "69766" not in line:
            continue
        try:
            t, flag, _, _, target_guid, _, *spell = line.split(',')
            stacks[target_guid].append((t, flag, spell[-1]))
        except:
            pass
    
    dmg = parse_ucm_damage(logs_slice)
    if not dmg:
        dmg = parse_ucm_damage(logs_slice, spell_id="71045")

    return {
        "dmg": dmg,
        "stacks": stacks,
    }

def count_dmg(dmg_events: list):
    line: list[str]
    pets = defaultdict(int)
    full = defaultdict(int)
    prevented = defaultdict(int)
    actual = defaultdict(int)
    overkill = defaultdict(int)
    for _, target, line in dmg_events:
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

def stacks_events_to_dict(stacks_events: list[list[str]]):
    stacks: dict[str, int] = {}
    for event_now, event_next in zip(stacks_events, stacks_events[1:]):
        if event_next[1] != "SPELL_AURA_REMOVED":
            continue
        if event_now[1] == "SPELL_AURA_REMOVED":
            continue
        stacks[event_next[0]] = stacks_to_int(event_now[-1])
    return stacks

def get_sindra_guid(guids):
    for guid in guids:
        if guid[6:12] == "008FF5":
            return guid
    return None

def format_damage(dmg_events):
    damage = count_dmg(dmg_events)
    explosion = {}
    for damage_type, damage_done in damage.items():
        explosion[f"{damage_type}_total"] = separate_thousands(sum(damage_done.values()))
        explosion[damage_type] = separate_thousands_dict(sort_dict_by_value(damage_done))
    
    explosion["players_hit"] = len(damage["actual"])
    return explosion


class UCM(logs_base.THE_LOGS):
    def stacks_before_explosion(self, t1, stacks):
        for t2, _stacks in stacks.items():
            dt = abs(self.get_timedelta(t2, t1)).total_seconds()
            if dt < 4:
                return _stacks
        return 0
    
    def explostions_after_removed(self, t1, dmg):
        for t2, dmg_events in dmg.items():
            
            dt = self.get_timedelta(t1, t2).total_seconds()
            if dt >= 0 and dt < 0.2:
                return dmg_events
        return {}

    def group_explosions(self, x: list[tuple[str]], window_sec=1):
        groupped = []
        t_prev = x[0][0]
        qqq = []
        groupped.append(qqq)
        for q in x:
            t_now = q[0]
            d = self.get_timedelta(t_prev, t_now).total_seconds()
            if d > window_sec:
                qqq = []
                groupped.append(qqq)
            t_prev = t_now
            qqq.append(q)
        
        return {
            group[0][0]: group
            for group in groupped
        }

    def parse_slice_sindra_source(self, _ucm: ParsedUCM, _start):
        sindra_guid = get_sindra_guid(_ucm["dmg"])
        if not sindra_guid:
            return []

        all_dmg = self.group_explosions(_ucm["dmg"][sindra_guid], 0.05)

        explosions = []
        for source, _stacks_events in _ucm["stacks"].items():
            stacks_groupped = stacks_events_to_dict(_stacks_events)
            for timestamp, _stacks in stacks_groupped.items():
                dmg_events = self.explostions_after_removed(timestamp, all_dmg)
                if not dmg_events:
                    continue
                explosion = format_damage(dmg_events)
                explosion["stacks"] = _stacks
                t = self.get_timedelta(_start, timestamp).total_seconds()
                explosion["timestamp"] = sec_to_str(t)
                explosion["source"] = source
                explosions.append(explosion)
        return explosions

    @logs_base.cache_wrap
    def parse_slice(self, s, f):
        logs_slice = self.LOGS[s:f]
        _start = logs_slice[0]
        
        _ucm = parse_ucm(logs_slice)
        
        if any(guid[6:12] == "008FF5" for guid in _ucm["dmg"]):
            return self.parse_slice_sindra_source(_ucm, _start)
        
        explosions = []
        sources = sorted(set(_ucm["stacks"]) | set(_ucm["dmg"]))
        for source in sources:
            damage_events = _ucm["dmg"].get(source)
            stacks_events = _ucm["stacks"].get(source)
            if not damage_events or not stacks_events:
                continue
            
            stacks = stacks_events_to_dict(stacks_events)
            dmg = self.group_explosions(damage_events)
            for timestamp, dmg_events in dmg.items():
                if not dmg_events:
                    continue
                
                explosion = format_damage(dmg_events)
                explosion["stacks"] = self.stacks_before_explosion(timestamp, stacks)
                t = self.get_timedelta(_start, timestamp).total_seconds()
                explosion["timestamp"] = sec_to_str(t)
                explosion["source"] = source
                explosions.append(explosion)
        return explosions

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
    report = UCM("24-02-18--12-44--Qxt--Rising Gods")
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
