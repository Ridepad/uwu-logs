from typing import List
import _main

from multiprocessing import Pool
import os

ALL_SHIT = set()

def check_spirits(logs: List[str]):
    for line in logs:
        if "00954E" in line and "71426" not in line:
            q = line.split(',')
            # if q[7] == "Vengeful Blast":
                # continue
            ALL_SHIT.add((q[1], q[6], q[7]))
            # print(f"{q[1]:<25} {q[3]:>12} {q[5]:>12} {q[6]:>7} {q[7]}")
    print(ALL_SHIT)

def redo(name):
    print(name)
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    check_spirits(logs)

folders = next(os.walk('./LogsDir/'))[1]
# i = folders.index('21-08-10--18-31--Inia')
# folders = folders[i:]
for x in folders:
    redo(x)
# with Pool(8) as p:
#     p.map(redo, folders)
print(ALL_SHIT)
print('done')