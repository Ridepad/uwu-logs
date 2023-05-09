import os
import threading
from datetime import datetime, timedelta
from struct import unpack

from flask import (
    Flask, request,
    make_response, render_template, send_from_directory)
import psutil

from werkzeug.exceptions import TooManyRequests
from werkzeug.middleware.proxy_fix import ProxyFix

import logs_top_statistics
import file_functions
import logs_calendar
import logs_main
import logs_upload
from constants import (
    ICON_CDN_LINK, LOGGER_CONNECTIONS, LOGGER_MEMORY, LOGS_DIR, LOGS_RAW_DIR, MONTHS, PATH_DIR,
    REPORTS_PRIVATE, STATIC_DIR, T_DELTA, TOP_DIR
)

try:
    import _validate
except ImportError:
    pass

SERVER = Flask(__name__)
SERVER.wsgi_app = ProxyFix(SERVER.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
SERVER.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
SERVER.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300

LOGGER_CONNECTIONS.debug("Starting server...")

USE_FILTER = True
MAX_SURVIVE_LOGS = T_DELTA["5MIN"]
OPENED_LOGS: dict[str, logs_main.THE_LOGS] = {}
NEW_UPLOADS: dict[str, logs_upload.FileSave] = {}
CACHED_PAGES = {}
IGNORED_PATHS = {"upload", "upload_progress"}

RL: dict[str, dict[str, datetime]] = {}
RL_TD = {
    timedelta(seconds=30): 5,
    timedelta(minutes=1): 10,
    timedelta(hours=1): 30,
    timedelta(days=1): 100,
}
def wait_for_new(ip):
    openned_times_ip = RL.get(ip)
    if not openned_times_ip: return

    openned_times = openned_times_ip.values()

    now = datetime.now()
    for _delta, open_max in RL_TD.items():
        rlimit = now - _delta
        openned = sum(openned_on > rlimit for openned_on in openned_times)
        print(ip, _delta, openned)
        if openned > open_max:
            _min_opened = min(x for x in openned_times if x > rlimit)
            return _min_opened + _delta

def add_log_entry(ip, method, msg):
    LOGGER_CONNECTIONS.info(f"{ip:>15} | {method:<7} | {msg}")

def load_report(report_id: str):
    now = datetime.now()
    ip = request.remote_addr
    if report_id in OPENED_LOGS:
        report = OPENED_LOGS[report_id]
    elif wait_for_new(ip):
        add_log_entry(ip, "SPAM", report_id)
        raise TooManyRequests(retry_after=wait_for_new(ip))
    else:
        report = logs_main.THE_LOGS(report_id)
        OPENED_LOGS[report_id] = report
        RL.setdefault(ip, {})[report_id] = now
        add_log_entry(ip, "OPENNED", report_id)
        LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | OPEN    | {report_id:50} | {ip:>15}")
    
    report.last_access = now
    return report

def get_formatted_query_string():
    query = request.query_string.decode()
    if not query:
        return ""
    return f"?{query}"

MAX_PW_ATTEMPTS = 5
WRONG_PW_FILE = os.path.join(PATH_DIR, '_wrong_pw.json')
WRONG_PW = file_functions.json_read(WRONG_PW_FILE)

def wrong_pw(ip):
    attempt = WRONG_PW.get(ip, 0) + 1
    WRONG_PW[ip] = attempt
    if attempt >= MAX_PW_ATTEMPTS:
        file_functions.json_write(WRONG_PW_FILE, WRONG_PW, backup=True)
    return MAX_PW_ATTEMPTS - attempt

def banned(ip):
    return WRONG_PW.get(ip, 0) >= MAX_PW_ATTEMPTS

def render_template_wrap(file: str, **kwargs):
    path = kwargs.get("PATH", "")
    query = kwargs.get("QUERY", "")
    page = render_template(file, **kwargs)
    pages = CACHED_PAGES.setdefault(path, {})
    pages[query] = page
    return page


@SERVER.route('/favicon.ico')
def favicon():
    response = send_from_directory(STATIC_DIR, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    response.cache_control.max_age = 30 * 24 * 60 * 60
    return response

@SERVER.route('/class_icons.jpg')
def class_icons():
    response = send_from_directory(STATIC_DIR, 'class_icons.jpg', mimetype='image/jpeg')
    response.cache_control.max_age = 30 * 24 * 60 * 60
    return response

@SERVER.errorhandler(404)
def method404(e):
    return render_template("404.html")

@SERVER.errorhandler(429)
def method429(e):
    retry_in = e.retry_after - datetime.now()
    return render_template("429.html", retry_in=retry_in)

@SERVER.errorhandler(500)
def method500(e):
    LOGGER_CONNECTIONS.exception(f"{request.remote_addr:>15} | {request.method:<7} | {get_incoming_connection_info()}")
    return render_template("500.html")


def __cleaner():
    cleaner_thread: threading.Thread = None

    def cleaner2():
        print(psutil.virtual_memory().available)
        LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | CLEANER")
        now = datetime.now()
        for report_id, report in dict(OPENED_LOGS).items():
            if now - report.last_access > MAX_SURVIVE_LOGS:
                del OPENED_LOGS[report_id]
                LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | NUKED   | {report_id}")
        
        a = sorted((report.last_access, report_id) for report_id, report in OPENED_LOGS.items())
        while a and psutil.virtual_memory().available < 800*1024*1024:
            _, report_id = a.pop(0)
            del OPENED_LOGS[report_id]
            LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | NUKED   | {report_id}")

    def cleaner():
        nonlocal cleaner_thread
        if cleaner_thread is None:
            cleaner_thread = threading.Thread(target=cleaner2)
            cleaner_thread.start()
        elif not cleaner_thread.is_alive():
            cleaner_thread = None
    
    return cleaner

cleaner = __cleaner()

@SERVER.teardown_request
def after_request_callback(response):
    cleaner()
    
    return response

@SERVER.route("/pw_validate", methods=["POST"])
def pw_validate():
    if _validate.pw(request):
        resp = make_response('Success')
        _validate.set_cookie(resp)
        return resp
    
    attempts_left = wrong_pw(request.remote_addr)
    return f'{attempts_left}', 401

def get_incoming_connection_info():
    path = request.path
    
    if request.query_string:
        path = f"{path}?{request.query_string.decode()}"

    if request.data:
        try:
            path = f"{path} | {request.data.decode()}"
        except UnicodeDecodeError:
            pass
    
    return f"{path} | {request.headers.get('User-Agent')}"

def log_incoming_connection():
    path = request.path
    if path in IGNORED_PATHS:
        return
    msg = get_incoming_connection_info()
    add_log_entry(request.remote_addr, request.method, msg)

@SERVER.before_request
def before_request():
    log_incoming_connection()

    if banned(request.remote_addr):
        return render_template('home.html')

    url_comp = request.path.split('/')
    if url_comp[1] != "reports":
        return

    report_id = url_comp[2]
    if not report_id:
        return show_logs_list()

    report_path = os.path.join(LOGS_DIR, report_id)
    if not os.path.isdir(report_path):
        return render_template("404.html")
    
    elif USE_FILTER:
        _filter = file_functions.get_logs_filter(REPORTS_PRIVATE)
        if report_id in _filter and not _validate.cookie(request):
            return render_template('protected.html')

    if request.path in CACHED_PAGES:
        query = get_formatted_query_string()
        pages = CACHED_PAGES[request.path]
        if not SERVER.debug and query in pages:
            return pages[query]


@SERVER.route("/")
def home():
    return render_template('home.html')

LOGS_LIST_MONTHS = list(enumerate(MONTHS, 1))
# @SERVER.route("/logs_list", methods=['GET', 'POST'])
@SERVER.route("/logs_list")
def show_logs_list():
    # if request.method == 'POST':
    #     print(request.data)
    #     return '', 200
        # page = request.data.get()
        # new_month = logs_calendar.makeshit(page)
        # return logs_calendar.makeshit(page)

    page = request.args.get("page", default=0, type=int)
    free = request.args.get("free")
    server = request.args.get("server")
    new_month = logs_calendar.makeshit(page, free, server)
    year, month = logs_calendar.new_month(page)
    years = list(range(2018, datetime.now().year+2))
    month_name = MONTHS[month-1]
    servers = file_functions.get_folders(TOP_DIR)
    
    query = ""
    if server:
        query = f"{query}&server={server}"
    if free:
        query = f"{query}&free={free}"
    prev_query = f"?page={page-1}{query}"
    next_query = f"?page={page+1}{query}"
    
    return render_template(
        'logs_list.html',
        new_month=new_month,
        PREV_QUERY=prev_query, NEXT_QUERY=next_query,
        CURRENT_MONTH=month_name, CURRENT_YEAR=year, CURRENT_SERVER=server,
        MONTHS=LOGS_LIST_MONTHS, YEARS=years, SERVERS=servers,
    )

def file_is_proccessing(ip):
    if ip not in NEW_UPLOADS:
        return False
    
    new_upload = NEW_UPLOADS[ip]
    if new_upload.upload_thread is None:
        return False
    if new_upload.upload_thread.is_alive():
        return True
    
    del NEW_UPLOADS[ip]
    return False

@SERVER.route("/upload_progress")
def upload_progress():
    ip = request.remote_addr
    if ip not in NEW_UPLOADS:
        print("upload_progress ip not in NEW_UPLOADS")
        return '', 204
    
    print("upload_progress ip in NEW_UPLOADS")
    new_upload = NEW_UPLOADS[ip]
    if new_upload.upload_thread is None:
        return '', 204

    print(new_upload.upload_thread.status_dict)
    status_str = new_upload.upload_thread.status_json
    if new_upload.upload_thread.status_dict.get('done') == 1:
        del NEW_UPLOADS[ip]
    elif not new_upload.upload_thread.is_alive():
        del NEW_UPLOADS[ip]
        return '', 500
    
    return status_str, 200

@SERVER.route("/upload", methods=['GET', 'POST'])
def upload():
    IP = request.remote_addr

    if request.method == 'GET':
        servers = file_functions.get_folders(TOP_DIR)
        return render_template('upload.html', SERVERS=servers)

    new_upload = NEW_UPLOADS.get(IP)
    if new_upload is None:
        new_upload = NEW_UPLOADS[IP] = logs_upload.FileSave()
    
    if request.headers.get("Content-Type") == "application/json":
        new_upload.done(request)
        return '', 201

    chunkN = request.headers.get("X-Chunk", type=int)
    date = request.headers.get("X-Date", type=int)
    success = new_upload.add_chunk(request.data, chunkN, date)
    
    if success:
        return '', 200
    
    return '', 304

@SERVER.route("/reports/<report_id>/")
def report_page(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    data = report.get_report_page_all(segments)

    return render_template_wrap(
        'report_main.html', **default_params, **data,
        ICON_CDN_LINK=ICON_CDN_LINK,
    )

@SERVER.route("/reports/<report_id>/download")
def download_logs(report_id):
    return send_from_directory(LOGS_RAW_DIR, f"{report_id}.7z")

@SERVER.route("/reports/<report_id>/player/<source_name>/")
def player(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    sGUID = report.name_to_guid(source_name)
    tGUID = request.args.get('target')
    
    data_gen = report.player_damage_gen(segments, sGUID, tGUID)
    data_sum = report.player_damage_sum(data_gen)
    data = report.player_damage_format(data_sum)

    _server = default_params.get("SERVER", "")
    if _server.startswith("Frostmourne"):
        default_params["SERVER"] = "Frostmourne"

    return render_template_wrap(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/taken/<source_name>/")
def taken(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    sGUID = report.name_to_guid(source_name)
    tGUID = request.args.get('target')
    data_gen = report.player_damage_taken_gen(segments, sGUID, tGUID)
    data_sum = report.player_damage_sum(data_gen)
    data = report.player_damage_format(data_sum)

    return render_template_wrap(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/heal/<source_name>/")
def heal(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    sGUID = report.name_to_guid(source_name)
    tGUID = request.args.get('target')
    data_gen = report.player_heal_gen(segments, sGUID, tGUID)
    data_sum = report.player_damage_sum(data_gen)
    print(data_sum["units"])
    data = report.player_damage_format(data_sum)

    return render_template_wrap(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/casts/<source_name>/")
def casts(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.get_spell_history_wrap(segments, source_name)
    rounded_duration = round(default_params.get("DURATION", 0), 1)
    return render_template_wrap(
        'player_spells.html', **default_params, **data,
        SOURCE_NAME=source_name, RDURATION=rounded_duration,
    )

@SERVER.route("/reports/<report_id>/spellsearch", methods=["POST"])
def spellsearch(report_id):
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = request.form
    report = load_report(report_id)
    return report.filtered_spell_list(data)

@SERVER.route("/reports/<report_id>/get_dps", methods=["POST"])
def get_dps(report_id):
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = request.form
    report = load_report(report_id)
    return report.get_dps_wrap(data)

@SERVER.route("/reports/<report_id>/spell/<spell_id>/")
def spells(report_id, spell_id: str):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.spell_count_all(segments, spell_id)

    return render_template_wrap(
        'spells_page.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/consumables/")
def consumables(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.potions_all(segments)

    return render_template_wrap(
        'consumables.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/all_auras/")
def all_auras(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.auras_info_all(segments)

    return render_template_wrap(
        'all_auras.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/damage/")
def damage_targets(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.useful_damage_all(segments, default_params["BOSS_NAME"])

    return render_template_wrap(
        'damage_target.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/compare/", methods=["GET", "POST"])
def compare(report_id):
    if request.method == 'GET':
        report = load_report(report_id)
        default_params = report.get_default_params(request)

        return render_template(
            'compare.html', **default_params,
        )
    elif request.method == 'POST':
        request_data = request.get_json(force=True, silent=True)
        if request_data is None:
            request_data = request.form
        class_name = request_data.get('class')
        if not class_name:
            return "{}"
        
        report = load_report(report_id)
        default_params = report.get_default_params(request)
        segments = default_params["SEGMENTS"]
        return report.get_comp_data(segments, class_name)

@SERVER.route("/reports/<report_id>/valks/")
def valks(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.valk_info_all(segments)

    return render_template_wrap(
        'valks.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/deaths/")
def deaths(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    guid = request.args.get("target")
    data = report.get_deaths(segments, guid)

    return render_template_wrap(
        'deaths.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/powers/")
def powers(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.get_powers_all(segments)

    return render_template_wrap(
        'powers.html', **default_params, **data
    )


@SERVER.route("/reports/<report_id>/custom_search_post", methods=["POST"])
def custom_search_post(report_id):
    data = None
    try:
        data = request.get_json(force=True)
    except Exception:
        pass
    if not data:
        return ('', 204)
    report = load_report(report_id)
    return report.logs_custom_search(data)

@SERVER.route("/reports/<report_id>/custom_search/")
def custom_search(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    return render_template(
        'custom_search.html', **default_params,
    )
        
@SERVER.route("/reports/<report_id>/player_auras/<player_name>/")
def player_auras(report_id, player_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    s, f = segments[0]

    filter_guid = report.name_to_guid(player_name)

    data = report.get_auras(s, f, filter_guid)


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
    
    return render_template_wrap(
        'player_auras.html', **default_params, **data,
        SOURCE_NAME=player_name,
        # checkboxes=checkboxes, intable=intable, 
    )

def get_uncompressed_size(filename):
    try:
        with open(filename, 'rb') as f:
            f.seek(-4, 2)
            return unpack('I', f.read(4))[0]
    except FileNotFoundError:
        return 0

@SERVER.route('/top', methods=["GET", "POST"])
def top():
    if request.method == "GET":
        servers = file_functions.get_folders(TOP_DIR)
        return render_template('top.html', SERVERS=servers)
    
    _data: dict = request.get_json()

    server = _data.get("server")
    boss = _data.get("boss")
    diff = _data.get("diff")
    if not any({server, boss, diff}):
        return '', 404
    
    server_folder = file_functions.new_folder_path(TOP_DIR, server)
    fname = f"{boss} {diff}.gzip"
    p = os.path.join(server_folder, fname)
    content = file_functions.bytes_read(p)

    response = make_response(content)
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-length'] = len(content)
    response.headers['X-Full-Content-length'] = get_uncompressed_size(p)
    return response

@SERVER.route('/top_stats', methods=["GET", "POST"])
def top_stats():
    if request.method == "GET":
        servers = file_functions.get_folders(TOP_DIR)
        return render_template(
            'top_stats.html',
            SPECS_BASE=logs_top_statistics.get_specs_data(),
            SERVERS=servers,
        )
    
    _data: dict = request.get_json()

    server = _data.get("server")
    boss = _data.get("boss")
    diff = _data.get("diff")
    
    return logs_top_statistics.get_boss_data(server, boss, diff)


def connections():
    return

if __name__ == "__main__":
    SERVER.run(host="0.0.0.0", port=5000, debug=True)
