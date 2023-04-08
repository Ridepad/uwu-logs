import json
import os
import file_functions
import gzip
import numpy
from datetime import datetime, timedelta
from constants import SPECS_LIST, TOP_DIR, CLASSES, running_time
CLASSES_LIST = list(CLASSES)

ONE_HOUR = timedelta(hours=1)
DATA_CACHE = {}
DATA_CACHE_RENEW = {}

def get_boss_top_file(server: str=None, boss: str=None, mode: str=None):
    if not server:
        server = "Lordaeron"
    if not boss:
        boss = "The Lich King"
    if not mode:
        mode = "25H"

    server_folder = os.path.join(TOP_DIR, server)
    return os.path.join(server_folder, f"{boss} {mode}.gzip")

@running_time
def get_boss_data(server: str=None, boss: str=None, mode: str=None):
    boss_file = get_boss_top_file(server, boss, mode)
    if (
        boss_file in DATA_CACHE
    and boss_file in DATA_CACHE_RENEW
    and DATA_CACHE_RENEW[boss_file] > datetime.now()
    ):
        return DATA_CACHE[boss_file]

    data = _get_boss_data(boss_file)
    data = json.dumps(data)
    DATA_CACHE[boss_file] = data
    DATA_CACHE_RENEW[boss_file] = datetime.now() + ONE_HOUR
    return data

def get_class_spec_full(spec_index):
    spec, icon = SPECS_LIST[spec_index]
    _class = CLASSES_LIST[spec_index//4]
    return f"{_class} {spec}".replace(' ', '-').lower()

SPECS_TO_HTML_LIST = [get_class_spec_full(spec_index) for spec_index in range(40)]

IGNORED_SPECS = [*range(0, 40, 4), 7, 17, 18, 21, 22, 31, 39]
SPECS_DATA: list[str] = None

def get_specs_data():
    global SPECS_DATA
    if SPECS_DATA: return SPECS_DATA
    
    SPECS_DATA = []
    for spec_index in set(range(40)) - set(IGNORED_SPECS):
        spec, icon = SPECS_LIST[spec_index]
        _class = CLASSES_LIST[spec_index//4]
        SPECS_DATA.append((_class, _class.replace(' ', '-').lower(), spec, SPECS_TO_HTML_LIST[spec_index], icon))
    return SPECS_DATA

def get_percentile(data, percentile):
    return round(numpy.percentile(data, percentile), 2)

def _get_boss_data(boss_file: str):
    if not os.path.isfile(boss_file):
        return {}
    
    data = file_functions.bytes_read(boss_file)
    data = gzip.decompress(data)
    data = json.loads(data)
    
    new_data = {}
    for spec_index in range(40):
        if spec_index in IGNORED_SPECS:
            continue
        data_s = numpy.fromiter((x["ud"] for x in data if x["s"] == spec_index), float)
        if len(data_s) < 10:
            continue
        data_s = numpy.sort(data_s)
        new_data[SPECS_TO_HTML_LIST[spec_index]] = {
            "max": max(data_s),
            "p99": get_percentile(data_s, 99),
            "p75": get_percentile(data_s, 75),
            "p50": get_percentile(data_s, 50),
            "p10": get_percentile(data_s, 10),
        }
    return new_data

if __name__ == "__main__":
    get_boss_data()
