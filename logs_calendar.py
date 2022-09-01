import calendar
from collections import defaultdict
from datetime import datetime

from constants import get_folders_filter

HTMLC = calendar.HTMLCalendar()


def _split3(folder_name: str):
    date, time, name, server = folder_name.split('--')
    time = time.replace('-', ':')
    report_link = f'<a href="/reports/{folder_name}/">{time} | {server} | {name}</a>'
    return date, report_link
   
def formal_cell(day_n, reports_list):
    section = [
        '',
        f'<input id="calendar-day{day_n}" class="radio" name="calendar-days" type="radio">',
        f'<label class="show-reports" for="calendar-day{day_n}">{day_n}</label>',
        '<article>',
        *reports_list,
        '</article>',
        '',
    ]
    return '\n'.join(section)

def logs_db_gen(year, month):
    _correct_month = f"{year%100:>02}-{month:>02}"
    folders = get_folders_filter()
    for folder in folders:
        if folder.count('--') < 3:
            continue
        date, _link = _split3(folder)
        _month, day = date.rsplit('-', 1)
        if _month == _correct_month:
            yield int(day), _link

def get_reports_by_month(year: int, month: int):
    new_html = HTMLC.formatmonth(year, month)
    dd = defaultdict(list)
    for day_n, _link in logs_db_gen(year, month):
        dd[day_n].append(_link)

    for day_n, reports_list in dd.items():
        section = formal_cell(day_n, reports_list)
        new_html = new_html.replace(f">{day_n}<", f">{section}<")
    
    return new_html


def new_month(page: int=0):
    dt = datetime.now()
    month = dt.month + page - 1
    return dt.year + month//12, month % 12 + 1
