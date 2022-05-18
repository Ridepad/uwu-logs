import os
import threading
from datetime import datetime, timedelta

from flask import Flask, render_template, request, send_from_directory
from flask.helpers import url_for
from waitress import serve
from werkzeug.utils import redirect

import _main
import constants
import deaths
import logs_calendar
import logs_upload

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
UPLOAD_FOLDER = os.path.join(DIR_PATH, "uploads")
LOGS_DIR = os.path.join(DIR_PATH, "LogsDir")
ALLOWED_EXTENSIONS = {'zip', '7z', }
NEW_FILES: dict[str, logs_upload.NewUpload] = {}
OPENED_LOGS: dict[str, _main.THE_LOGS] = {}

CLEANER = []
MAX_SURVIVE_LOGS = timedelta(minutes=10)
MAX_SURVIVE_LOGS = timedelta(seconds=20)

ICON_CDN_LINK = "https://wotlk.evowow.com/static/images/wow/icons/large"

SERVER = Flask(__name__)
SERVER.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
SERVER.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


PRIVATE_LOGS = {
    "21-10-31--19-59--Nomadra", "21-10-24--19-59--Nomadra"
}

ALLOWED_REPORTS = {
    # '22-03-05--20-56--Nomadra',
    # '21-10-31--19-59--Nomadra',
    # '22-03-12--21-04--Nomadra',
    '22-04-30--21-35--Piscolita',
}

STATIC = {
    'favicon.ico',
}

USE_FILTER = True
USE_FILTER = False

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
# __MONTHS = [f"{x:0>2}" for x in range(1,13)]
# MONTHS = dict(zip(__MONTHS, MONTHS))

SHIFT = {
    'spell': 10,
    'potions': 10,
    'damage': 10,
    'player2': 10,
}

def get_shift(url_comp: list[str]):
    try:
        return SHIFT.get(url_comp[3], 0)
    except IndexError:
        return 0

def load_report(name: str):
    if name in OPENED_LOGS:
        report = OPENED_LOGS[name]
    else:
        report = _main.THE_LOGS(name)
        OPENED_LOGS[name] = report
        print('[SERVER] LOGS OPENED:', name)
    report.last_access = datetime.now()
    return report

def add_space(v):
    return f"{v:,}".replace(',', ' ')

def format_report_name(report_id: str):
    date, time, name = report_id.split('--')
    time = time.replace('-', ':')
    year, month, day = date.split("-")
    month = MONTHS[int(month)-1][:3]
    date = f"{day} {month} {year}"
    return f"{date}, {time} - {name}"

def default_params(report_id, request, shift=0):
    report = load_report(report_id)
    report_name = format_report_name(report_id)
    attempts_list = report.format_attempts()
    parsed = report.parse_request(request, shift)
    # class_data = report.get_classes()
    classes_names = report.get_classes_with_names()
    # SEGMENTS_QUERIES = report.SEGMENTS_SEPARATED
    _data = report.SEGMENTS_QUERIES
    segm_links = _data['segm_links']
    # diff_links = _data['diff_links']
    # boss_links = _data['boss_links']
    return {
        "report_id": report_id,
        "report_name": report_name,
        "attempts_list": attempts_list,
        "class_data": classes_names,
        "query": parsed["query"],
        "boss_name_id": parsed["boss_name_id"],
        "boss_name": parsed["boss_name"],
        "segments": parsed["segments"],
        # "SEGMENTS_QUERIES": SEGMENTS_QUERIES,
        "segments_links": segm_links,
        # "diff_links": diff_links,
        # "boss_links": boss_links,
    }



@SERVER.route('/favicon.ico')
def favicon():
    pth = os.path.join(SERVER.root_path, 'static')
    return send_from_directory(pth, 'favicon.ico')

# @SERVER.route('/static/style.css')
# def stylesheet():
#     pth = os.path.join(SERVER.root_path, 'static')
#     return send_from_directory(pth, 'style.css')

@SERVER.errorhandler(405)
def method405(e):
    return "POST ON DEEZ NUTZ INSTEAD, DOG"

@SERVER.errorhandler(413)
def method413(e):
    status = 'Files <64mb only, learn to compress, scrub'
    return render_template('upload.html', status=status)

@SERVER.errorhandler(404)
def method404(e):
    return render_template('no_page.html')

def _cleaner():
    now = datetime.now()
    for name, report in dict(OPENED_LOGS).items():
        if now - report.last_access > MAX_SURVIVE_LOGS:
            del OPENED_LOGS[name]
            print('[SERVER] CLEANED:', name, now - report.last_access)
    
    CLEANER.clear()

@SERVER.after_request
def after_request(response):
    if not CLEANER:
        t = threading.Thread(target=_cleaner)
        t.start()
        CLEANER.append(t)
    return response

@SERVER.before_request
def before_request():
    if request.path.startswith('/reports/'):
        url_comp = request.path.split('/')
        report_id = url_comp[2]
        report_path = os.path.join(LOGS_DIR, report_id)
        if not os.path.exists(report_path) or USE_FILTER and report_id not in ALLOWED_REPORTS:
            return render_template('no_page.html')

        shift = get_shift(url_comp)
        request.default_params = default_params(report_id, request, shift)
    SERVER.logger.info("before_request")

@SERVER.route("/")
def home():
    return render_template('layout.html')

@SERVER.route("/logs_list")
def show_logs_list():
    page = request.args.get("page", default=0, type=int)
    year, month = logs_calendar.new_month(page)
    new_month = logs_calendar.get_reports_by_month(year, month)
    month_name = MONTHS[month-1]
    return render_template(
        'logs_list.html',
        new_month=new_month,
        page=page, month=month_name, year=year,
    )

@SERVER.route("/upload/check_progress", methods=['POST'])
def check_progress():
    ip = request.remote_addr
    t = NEW_FILES.get(ip)
    if not t:
        return '{"f": 0, "m": "Session ended or file uploaded"}'
    
    new_name = getattr(t, 'new_name', None)
    if new_name and new_name not in OPENED_LOGS and t.new_logs:
        OPENED_LOGS[new_name] = t.new_logs
    return t.status_json

def allowed_file(filename: str):
    if '.' in filename:
        return filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def file_is_proccessing(ip):
    if ip in NEW_FILES:
        if NEW_FILES[ip].is_alive():
            return True
        del NEW_FILES[ip]
    return False

@SERVER.route("/upload", methods=['GET', 'POST'])
def upload():
    ip = request.remote_addr

    if file_is_proccessing(ip):
        return render_template('upload_progress.html')
    
    if request.method == 'GET':
        return render_template('upload.html')

    file = request.files.get('file')
    if not file or file.filename == '':
        status = 'No file was selected'
        return render_template('upload.html', status=status)
    
    if not allowed_file(file.filename):
        status = 'Supported file formats are .7z and .zip only'
        return render_template('upload.html', status=status)
    
    t = NEW_FILES[ip] = logs_upload.main(file, ip)
    t.start()
    return render_template('upload_progress.html')

@SERVER.route("/test2")
def test2():
    # deaths test
    report_id = '21-10-08--20-57--Nomadra'
    report = load_report(report_id)
    logs_slice = report.get_logs()
    guid = '0x06000000004C3CEB'
    death_logs = deaths.find_deaths(logs_slice, guid)
    d2 = []
    css = []
    tabs = []
    for n, timestamp in enumerate(death_logs, 1):
        name_css = f"death{n}"
        tabs.append((name_css, timestamp))
        css.append(f'#{name_css}:checked ~ #{name_css}-panel')
        d2.append((name_css, death_logs[timestamp]))
    # css = ', '.join(css) + " {position: absolute; display: block;}"
    css = ', '.join(css) + " {display: block;}"
    class_data = report.get_classes()
    return render_template(
        'deaths.html', tabs=tabs, _deaths=d2, customstyle=css,
        class_data=class_data,
        )

@SERVER.route("/test22")
def test22():
    report_id = '21-10-07--21-06--Inia'
    report = load_report(report_id)
    logs_slice = report.get_logs()
    guid = '0x06000000002E50C8'
    death_logs = deaths.find_deaths(logs_slice, guid)
    d2 = []
    css = []
    tabs = []
    for n, timestamp in enumerate(death_logs, 1):
        name_css = f"death{n}"
        tabs.append((name_css, timestamp))
        # css.append(f'#{name_css}:checked ~ #{name_css}-panel')
        # d2.append((name_css, death_logs[timestamp]))
    # css = ', '.join(css) + " {position: absolute; display: block;}"
    class_data = report.get_classes()
    return render_template(
        'deaths2.html', tabs=tabs, death_logs=death_logs,
        class_data=class_data,
        )

@SERVER.route("/testspells/<player_name>/")
def testspells(player_name):
    name = '21-07-16--21-10--Nomadra'
    name = '21-06-05--23-50--Zmed'
    report = load_report(name)
    if not player_name:
        player_guid = '0x060000000040F817' #Nomadra
    else:
        player_guid = report.name_to_guid(player_name)
    s, f, query = parse_first(request)
    spell_names, hits_data, raw_total, act_total = report.spell_info(player_guid, s, f)
    spell_colors = report.get_spells_colors(spell_names)
    return render_template(
        'dmg_done2.html', spell_colors=spell_colors,
        spell_names=spell_names, hits_data=hits_data,
        raw_total=raw_total, act_total=act_total)

@SERVER.route("/test3")
def test3():
    # new dmg done test
    name = '21-07-16--21-10--Nomadra'
    report = load_report(name)
    # players_names = report.get_players_guids().values()

    enc_data = report.get_enc_data()
    s, f = enc_data["deathbringer_saurfang"][-1]
    s, f = enc_data["professor_putricide"][-1]
    s, f = enc_data["the_lich_king"][-1]
    # s, f = 626385, 633765
    logs_slice = report.get_logs(s, f)
    # '0xF150008F010002BE', '0xF150008F010002BF', '0xF150008F010002C0'
    # filter_guids = ['0xF150008F010005AC', '0xF150008F010005AD', '0xF150008F010005AE', "0xF130008EF500020C"]
    # dmg = report.dmg_taken(logs_slice, filter_guids=filter_guids)
    dmg = report.dmg_taken(logs_slice)
    boss = next(iter(dmg))
    players = list(dmg[boss])
    players_names = {name for sources in dmg.values() for name in sources}
    # players_names = {name for name in players_names if any(name in sources for sources in dmg.values())}
    players.extend(players_names - set(players))
    return render_template('dmg_taken_test.html', dmg=dmg, players=players)


@SERVER.route("/reports/<report_id>/spellsearch", methods=["POST"])
def spellsearch(report_id):
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = request.form
    report = load_report(report_id)
    return report.filtered_spell_list(data)

@SERVER.route("/reports/<report_id>/spell/<spell_id>/")
def spells(report_id, spell_id: str):
    # _default = default_params(report_id, request, 10)
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.spell_count_all(segments, spell_id)

    _spells = report.get_spells()
    s_id = abs(int(spell_id))
    spell_name = _spells.get(s_id, {}).get('name', '')
    spell_name = f"{spell_id} {spell_name}"

    return render_template(
        'spells_page.html', **_default,
        slice_duration=data["duration"],
        spells=data["spells"], tabs=data["tabs"],
        spell_name=spell_name, spell_id=s_id,
    )

@SERVER.route("/reports/<report_id>/")
def report_page(report_id):
    # _default = default_params(report_id, request)
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.get_report_page_all(segments)
    # print(data['damage'])
    return render_template(
        'report_main.html', **_default,
        slice_duration=data["duration"],
        DAMAGE=data["damage"], HEALS=data["heals"],
        SPECS=data["specs"],
        icon_cdn_link=ICON_CDN_LINK,
    )

@SERVER.route("/reports/<report_id>/player2/<player_name>/")
def player2(report_id, player_name):
    # _default = default_params(report_id, request)
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    s, f = segments[0]

    filter_guid = report.name_to_guid(player_name)

    data = report.get_auras(s, f, filter_guid)

    buffs = data['buffs']
    debuffs = data['debuffs']
    spells = data['spells']
    spell_colors = report.get_spells_colors(spells)
    all_spells = report.get_spells()

    # checkboxes = []
    # intable = []
    # css = []
    # for n, guid in enumerate(buffs):
    #     name =  report.guid_to_name(guid)
    #     name_css = convert_to_html_name(name)
    #     color_hue = n*48
    #     zindex = n-1 if n>0 else 10
    #     checkboxes.append((name, color_hue, name_css))
    #     intable.append((guid, color_hue, zindex, name_css))
    #     css.append(f'#tar-{name_css}:checked ~ table .tar-{name_css}')
    # css = ', '.join(css) + "{display: inline-block;}"
    
    return render_template(
        'player2.html', **_default,
        buffs=buffs, debuffs=debuffs, spells=spells,
        source_name=player_name,
        all_spells=all_spells,
        buffs_uptime=data['buffs_uptime'],
        debuffs_uptime=data['debuffs_uptime'],
        # checkboxes=checkboxes, intable=intable, 
        spell_colors=spell_colors)

@SERVER.route("/reports/<report_id>/player/<source_name>/")
def player(report_id, source_name):
    # _default = default_params(report_id, request)
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')
    print(segments)
    sGUID = report.name_to_guid(source_name)
    tGUID = request.args.get('target')
    data = report.player_info_all(segments, sGUID, tGUID)

    return render_template(
        'dmg_done2.html', **_default,
        slice_duration=data["duration"],
        source_name=source_name,
        spell_colors=data["colors"], spell_names=data["names"],
        total=data["total"], useful=data["useful"],
        hits_data=data["hits"], targets=data["targets"]
    )

@SERVER.route("/reports/<report_id>/potions/")
def potions(report_id):
    # _default = default_params(report_id, request, 10)
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.potions_all(segments)

    return render_template(
        'potions.html', **_default,
        slice_duration=data["duration"], 
        total=data["total"], pots=data["pots"],
        pot_info=data["pot_info"],
    )

@SERVER.route("/reports/<report_id>/damage/")
def damage_targets(report_id):
    # print(request.default_params)
    # _default = default_params(report_id, request, 10)
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')
    data = report.useful_damage_all(segments, _default["boss_name"])

    return render_template(
        'damage_target.html', **_default,
        slice_duration=data["duration"], 
        _ths=data["head"],
        _total=data["total"],
        _all_shit=data["formatted"],
    )


@SERVER.route("/reports/<report_id>/valks/")
def valks(report_id):
    s, f, query = parse_first(request)
    report_name = format_report_name(report_id)

    report = load_report(report_id)
    class_data = report.get_classes()
    full_attempts = report.format_difficulty()

    exact, boss_name = report.parse_boss(request)
    s, f = report.convert_slice_to_time(s, f, exact)
    if not s and not f:
        s, f = report.boss_full_slice("The Lich King")
    logs_slice = report.get_logs(s, f)

    slice_duration = convert_duration(logs_slice)

    valk_grabs, valk_grabs_details, valks_damage = report.valk_info(logs_slice)

    return render_template(
        'valks.html', report_name=report_name, report_id=report_id, query=query,
        boss_name=boss_name, full_attempts=full_attempts, class_data=class_data,
        slice_duration=slice_duration,
        valks_damage=valks_damage,
        valk_grabs=valk_grabs, valk_grabs_details=valk_grabs_details)



@SERVER.route("/reports/<report_id>/custom_search_post", methods=["POST"])
def custom_search_post(report_id):
    data = request.get_json(force=True)
    report = load_report(report_id)
    return report.logs_custom_search(data)

@SERVER.route("/reports/<report_id>/custom_search/")
def custom_search(report_id):
    _default = default_params(report_id, request)
    report = load_report(report_id)
    segments = _default.pop('segments')



    return render_template(
        'custom_search.html', **_default,
    )
        

if __name__ == "__main__":
    SERVER.run(host="0.0.0.0", port=5000, debug=True)
    # serve(SERVER, listen='0.0.0.0:5000')
