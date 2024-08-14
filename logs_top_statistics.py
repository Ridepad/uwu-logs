import numpy

from c_player_classes import CLASSES, SPECS_LIST
from h_other import convert_to_html_name
from h_debug import running_time

CLASSES_LIST = list(CLASSES)
IGNORED_SPECS = set([*range(0, 40, 4), 7, 17, 18, 21, 22, 31, 39])

def get_spec_data(spec_index: int):
    _spec_info = SPECS_LIST[spec_index]
    _class = CLASSES_LIST[spec_index//4]
    return {
        "class_name": _class,
        "class_html": convert_to_html_name(_class),
        "spec_name": _spec_info.name,
        "spec_html": _spec_info.html_name,
        "icon": _spec_info.icon,
    }

SPECS_DATA = [
    get_spec_data(spec_index)
    for spec_index in range(40)
]

SPECS_DATA_NOT_IGNORED = [
    data
    for spec_index, data in enumerate(SPECS_DATA)
    if spec_index not in IGNORED_SPECS
]


def n_greater_than(data: numpy.ndarray, value: float):
    return int((data > value).sum())

def get_percentile(data, percentile):
    if percentile == 100:
        v = max(data)
        n = 1
    elif percentile == 0:
        v = 0
        n = len(data)
    else:
        v = round(numpy.percentile(data, percentile), 2)
        n = n_greater_than(data, v)
    
    return {
        "v": v,
        "n": n,
    }

@running_time
def convert_boss_data(data: dict[int, list[float]]):
    BOSS_DATA = {}
    for spec_index, values in data.items():
        if spec_index in IGNORED_SPECS:
            continue
        if len(values) < 5:
            continue
        
        data_s = numpy.fromiter(values, dtype=numpy.float64)
        spec_html = SPECS_DATA[spec_index]["spec_html"]
        BOSS_DATA[spec_html] = {
            "top100": get_percentile(data_s, 100),
            "top99": get_percentile(data_s, 99),
            "top95": get_percentile(data_s, 95),
            "top90": get_percentile(data_s, 90),
            "top75": get_percentile(data_s, 75),
            "top50": get_percentile(data_s, 50),
            "top10": get_percentile(data_s, 10),
            "all": get_percentile(data_s, 0),
        }
    return BOSS_DATA
