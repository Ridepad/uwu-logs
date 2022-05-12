import calendar
import os
from collections import defaultdict
from datetime import datetime

HTMLC = calendar.HTMLCalendar()


def _split3(folder_name: str):
    date, time, name = folder_name.split('--')
    time = time.replace('-', ':')
    report_link = f'<a href="/reports/{folder_name}/">{time} - {name}</a>'
    return date, report_link
   
def formal_cell(day_n, reports_list):
    section = [
        '',
        f'<input id="day{day_n}" class="radio" name="calend-days" type="radio">',
        f'<label class="show-reports" for="day{day_n}">{day_n}</label>',
        '<section>',
        *reports_list,
        '</section>',
        '',
    ]
    return '\n'.join(section)

def logs_db_gen(year, month):
    _correct_month = f"{year%100:>02}-{month:>02}"
    folders = next(os.walk('LogsDir'))[1]
    for folder in folders:
        if '--' not in folder:
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
