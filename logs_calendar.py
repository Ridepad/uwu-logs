import calendar
from collections import defaultdict
from datetime import datetime

import file_functions
from constants import get_report_name_info, LOGS_DIR, running_time

HTMLC = calendar.HTMLCalendar()
SPLIT_TR = "<tr>"
SPLIT_TD = "<td"
   
def formal_cell(reports_list: list[str], month: int, day_n: int):
    section = [
        '',
        f'<input id="calendar-{month}-{day_n}" class="radio" name="calendar-days" type="radio">',
        f'<label for="calendar-{month}-{day_n}" class="show-reports">{day_n}</label>',
        '<aside>',
        *reports_list,
        '</aside>',
        '',
    ]
    return '\n'.join(section)

def inside_name(report_name_info: dict[str, str]):
    time = report_name_info["time"].replace('-', ':')
    return f'''{time} | {report_name_info["server"]} | {report_name_info["name"]}'''

def logs_db_gen(folders):
    for report_name in folders:
        report_name_info = get_report_name_info(report_name)
        _, day = report_name_info["date"].rsplit('-', 1)
        report_link = f'<a href="/reports/{report_name}/">{inside_name(report_name_info)}</a>'
        yield int(day), report_link

def get_reports_by_month(year: int, month: int, folders: list[str]):
    new_html = HTMLC.formatmonth(year, month)
    reports_by_day = defaultdict(list)
    for day_n, _link in logs_db_gen(folders):
        reports_by_day[day_n].append(_link)

    for day_n, reports_list in reports_by_day.items():
        section = formal_cell(reports_list, month, day_n)
        new_html = new_html.replace(f">{day_n}<", f">{section}<")
    
    return new_html

def new_month(page: int=0):
    dt = datetime.now()
    month = dt.month + page - 1
    return dt.year + month//12, month % 12 + 1

def get_a(page: int, folders: list[str]):
    year, month = new_month(page)
    _correct_month = f"{year%100:>02}-{month:>02}"
    folders = (
        folder
        for folder in folders
        if folder.startswith(_correct_month)
    )
    html = get_reports_by_month(year, month, folders)
    return html.split(SPLIT_TR)

def remove_empty(line: str):
    a = [x for x in line.split(SPLIT_TD) if "&nbsp" not in x]
    return SPLIT_TD.join(a)

@running_time
def makeshit(page: int=0, *filters):
    folders = file_functions.get_folders(LOGS_DIR)
    for x in filters:
        print(x)
        folders = file_functions.get_folders_filter(folders, _filter=x)
    prev_month = get_a(page-1, folders)
    prev_month_last_line = remove_empty(prev_month[-1])

    this_month = get_a(page, folders)
    this_month_first_line = remove_empty(this_month[3])

    if prev_month[-1] != prev_month_last_line:
        this_month_first_line = prev_month_last_line + this_month_first_line
        prev_month_last_line = prev_month[-2]

    combined = ['', prev_month_last_line, this_month_first_line] + this_month[4:]
    return SPLIT_TR.join(combined).replace("</table>\n", "")
