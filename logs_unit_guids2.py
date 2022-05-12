from typing import List
import _main
import constants

@constants.running_time
def get_all(logs: List[str]):
    d = {}
    for line in logs:
        _, _, sguid, sname, tguid, tname, *_ = line.split(',', 6)
        d[sguid] = sname
        d[tguid] = tname
    return d


if __name__ == "__main__":
    name = "21-05-07--21-02--Nomadra"
    print(name)
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guids = get_all(logs)
    assert "0x0600000000311347" in guids
