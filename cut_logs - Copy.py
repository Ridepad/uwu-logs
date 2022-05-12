from datetime import datetime, timedelta
import pickle
from time import time as tm
import re
import constants

def logs_read(logs_path):
    with open(logs_path, 'r') as f:
        return f.read()
# SPELL_CAST_FAILED 
# SPELL_AURA 48942,"Devotion Aura",0x2,BUFF
# 5/7 21:32:59.002  SPELL_DAMAGE,0x0600000000307023,"Bluehood",0x514,0xF13000966C00043B,"Blood Beast",0x100a48,56488,"Global Thermal Sapper Charge",0x4,146,0,4,16,0,0,nil,nil,nil


# q = list(map(int, Z.match(s).groups()))
# S = re.compile('[/:. ]')
# q = list(map(int, S.split(s)))
# Q = re.compile('\d{1,3}')
# q = list(map(int, Q.findall(s)))
# q = list(map(int, re.findall('\d{1,3}', s)))

Z = re.compile('(\d{1,2})/(\d\d) (\d\d):(\d\d):(\d\d).(\d\d\d)')
def conv_to_dt1(s):
    q = list(map(int, Z.findall(s)[0]))
    return datetime(2021, *q)

LINE_SEPARATOR = constants.LINE_SEPARATOR

st = tm()
logs = constants.logs_read(constants.LOGS_NAME)
print(f'{tm() - st:.2f} logs_read')
st = tm()
logs = logs.replace('"', '')
print(f'{tm() - st:.2f} replace "')
st = tm()
logs = logs.replace('  ', ',')
print(f'{tm() - st:.2f} replace ,')
st = tm()
logs = logs.splitlines()
print(f'{tm() - st:.2f} splitlines')

def main(logs):
    open(constants.LOGS_NAME_CUT, 'w').close()
    with open(constants.LOGS_NAME_CUT, 'a+') as f:
        st = tm()
        w = f.write
        for line in logs:
            # time, line = line.split('  ')
            # time1 = conv_to_dt1(time)
            line = line.split(',')
            if line[0].endswith('SPELL_CAST_FAILED'):
                continue
            line.pop(6)
            line.pop(3)
            # w(time)
            # w('#')
            line = ','.join(line)
            w(f'{line}{LINE_SEPARATOR}')
            # w(LINE_SEPARATOR)
            # line = [line[0], line[1], line[2], line[4], line[5], line[7:]]
            # z.setdefault(time, []).append(line)
        # print(f'{tm() - st:.2f} main')
        # with open('parsed_logs', 'w') as f:
        #     pickle.dump(z, f)
        print(f'{tm() - st:.2f} main')

def main1(logs):
    st = tm()
    z = []
    for line in logs:
        line = line.split(',')
        if line[1] == 'SPELL_CAST_FAILED':
            continue
        del line[7]
        del line[4]
        z.append(','.join(line))
    # print(f'{tm() - st:.2f} main11')
    with open(constants.LOGS_NAME_CUT, 'w') as f:
        f.write(LINE_SEPARATOR.join(z))
    print(f'{tm() - st:.2f} main1')

def genkek(logs):
    for line in logs:
        line = line.split(',')
        if line[1] == 'SPELL_CAST_FAILED':
            continue
        del line[7]
        del line[4]
        yield ','.join(line)
def main2(logs):
    st = tm()
    # z = []
    # for line in logs:
    #     line = line.split(',')
    #     if line[1] == 'SPELL_CAST_FAILED':
    #         continue
    #     del line[7]
    #     del line[4]
    #     z.append(','.join(line))
    # print(f'{tm() - st:.2f} main1')
    z = genkek(logs)
    with open(constants.LOGS_NAME_CUT, 'w') as f:
        f.write(LINE_SEPARATOR.join(z))
        # f.write(LINE_SEPARATOR.join(iter(genkek(logs))))
    print(f'{tm() - st:.2f} main2')
    
main2(logs)
main1(logs)
main2(logs)
main1(logs)
main2(logs)
main1(logs)