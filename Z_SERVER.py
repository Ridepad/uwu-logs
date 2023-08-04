import os
import threading
from datetime import datetime
from struct import unpack

from flask import (
    Flask, request,
    make_response,
    redirect,
    render_template,
    send_from_directory,
)
import psutil

from werkzeug.exceptions import NotFound, TooManyRequests
from werkzeug.middleware.proxy_fix import ProxyFix

import logs_top_statistics
import file_functions
import logs_calendar
import logs_main
import logs_upload
from constants import (
    ALL_FIGHT_NAMES, FLAG_ORDER, ICONS_DIR, LOGGER_CONNECTIONS, LOGGER_MEMORY, LOGS_DIR, LOGS_RAW_DIR, MONTHS,
    STATIC_DIR, T_DELTA, TOP_DIR
)

try:
    import _validate
except ImportError:
    _validate = None


SERVER = Flask(__name__)
SERVER.wsgi_app = ProxyFix(SERVER.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
SERVER.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
SERVER.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300

USE_FILTER = True
MAX_SURVIVE_LOGS = T_DELTA["5MIN"]
IGNORED_PATHS = {"/upload", "/upload_progress"}
LOGS_LIST_MONTHS = list(enumerate(MONTHS, 1))
SERVER_STARTED = datetime.now()
SERVER_STARTED_STR = SERVER_STARTED.strftime("%y-%m-%d")
YEARS = list(range(2018, SERVER_STARTED.year+2))

CACHED_PAGES = {}
OPENED_LOGS: dict[str, logs_main.THE_LOGS] = {}
NEW_UPLOADS: dict[str, logs_upload.FileSave] = {}

LOGGER_CONNECTIONS.debug("Starting server...")


def add_log_entry(ip, method, msg):
    LOGGER_CONNECTIONS.info(f"{ip:>15} | {method:<7} | {msg}")

def load_report(report_id: str):
    now = datetime.now()
    ip = request.remote_addr
    if report_id in OPENED_LOGS:
        report = OPENED_LOGS[report_id]
        report.last_access = now
        return report
    
    if _validate:
        _limit = _validate.rate_limited(ip, report_id)
        if _limit:
            add_log_entry(ip, "SPAM", report_id)
            raise TooManyRequests(retry_after=_limit)
    
    report = logs_main.THE_LOGS(report_id)
    OPENED_LOGS[report_id] = report
    add_log_entry(ip, "OPENNED", report_id)
    LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | OPEN    | {report_id:50} | {ip:>15}")

    report.last_access = now
    return report

def get_formatted_query_string():
    query = request.query_string.decode()
    if not query:
        return ""
    return f"?{query}"

def render_template_wrap(file: str, **kwargs):
    path = kwargs.get("PATH", "")
    query = kwargs.get("QUERY", "")
    page = render_template(
        file,
        **kwargs,
        V=SERVER.debug and datetime.now() or SERVER_STARTED_STR,
    )
    pages = CACHED_PAGES.setdefault(path, {})
    pages[query] = page
    return page


@SERVER.route('/favicon.ico')
def favicon():
    response = send_from_directory(STATIC_DIR, 'favicon.ico', mimetype='image/x-icon')
    response.cache_control.max_age = 30 * 24 * 60 * 60
    return response

@SERVER.route('/class_icons.jpg')
def class_icons():
    response = send_from_directory(STATIC_DIR, 'class_icons.jpg', mimetype='image/jpeg')
    response.cache_control.max_age = 30 * 24 * 60 * 60
    return response

@SERVER.errorhandler(404)
def method404(e):
    if SERVER.debug and request.path.endswith(".jpg"):
        # handled by nginx
        return send_from_directory(ICONS_DIR, os.path.basename(request.path), mimetype='image/jpeg')

    response = ""
    if request.method == 'GET':
        response = render_template("404.html")
    return response, 404

@SERVER.errorhandler(405)
def method405(e):
    response = ""
    if request.method == 'GET':
        response = render_template("404.html")
    return response, 405

@SERVER.errorhandler(429)
def method429(e: TooManyRequests):
    retry_in = e.retry_after - datetime.now()
    response = str(retry_in)
    if request.method == 'GET':
        response = render_template("429.html", retry_in=retry_in)
    return response, 429

@SERVER.errorhandler(500)
def method500(e):
    LOGGER_CONNECTIONS.exception(f"{request.remote_addr:>15} | {request.method:<7} | {get_incoming_connection_info()}")
    response = ""
    if request.method == 'GET':
        response = render_template("500.html")
    return response, 500


def __cleaner():
    cleaner_thread: threading.Thread = None

    def cleaner2():
        LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | CLEANER")
        now = datetime.now()
        for report_id, report in dict(OPENED_LOGS).items():
            if now - report.last_access > MAX_SURVIVE_LOGS:
                del OPENED_LOGS[report_id]
                LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | NUKED O | {report_id}")
        
        a = sorted((report.last_access, report_id) for report_id, report in OPENED_LOGS.items())
        while a and psutil.virtual_memory().available < 800*1024*1024:
            _, report_id = a.pop(0)
            del OPENED_LOGS[report_id]
            LOGGER_MEMORY.info(f"{psutil.virtual_memory().available:>12} | NUKED M | {report_id}")

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
    if not _validate:
        return ""
    
    if _validate.pwcheck.banned(request.remote_addr):
        return "", 403

    if _validate.pw(request):
        resp = make_response('Success')
        _validate.set_cookie(resp)
        return resp
    
    attempts_left = _validate.pwcheck.attempts_left(request.remote_addr)
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

    url_comp = request.path.split('/')
    if url_comp[1] != "reports":
        return

    report_id = url_comp[2]
    if not report_id:
        return show_logs_list()

    report_folder = os.path.join(LOGS_DIR, report_id)
    if not os.path.isdir(report_folder):
        backup_folder = file_functions.get_backup_folder(report_folder)
        if not os.path.isdir(backup_folder):
            raise NotFound()
    
    if not USE_FILTER:
        pass
    elif not _validate:
        pass
    elif report_id not in file_functions.get_privated_logs():
        pass
    elif _validate.pwcheck.banned(request.remote_addr):
        if request.method == "GET":
            return redirect("/")
        return "", 403
    elif not _validate.cookie(request):
        if request.method == "GET":
            return render_template('protected.html')
        return "", 403

    if not SERVER.debug and request.path in CACHED_PAGES:
        query = get_formatted_query_string()
        pages = CACHED_PAGES[request.path]
        if query in pages:
            return pages[query]


@SERVER.route("/")
def home():
    return render_template('home.html')

@SERVER.route("/about")
def about():
    return render_template('about.html')

@SERVER.route("/logs_list", methods=['GET', 'POST'])
def show_logs_list():
    if request.method == "POST":
        _filter = logs_calendar.normalize_filter(request.json)
        if not _filter:
            return "", 418
        resp = make_response(logs_calendar.get_logs_list_filter_json(_filter))
        resp.headers.add("Content-Type", "application/json")
        return resp
    
    servers = file_functions.get_folders(TOP_DIR)
    server = request.args.get("server")
    YEAR_REQUEST = request.args.get("year", type=int)
    MONTH_REQUEST = request.args.get("month", type=int)
    if YEAR_REQUEST is None or MONTH_REQUEST is None:
        DATE_CURRENT = datetime.now()
        YEAR_REQUEST = DATE_CURRENT.year
        MONTH_REQUEST = DATE_CURRENT.month

    MONTH_PREV = (MONTH_REQUEST + 10) % 12 + 1
    YEAR_PREV = YEAR_REQUEST-1 if MONTH_PREV == 12 else YEAR_REQUEST

    r = dict(request.args)
    r["month"] = MONTH_REQUEST
    r["year"] = YEAR_REQUEST % 1000
    current_month = logs_calendar.get_logs_list_df_filter_to_calendar_wrap(r)
    r["month"] = MONTH_PREV
    r["year"] = YEAR_PREV % 1000
    prev_month = logs_calendar.get_logs_list_df_filter_to_calendar_wrap(r)
    new_month = prev_month | current_month

    month_name = MONTHS[MONTH_REQUEST-1]
    calend_prev = logs_calendar.get_calend_days(YEAR_PREV, MONTH_PREV)
    calend = logs_calendar.get_calend_days(YEAR_REQUEST, MONTH_REQUEST)
    calend_prev_last_week = calend_prev[-1]
    if calend_prev_last_week == calend[0]:
        calend_prev_last_week = calend_prev[-2]
    calend.insert(0, calend_prev_last_week)

    return render_template(
        'logs_list.html',
        MONTH=new_month, CALEND=calend,
        CURRENT_MONTH=month_name, CURRENT_YEAR=YEAR_REQUEST,
        CURRENT_SERVER=server,
        MONTHS=LOGS_LIST_MONTHS, YEARS=YEARS, SERVERS=servers,
        ALL_FIGHT_NAMES=ALL_FIGHT_NAMES,
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
        return '', 204
    
    new_upload = NEW_UPLOADS[ip]
    if new_upload.upload_thread is None:
        return '', 204

    status_dict = new_upload.upload_thread.status_dict
    if status_dict.get('done') == 1:
        del NEW_UPLOADS[ip]
    elif not new_upload.upload_thread.is_alive():
        del NEW_UPLOADS[ip]
        return '', 500
    
    return new_upload.upload_thread.status_to_json(), 200

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
        new_upload.done(IP, request.data)
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
    )

@SERVER.route("/reports/<report_id>/download")
def download_logs(report_id):
    fname = f"{report_id}.7z"
    if os.path.isfile(os.path.join(LOGS_RAW_DIR, fname)):
        return send_from_directory(LOGS_RAW_DIR, fname)
    return send_from_directory(file_functions.get_backup_folder(LOGS_RAW_DIR), fname)

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
    
    tGUID = request.args.get('target')
    _absorbs = report.get_absorbs_by_source_spells_wrap(segments, sGUID, tGUID)
    
    data = report.player_damage_format(data_sum, add_absorbs=_absorbs)

    return render_template_wrap(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/healed/<source_name>/")
def healed(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    sGUID = report.name_to_guid(source_name)
    tGUID = request.args.get('target')
    data_gen = report.player_heal_taken_gen(segments, sGUID, tGUID)
    data_sum = report.player_damage_sum(data_gen)
    
    tGUID = request.args.get('target')
    _absorbs = report.get_absorbs_by_target_wrap(segments, sGUID, tGUID)
    
    data = report.player_damage_format(data_sum, add_absorbs=_absorbs)
    return render_template_wrap(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
        ABORBS_DETAILS=report.get_absorbs_details_wrap(segments, sGUID)
    )

@SERVER.route("/reports/<report_id>/casts/<source_name>/")
def casts(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    # segments = default_params["SEGMENTS"]

    # data = report.get_spell_history_wrap(segments, source_name)
    return render_template_wrap(
        'casts.html', **default_params,
        # **data,
        FLAG_ORDER=FLAG_ORDER,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/casts/", methods=['POST'])
def casts_post(report_id):
    if not request.is_json:
        return "", 400
    
    _data: dict = request.json
    report = load_report(report_id)
    _z = report.parse_request(request.path, _data)
    data = report.get_spell_history_wrap_json(_z["SEGMENTS"], _data["name"])
    return data

@SERVER.route("/reports/<report_id>/report_slices/", methods=['POST'])
def report_slices(report_id):
    report = load_report(report_id)
    return report.get_segments_data_json()

@SERVER.route("/reports/<report_id>/players_classes/", methods=['POST'])
def players_classes(report_id):
    report = load_report(report_id)
    return report.get_classes_with_names_json()

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
        return render_template(
            'top.html',
            SERVERS=servers,
            V=SERVER.debug and datetime.now() or SERVER_STARTED_STR,
        )
    
    _data: dict = request.get_json()

    server = _data.get("server")
    boss = _data.get("boss")
    diff = _data.get("diff")
    if not any({server, boss, diff}):
        return '', 400
    
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
