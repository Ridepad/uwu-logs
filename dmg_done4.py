from typing import Dict, List

import _main
import constants
from time import time as tm

from numba import jit, cuda

# def get_all_targets_gen(logs: List[str]):
#     for line in logs:
#         # if ',0xF1' not in line:
#             # continue
#         yield line

@jit
def get_all(logs):
    s: Dict[str, Dict[str, int]] = {}
    for line in logs:
        if "_DAMAG" not in line:
            continue
        _, _, sguid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
        q = s.setdefault(sguid, {})
        tguid = tguid[:-6]
        q[tguid] = q.get(tguid, 0) + int(d) - int(ok)
    return s

def __main():

    name = '21-10-08--20-57--Nomadra'
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guids = report.get_all_guids()
    enc_data = report.get_enc_data()
    st = tm()
    get_all(logs)
    print(tm()-st)
    # get_all(logs)
    # get_all(logs)
    # get_all(logs)
    # get_all(logs)
    # get_all(logs)
    # get_all(logs)
    # get_all(logs)

def valid_npc(guid):
    if "0xF14" in guid:
        return
    if "004CD4" in guid:
        return
    if "006CB5" in guid:
        return
    if "0007AC" in guid:
        return
    if "0079F0" in guid:
        return
    if "005E8F" in guid:
        return
    if "002284" in guid:
        return
    if "003C4E" in guid:
        return
    if "004DD1" in guid:
        return
    if "004D79" in guid:
        return
    return True


@constants.running_time
def get_all2(logs):
    gen = get_all_targets_gen(logs)
    s = set()
    for line in gen:
        _, _, sguid, _, tguid, _, _, _, _, d, ok, _ = line.split(',', 11)
        # sguid = line[4][:-6]
        if '0xF1' in tguid:
            s.add(tguid[:-6])
    return s

def __main2():

    name = '21-10-08--20-57--Nomadra'
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guids = report.get_all_guids()
    enc_data = report.get_enc_data()
    a = {}
    for name, v in enc_data.items():
        z = set()
        for s,f in v:
            logs_slice = logs[s:f]
            q = get_all2(logs_slice)
            z.update(q)
        z = {x for x in z if valid_npc(x)}
        a[name] = z
    print(a)


if __name__ == "__main__":
    __main()
