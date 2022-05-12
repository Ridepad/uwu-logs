from constants_WBF import DIR_PATH, get_all_files, json_read, json_write
import os

TMP_CACHE = os.path.join(DIR_PATH, "tmp_cache")

all_files = get_all_files('json', TMP_CACHE)
# print(all_files[:10])
for file in all_files:
    print(file)
    fname = os.path.join(TMP_CACHE, file)
    _data = json_read(fname)
    # print(_data)
    # input()
    json_write(fname, _data, indent=None)