import time
import requests

NIL_GUID = '0x0000000000000000'
REPORT_NAME_STRUCTURE = ("date", "time", "author", "server")


class Ports(dict[str, int]):
    __getattr__ = dict.get
    
    main = 5000
    upload = 5010
    top = 5020


def requests_get(page_url, headers, timeout=2, attempts=3):
    for _ in range(attempts):
        try:
            page = requests.get(page_url, headers=headers, timeout=timeout, allow_redirects=False)
            if page.status_code == 200:
                return page
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            time.sleep(2)
    
    return None

def get_report_name_info(report_id: str):
    _report_id = report_id.split('--')
    while len(_report_id) < len(REPORT_NAME_STRUCTURE):
        _report_id.append("")
    return dict(zip(REPORT_NAME_STRUCTURE, _report_id))

def sort_dict_by_value(d: dict):
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=True))

def is_player(guid: str):
    return guid.startswith('0x0') and guid != NIL_GUID

def convert_to_html_name(name: str):
    return name.lower().replace(' ', '-').replace("'", '')

def separate_thousands(num, precision=None):
    try:
        num + 0
    except TypeError:
        return ""
    
    if not num:
        return ""
    
    if precision is None:
        precision = 1 if isinstance(num, float) else 0
    
    return f"{num:,.{precision}f}".replace(',', ' ')

def separate_thousands_dict(data: dict):
    return {
        k: separate_thousands(v)
        for k, v in data.items()
    }

def add_new_numeric_data(data_total: dict, data_new: dict[str, int]):
    for source, amount in data_new.items():
        data_total[source] += amount
