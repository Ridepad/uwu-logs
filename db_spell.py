import constants
from multiprocessing import Pool
import os
import _main
import json

@constants.running_time
def main(logs):
    _spells = {}
    for line in logs:
        if ",SPELL_" not in line:
            continue
        q = line.split(',')
        _spells.setdefault(q[2], set()).add(q[6])
    return _spells

def __do(name):
    print(name)
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    _spells = main(logs)
    with open(f"./spells_json/{name}.json", 'w') as f:
        json.dump(_spells, f, default=list)

def __do_all():
    folders = next(os.walk('./LogsDir/'))[1][8:]
    with Pool(8) as p:
        p.map(__do, folders)

def combineshit():
    files = next(os.walk('./spells_json/'))[2]
    _all = {}
    for filename in files:
        with open(f"./spells_json/{filename}", 'r') as f:
            q = json.load(f)
        for x,y in q.items():
            if x[:4] == "0x06":
                _all.setdefault(x, set()).update(y)

    with open("ULTIMATE_SPELLS.json", 'w') as f:
        json.dump(_all, f, default=list)
if __name__ == '__main__':
    __do_all()
    combineshit()