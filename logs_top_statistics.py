import json
import os
import numpy
from constants import SPECS_LIST, TOP_DIR, CLASSES, running_time
import pandas

COMPRESSION = "zstd"
CLASSES_LIST = list(CLASSES)
SPECS_DATA: list[str] = []
IGNORED_SPECS = [*range(0, 40, 4), 7, 17, 18, 21, 22, 31, 39]

def get_class_spec_full(spec_index):
    spec, icon = SPECS_LIST[spec_index]
    _class = CLASSES_LIST[spec_index//4]
    return f"{_class} {spec}".replace(' ', '-').lower()


SPECS_TO_HTML_LIST = [
    get_class_spec_full(spec_index)
    for spec_index in range(40)
]

def get_specs_data():
    if SPECS_DATA:
        return SPECS_DATA
    
    for spec_index in set(range(40)) - set(IGNORED_SPECS):
        spec, icon = SPECS_LIST[spec_index]
        _class = CLASSES_LIST[spec_index//4]
        SPECS_DATA.append({
            "class_name": _class,
            "class_html": _class.replace(' ', '-').lower(),
            "spec_name": spec,
            "spec_html": SPECS_TO_HTML_LIST[spec_index],
            "icon": icon,
        })
    return SPECS_DATA


def get_mtime(path):
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return 0.0

def get_boss_top_file(server: str=None, boss: str=None, mode: str=None):
    if not server:
        server = "Lordaeron"
    if not boss:
        boss = "The Lich King"
    if not mode:
        mode = "25H"

    server_folder = os.path.join(TOP_DIR, server)
    return os.path.join(server_folder, f"{boss} {mode}.{COMPRESSION}")

@running_time
def _from_pickle(fname) -> pandas.DataFrame:
    return pandas.read_pickle(fname, compression=COMPRESSION)

def n_greater_than(data: numpy.ndarray, value: float):
    return int((data > value).sum())

def get_percentile(data, percentile):
    _percentile = round(numpy.percentile(data, percentile), 2)
    return {
        "p": _percentile,
        "n": n_greater_than(data, _percentile),
    }

@running_time
def _get_boss_data(df: pandas.DataFrame):
    if df.empty:
        return {}
    
    df_spec = df["s"]
    df_dps = df["u"] / df["t"]
    
    BOSS_DATA = {}
    for spec_index in range(40):
        if spec_index in IGNORED_SPECS:
            continue
        
        data_s = df_dps[df_spec == spec_index]
        if len(data_s) < 5:
            continue

        data_s = numpy.sort(data_s)
        BOSS_DATA[SPECS_TO_HTML_LIST[spec_index]] = {
            "max": {"p": max(data_s), "n": 0},
            "p99": get_percentile(data_s, 99),
            "p95": get_percentile(data_s, 95),
            "p90": get_percentile(data_s, 90),
            "p75": get_percentile(data_s, 75),
            "p50": get_percentile(data_s, 50),
            "p10": get_percentile(data_s, 10),
            "all": {"p": 0, "n": len(data_s)},
        }
    return BOSS_DATA



def get_boss_data_wrap():
    cache = {}
    last_mtime = {}
    @running_time
    def get_boss_data(server: str=None, boss: str=None, mode: str=None):
        boss_file = get_boss_top_file(server, boss, mode)
        current_mtime = get_mtime(boss_file)
        if current_mtime > last_mtime.get(boss_file, 0):
            df = _from_pickle(boss_file)
            data = _get_boss_data(df)
            data = json.dumps(data)
            cache[boss_file] = data
            print(current_mtime)
            last_mtime[boss_file] = current_mtime
        return cache[boss_file]
    
    return get_boss_data

get_boss_data = get_boss_data_wrap()
