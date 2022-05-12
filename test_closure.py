from datetime import datetime
import re
from time import perf_counter

def running_time(f):
    def inner(*args, **kwargs):
        st = perf_counter()
        q = f(*args, **kwargs)
        fin = int((perf_counter() - st) * 1000)
        print(f'[PERF]: Done in {fin:>6,} ms with {f.__module__}.{f.__name__}')
        return q
    return inner

def get_now():
    return datetime.now()

def to_dt():
    Z = re.compile('(\d{1,2})/(\d{1,2}) (\d\d):(\d\d):(\d\d).(\d\d\d)')
    current = get_now()
    year = current.year
    month = current.month
    day = current.day
    def inner(s: str):
        q = list(map(int, Z.findall(s)[0]))
        q[-1] *= 1000
        if q[0] > month or q[0] == month and q[1] > day:
            return datetime(year-1, *q)
        return datetime(year, *q)
    return inner

def to_dt2():
    Z = re.compile('(\d+)')
    current = get_now()
    year = current.year
    month = current.month
    day = current.day
    def inner(s: str):
        q = list(map(int, Z.findall(s, endpos=18)))
        q[-1] *= 1000
        if q[0] > month or q[0] == month and q[1] > day:
            return datetime(year-1, *q)
        return datetime(year, *q)
    return inner


line1 = '''12/12 21:17:38.668  SPELL_PERIODIC_LEECH,0x06000000003C109F,"Nolfein",0x514,0xF13000943D000253,"Cult Adherent",0xa48,3034,"Viper Sting",0x8,502,0,1506'''
line1 = '''5/6 21:17:38.668  SPELL_PERIODIC_LEECH,0x06000000003C109F,"Nolfein",0x514,0xF13000943D000253,"Cult Adherent",0xa48,3034,"Viper Sting",0x8,502,0,1506'''

# dt = to_dt()
# dt2 = to_dt2()
# print(dt(line1))
# print(dt2(line1))

CYCLES = 10**6

@running_time
def test1():
    dt = to_dt3()
    print(dt(line1))
    for _ in range(CYCLES):
        dt(line1)

@running_time
def test2():
    dt = to_dt2()
    print(dt(line1))
    for _ in range(CYCLES):
        dt(line1)

for _ in range(5):
    test1()
for _ in range(5):
    test2()