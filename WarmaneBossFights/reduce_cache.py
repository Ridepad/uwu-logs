import zlib
import json
import constants_WBF
import base64
import pickle
import pandas

def print_compressed(data_raw, data_cmp):
    len_raw = len(data_raw)/1024/1024
    len_cmp = len(data_cmp)/1024/1024
    print(f"{len_raw:>6.3f}mb > {len_cmp:>6.3f}mb, ratio: {len_cmp/len_raw*100:>5.2f}%")

@constants_WBF.running_time
def read_raw(path):
    with open(path, 'r') as f:
        return f.read()

@constants_WBF.running_time
def zlib_json_read():
    with open("achi_dump/__main_cache_7.zlib", 'rb') as f:
        data = f.read()
    data = zlib.decompress(data).decode()
    return json.loads(data)

def main():
    PATH = "achi_dump/__main_cache.json"
    # data_full_raw = read_raw(PATH)
    # data_full_enc = data_full_raw.encode()
    # data_full_comp = constants_WBF.__compress(data_full_enc, 7)
    # print_compressed(data_full_raw, data_full_comp)
    dict_after_zlib_json = zlib_json_read()


    data_json = constants_WBF.json_read(PATH)
    # data_pickle_comp = constants_WBF.zlib_pickle_make(data_json)
    # print_compressed(data_full_raw, data_pickle_comp)

    comp_path = "achi_dump/__main_cache.pickle.zlib"
    # with open(comp_path, 'wb') as f:
    #     f.write(data_pickle_comp)

    dict_after_zlib_pickle = constants_WBF.zlib_pickle_read(comp_path)
    print(data_json == dict_after_zlib_json)
    print(data_json == dict_after_zlib_pickle)
    print(type(data_json))
    print(type(dict_after_zlib_json))
    print(type(dict_after_zlib_pickle))
    # print(data_json == dict_after)
    # with open('achi_dump/__main_cache.pickle', 'wb') as f:
    #     pickle.dump(data, f)
    # for x in range(5,8):
    #     data_comp = constants_WBF.__compress(data_enc, x)
    #     print("level:", x, "size:", f"{len(data_comp)/1024/1024:>5.2f}mb")
    #     path = f'achi_dump/__main_cache_{x}.zlib'
    #     with open(path, 'wb') as f:
    #         f.write(data_comp)
    #     constants_WBF.zlib_read(path)

@constants_WBF.running_time
def read_pandas_pickle(name):
    return pandas.read_pickle(name)

def main():
    db_date_pickle_path = "kill_db_date/data_kills_22-01.pickle"
    db_pickle = read_pandas_pickle(db_date_pickle_path)
    print(type(db_pickle))

main()