import cut_logs
import constants
import re
from datetime import timedelta, datetime

TD = timedelta(0)

def _open(name):
    with open(name) as f:
        return f.read().splitlines()

def werujiefuji(line):
    return line.split(',', 1)

def do(name):
    q = _open(name)
    q = sorted(q)
    q = [werujiefuji(x) for x in q]
    return list(zip(*q))

def get_now():
    return datetime.today()

CURRENT_YEAR = get_now().year
Z = re.compile('(\d{1,2})/(\d{1,2}) (\d\d):(\d\d):(\d\d).(\d\d\d)')
def to_dt(s: str):
    q = list(map(int, Z.findall(s)[0]))
    q[-1] *= 1000
    return datetime(CURRENT_YEAR, *q)

def get_time_delta(s: str, f: str):
    return to_dt(f) - to_dt(s)

@constants.running_time
def main():
    times1, lines1 = do("Log1_cut.txt")
    times2, lines2 = do("Log2_cut.txt")
    times_2, lines_2 = times2[::1], lines2[::1]
    lines1 = lines1[:1000]
    n2 = 0
    for n1, x in enumerate(lines1):
        try:
            n2 = n2 + lines2[n2:].index(x)
        except ValueError:
            n2 = n2 - lines_2[-n2+1:].index(x)
            # n2 = n2 - lines2[:n2][::-1].index(x)
        d = get_time_delta(times2[n2], times1[n1])
        if d > TD:
            print(n1, n2)
            print(d)

main()