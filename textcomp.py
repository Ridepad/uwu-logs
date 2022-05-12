import base64
import os
import zlib
import lzma
import gzip
import bz2

from time import perf_counter as tt

import constants

def __compress(s: str, f):
    e = s.encode()
    st = tt()
    z = f.compress(e)
    print(f"{tt() - st:4f} compress")
    st = tt()
    t = base64.b64encode(z)
    print(f"{tt() - st:4f} base64.b64encode")
    return t

def __decompress(s, f):
    st = tt()
    dt = base64.b64decode(s)
    print(f"{tt() - st:4f} base64.b64decode")
    st = tt()
    dz = f.decompress(dt)
    print(f"{tt() - st:4f} decompress")
    return dz

def __decompress_gzip(s):
    st = tt()
    dt = base64.b64decode(s)
    print(f"{tt() - st:4f} base64.b64decode")
    st = tt()
    dz = gzip.decompress(dt)
    print(f"{tt() - st:4f} gzip.decompress")
    return dz

def main2():
    name = "LogsDir/22-02-09--21-04--Safiyah"
    data_raw = constants.file_read(f"{name}/Logs_cut.txt")
    data = data_raw.encode()
    for x in [gzip, zlib]:
        print()
        print(x)
        t = __compress(logs_raw, x)
        print(f'SIZE: {len(t):_}')
        __decompress(t, x)

def test_zlib(data, level):
    st = tt()
    dt = zlib.compress(data, level=level)
    print(f"{tt() - st:.4f} compress")
    st = tt()
    t = base64.b64encode(dt)
    print(f"{tt() - st:.4f} b64encode")
    l1 = len(dt) / 1024 / 1024
    l2 = len(t) / 1024 / 1024
    print(f'SIZE1: {l1:.2f}mb | {l2:.2f}mb')
    st = tt()
    dz = zlib.decompress(dt)
    print(f"{tt() - st:.4f} decompress")
    print('SIZE2:', len(data) == len(dz))

def test_gzip(data, level):
    st = tt()
    dt = gzip.compress(data, compresslevel=level)
    print(f"{tt() - st:.4f} compress")
    st = tt()
    t = base64.b64encode(dt)
    print(f"{tt() - st:.4f} b64encode")
    l1 = len(dt) / 1024 / 1024
    l2 = len(t) / 1024 / 1024
    print(f'SIZE1: {l1:.2f}mb | {l2:.2f}mb')
    st = tt()
    dz = gzip.decompress(dt)
    print(f"{tt() - st:.4f} decompress")
    print('SIZE2:', len(data) == len(dz))

def main3():
    name = "LogsDir/22-02-09--21-04--Safiyah"
    data_raw = constants.file_read(f"{name}/Logs_cut.txt")
    data = data_raw.encode()
    # l0 = len(data) / 1024 / 1024
    for level in range(-1, 10):
        print("LEVEL:", level)
        test_gzip(data, level)
        # l3 = len(dz) / 1024 / 1024
        # print(f'SIZE2: {l0:.2f}mb | {l3:.2f}mb')

@constants.running_time
def _compress(data):
    return zlib.compress(data, level=7)

@constants.running_time
def _decompress(data):
    return zlib.decompress(data)

@constants.running_time
def main():
    name = "LogsDir/22-02-09--21-04--Safiyah"
    data_raw = constants.file_read(f"{name}/Logs_cut.txt")
    data = data_raw.encode()
    t = _compress(data)
    with open(f"{name}/tst3.txt", 'wb') as f:
        f.write(t)

@constants.running_time
def _read(name):
    with open(name, 'rb') as f:
        return f.read()

@constants.running_time
def _read2(name):
    with open(name, 'r') as f:
        return f.read()


@constants.running_time
def test1(name):
    data = _read(name)
    dz = _decompress(data)
    return dz.decode()


@constants.running_time
def test2(name):
    return _read2(name)


def main2():
    data = _read(name)
    dz = _decompress(data)
    dz = dz.decode()
    logs = dz.splitlines()
    # print(len(dz) / 1024 / 1024)

def __redo(name):
    print(name)
    file_name = f"LogsDir/{name}/Logs_cut.txt"
    if not os.path.exists(file_name):
        return
    data_raw = constants.file_read(file_name)
    enc = data_raw.encode()
    logs_comp = zlib.compress(enc, level=7)
    with open(f"LogsDir/{name}/{constants.LOGS_CUT_NAME}", 'wb') as f:
        f.write(logs_comp)


# def __redo(name):
#     print(name)
#     c = os.path.join(LOGS_DIR, name)
#     file_name = os.path.join(c, "LOGS_CUT")
#     file_name2 = os.path.join(c, "LOGS_CUT.pyzlib")
#     os.rename(file_name, file_name2)

def __redo_all():
    import os
    from multiprocessing import Pool
    folders = next(os.walk('LogsDir'))[1]
    with Pool(4) as p:
        p.map(__redo, folders)

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
LOGS_DIR = os.path.join(DIR_PATH, "LogsDir")

if __name__ == '__main__':
    # q = os.getcwd()
    # print(q)
    # __redo("22-02-12--21-14--Nomadra")
    __redo_all()

# name = "LogsDir/22-02-09--21-04--Safiyah/tst1.txt"
# q1 = test1(name)
# name = "LogsDir/22-02-09--21-04--Safiyah/Logs_cut.txt"
# q2 = test2(name)
# print(q1==q2)