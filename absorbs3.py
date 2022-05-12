from typing import List
import _main
import constants
from datetime import timedelta

TD = timedelta(milliseconds=200)

ABSORB = f"{'SPELL_ABSORB':>25}"

AURAS_ABSORBS = {
    'Shadow Ward', 'Anti-Magic Shell',
    "Savage Defense", 'Sacred Shield',
    'Divine Protection',
}

def gen1(logs_slice: List[str], target):
    for line in logs_slice:
        if target not in line:
            continue
        try:
            timestamp, flag, _, sname, tguid, tname, _, spellname, _, o = line.split(',', 9)
            if target == tname or flag == "DAMAGE_SPLIT" and target == sname:
                yield timestamp, flag, sname, tguid, tname, spellname, o.split(',')
        except ValueError:
            pass

def get_disco(logs: List[str]):
    return {line.split(',', 4)[3] for line in logs if "Divine Aegis" in line}

    
def add_absorb(new_absorb: str, _spell: str, other: dict[str, int], timestamp, last_time):

    new_absorb = int(new_absorb)
    new_spell = _spell
    if "+1" in _spell:
        print(_spell)
        _spell = _spell[:-2]
        new_spell = ""
        if last_time != '':
            delta = constants.get_time_delta(last_time, timestamp)
            if TD < delta:
                _spell = ""
    
    other["Total"] = other.get("Total", 0) + new_absorb
    other[_spell] = other.get(_spell, 0) + new_absorb
    return new_spell

def new_print(timestamp, flag, sname, tname, spellname, other=""):
    print(f"{timestamp} {flag:>25} {sname:>20} {tname:>20} {spellname:>30} {other}")

@constants.running_time
def do(logs_slice: List[str], target_name):  # sourcery no-metrics
    s = set()
    crits = []
    da = [0, 0]
    pws = [0, 0]
    other = {}
    absorb_spell = ""
    last_time = ''

    discos = get_disco(logs_slice)
    _gen = gen1(logs_slice, target_name)

    print(f'{"timestamp":<18} {"flag":>25} {"sname":>20} {"tname":>20} {"spellname":>30}')

    for line in _gen:
        timestamp, flag, sname, tguid, tname, spellname, o = line
        if "AURA" in flag and '0x06' in tguid:
            s.add(spellname)
        other_str = ""
        if spellname == "Power Word: Shield":
            absorb_spell = ""
            removed = flag == "SPELL_AURA_REMOVED"
            pws[removed] += 1
        
        elif spellname == "Divine Aegis":
            removed = flag == "SPELL_AURA_REMOVED"
            da[removed] += 1
        
        elif spellname in AURAS_ABSORBS and "AURA" in flag:
            absorb_spell = spellname if flag == "SPELL_AURA_APPLIED" else spellname+"+1"
            last_time = timestamp
        
        elif sname in discos and flag == "SPELL_HEAL" and o[-1] == "1":
            t = int(o[0])+int(o[1])
            other_str = f"{t:>6}"
            crits.append(t)
        
        elif flag == "DAMAGE_SPLIT":
            other_str = f"{o[0]:>6}"
            other[spellname] = other.get(spellname, 0) + int(o[0])
            # add_absorb(o[0], spellname, other, timestamp, last_time)
        
        elif "ABSORB" in o:
            other_str = f"{o[1]:>6}"
            absorb_spell = add_absorb(o[1], absorb_spell, other, timestamp, last_time)
        
        elif "_DAMAGE" in flag and o[5] != "0":
            other_str = f"{o[5]:>6} | {o[0]:>6} {o[1]:>6} {o[3]:>6}"
            absorb_spell = add_absorb(o[5], absorb_spell, other, timestamp, last_time)
        
        else:
            continue
        
        new_print(timestamp, flag, sname, tname, spellname, other_str)

    print(s)
    da_absorb = int(sum(crits) * .3)
    return {
        "crits": crits,
        "da": da,
        "da_absorb": da_absorb,
        "pws": pws,
        "other": other,
    }
# def do(logs_slice: List[str]):
#     s = {}
#     for line in logs_slice:
#         if "BUFF" in line:
#             line_s = line.split(',')
#             s[line_s[6]] = line_s[7]
#     print(s)

def main():
    name = "21-11-14--00-05--Lismee"
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    s, f = enc_data["Festergut"][-1]
    ts = report.get_timestamp()
    s = s-200
    # f = ts[report.find_index(s, 70)]
    # s = ts[report.find_index(s, 43)]
    logs = logs[s:f]
    logs_slice = logs
    target = "Shataria"
    q = do(logs_slice, target)
    for x,y in q.items():
        print(x,y)
    return

if __name__ == "__main__":
    main()