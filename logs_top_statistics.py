import numpy

from constants import (
    SPECS_LIST,
    CLASSES, 
    running_time,
    convert_to_html_name,
)

CLASSES_LIST = list(CLASSES)
IGNORED_SPECS = set([*range(0, 40, 4), 7, 17, 18, 21, 22, 31, 39])

def get_spec_data(spec_index):
    spec, icon = SPECS_LIST[spec_index]
    _class = CLASSES_LIST[spec_index//4]
    return {
        "class_name": _class,
        "class_html": convert_to_html_name(_class),
        "spec_name": spec,
        "spec_html": convert_to_html_name(f"{_class} {spec}"),
        "icon": icon,
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
    _percentile = round(numpy.percentile(data, percentile), 2)
    return {
        "p": _percentile,
        "n": n_greater_than(data, _percentile),
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
