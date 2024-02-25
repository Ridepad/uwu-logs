import os
import threading
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, request,
    make_response,
    redirect,
    render_template,
    send_from_directory,
)

from werkzeug.exceptions import NotFound, TooManyRequests
from werkzeug.middleware.proxy_fix import ProxyFix

# import test_prev_kills
import logs_item_parser
import logs_ench_parser

import h_cleaner
import logs_top_statistics
import file_functions
import logs_calendar
import logs_main
import logs_top_db
import logs_upload
from constants import (
    ALL_FIGHT_NAMES,
    FLAG_ORDER,
    GEAR,
    LOGGER_CONNECTIONS,
    LOGS_DIR,
    LOGS_RAW_DIR,
    MONTHS,
    STATIC_DIR,
    T_DELTA,
    TOP_DIR,
)

try:
    import _validate
except ImportError:
    _validate = None


PATH = Path(__file__).parent
CACHE_DIR = PATH.joinpath("cache")

DB_LOCK = threading.RLock()

SERVER = Flask(__name__)
# SERVER = Flask(__name__, static_url_path='')
SERVER.wsgi_app = ProxyFix(SERVER.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

USE_FILTER = True
MAX_SURVIVE_LOGS = T_DELTA["30MIN"]
IGNORED_PATHS = {"/upload", "/upload_progress"}
LOGS_LIST_MONTHS = list(enumerate(MONTHS))
SERVER_STARTED = datetime.now()
SERVER_STARTED_STR = SERVER_STARTED.strftime("%y-%m-%d")
YEARS = list(range(2018, SERVER_STARTED.year+2))

CACHED_PAGES = {}
OPENED_LOGS: dict[str, logs_main.THE_LOGS] = {}
NEW_UPLOADS: dict[str, logs_upload.FileSave] = {}

cleaner = h_cleaner.MemoryCleaner(OPENED_LOGS)

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
        _limit = _validate.rate_limited_reports(ip, report_id)
        if _limit:
            add_log_entry(ip, "SPAM", report_id)
            raise TooManyRequests(retry_after=_limit)
    
    cleaner.run()
    report = logs_main.THE_LOGS(report_id)
    OPENED_LOGS[report_id] = report
    add_log_entry(ip, "OPENNED", report_id)

    report.last_access = now
    return report

def get_formatted_query_string():
    query = request.query_string.decode()
    if not query:
        return ""
    return f"?{query}"

def render_template_cache(file: str, **kwargs):
    path = kwargs.get("PATH", "")
    query = kwargs.get("QUERY", "")
    page = render_template(
        file,
        **kwargs,
    )
    pages = CACHED_PAGES.setdefault(path, {})
    pages[query] = page
    return page

def render_template_wrap(file: str, **kwargs):
    return render_template(
        file,
        **kwargs,
    )


@SERVER.errorhandler(404)
def method404(e):
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
        return redirect("/logs_list")

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
            return render_template_wrap('protected.html')
        return "", 403

    if not SERVER.debug and request.method == "GET" and request.path in CACHED_PAGES:
        query = get_formatted_query_string()
        pages = CACHED_PAGES[request.path]
        if query in pages:
            return pages[query]


@SERVER.route("/")
def home():
    return render_template_wrap('home.html')

@SERVER.route("/about")
def about():
    return render_template_wrap('about.html')

@SERVER.route("/logs_list", methods=['GET', 'POST'])
def show_logs_list():
    if request.method == "POST":
        _filter = logs_calendar.normalize_filter(request.json)
        if not _filter:
            return "", 418
        resp = make_response(logs_calendar.get_logs_list_filter_json(_filter))
        resp.headers.add("Content-Type", "application/json")
        return resp
    
    servers = logs_top_db.server_list()
    server = request.args.get("server")
    YEAR_REQUEST = request.args.get("year", type=int)
    MONTH_REQUEST = request.args.get("month", type=int)
    if YEAR_REQUEST is None or MONTH_REQUEST is None:
        DATE_CURRENT = datetime.now()
        YEAR_REQUEST = DATE_CURRENT.year
        MONTH_REQUEST = DATE_CURRENT.month - 1

    MONTH_PREV = (MONTH_REQUEST + 11) % 12
    YEAR_PREV = YEAR_REQUEST-1 if MONTH_REQUEST == 0 else YEAR_REQUEST

    r = dict(request.args)
    r["month"] = MONTH_REQUEST + 1
    r["year"] = YEAR_REQUEST % 1000
    current_month = logs_calendar.get_logs_list_df_filter_to_calendar_wrap(r)
    r["month"] = MONTH_PREV + 1
    r["year"] = YEAR_PREV % 1000
    prev_month = logs_calendar.get_logs_list_df_filter_to_calendar_wrap(r)
    new_month = prev_month | current_month

    calend_prev = logs_calendar.get_calend_days(YEAR_PREV, MONTH_PREV)
    calend = logs_calendar.get_calend_days(YEAR_REQUEST, MONTH_REQUEST)
    calend_prev_last_week = calend_prev[-1]
    if calend_prev_last_week == calend[0]:
        calend_prev_last_week = calend_prev[-2]
    calend.insert(0, calend_prev_last_week)

    return render_template_wrap(
        'logs_list.html',
        MONTH=new_month,
        CALEND=calend,
        CURRENT_MONTH=MONTH_REQUEST,
        CURRENT_YEAR=YEAR_REQUEST,
        CURRENT_SERVER=server,
        MONTHS=LOGS_LIST_MONTHS,
        YEARS=YEARS,
        SERVERS=servers,
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
        return render_template_wrap('upload.html', SERVERS=servers)

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
    data = report.get_report_page_all_wrap(request)

    return render_template_cache(
        'report_main.html', **data,
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

    tGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, source_name, filter_guid=tGUID)

    return render_template_cache(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/heal/<source_name>/")
def heal(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    tGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, source_name, filter_guid=tGUID, heal=True)

    return render_template_cache(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/taken/<target_name>/")
def taken(report_id, target_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    sGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, target_name, filter_guid=sGUID, taken=True)

    return render_template_cache(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=target_name,
    )

@SERVER.route("/reports/<report_id>/healed/<target_name>/")
def healed(report_id, target_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    tGUID = report.name_to_guid(target_name)

    sGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, target_name, filter_guid=sGUID, heal=True, taken=True)
    
    return render_template_cache(
        'dmg_done2.html', **default_params, **data,
        SOURCE_NAME=target_name,
        ABORBS_DETAILS=report.get_absorbs_details_wrap(segments, tGUID)
    )

@SERVER.route("/reports/<report_id>/casts/<source_name>/")
def casts(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    # segments = default_params["SEGMENTS"]

    # data = report.get_spell_history_wrap(segments, source_name)
    return render_template_cache(
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

    return render_template_cache(
        'spells_page.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/consumables/")
def consumables(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.potions_all(segments)

    return render_template_cache(
        'consumables.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/all_auras/")
def all_auras(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.auras_info_all(segments)

    return render_template_cache(
        'all_auras.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/damage/")
def damage_targets(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.useful_damage_all(segments, default_params["BOSS_NAME"])

    return render_template_cache(
        'damage_target.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/compare/", methods=["GET", "POST"])
def compare(report_id):
    if request.method == 'GET':
        report = load_report(report_id)
        default_params = report.get_default_params(request)

        return render_template_cache(
            'compare.html', **default_params,
        )
    elif request.method == 'POST':
        request_data = request.get_json(force=True, silent=True)
        if request_data is None:
            request_data = request.form
        class_name = request_data.get('class')
        if not class_name:
            return "[]"
        
        target = request_data.get('target')
        
        report = load_report(report_id)
        default_params = report.get_default_params(request)
        segments = default_params["SEGMENTS"]
        return report.get_comp_data(segments, class_name, tGUID=target)

@SERVER.route("/reports/<report_id>/valks/")
def valks(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.valk_info_all(segments)

    return render_template_cache(
        'valks.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/lady_spirits/")
def lady_spirits(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.lady_spirits_wrap(segments)
    return render_template_cache(
        'lady_spirits.html', **default_params,
        PULLS=data,
    )

@SERVER.route("/reports/<report_id>/deaths/")
def deaths(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    guid = request.args.get("target")
    data = report.get_deaths(segments, guid)

    return render_template_cache(
        'deaths.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/powers/")
def powers(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.get_powers_all(segments)

    return render_template_cache(
        'powers.html', **default_params, **data
    )


@SERVER.route('/top', methods=["GET", "POST"])
def top():
    if request.method == "GET":
        servers = logs_top_db.server_list()
        return render_template_wrap(
            'top.html',
            SERVERS=servers,
            REPORT_NAME="Top",
        )
    
    _data: dict = request.get_json()

    server = _data.get("server")
    boss = _data.get("boss")
    mode = _data.get("mode")

    if not all({server, boss, mode}):
        return '', 400
    
    with DB_LOCK:
        top = logs_top_db.Top(**_data)
        if boss == "Points":
            z = top.parse_top_points()
        else:
            z = top.get_data()
    response = make_response(z["data"])
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = z["length_compressed"]
    response.headers["Content-Length-Full"] = z["length"]
    return response

@SERVER.route('/pve_stats', methods=["GET", "POST"])
@SERVER.route('/top_stats', methods=["GET", "POST"])
def pve_stats():
    if request.method == "GET":
        servers = logs_top_db.server_list()
        return render_template_wrap(
            'pve_stats.html',
            SPECS_BASE=logs_top_statistics.SPECS_DATA_NOT_IGNORED,
            SERVERS=servers,
        )
    
    _data: dict = request.get_json()

    server = _data.get("server")
    boss = _data.get("boss")
    mode = _data.get("mode")

    if not all({server, boss, mode}):
        return '', 400
    
    with DB_LOCK:
        data = logs_top_db.PveStats(server).get_data(boss, mode)
    
    if data is None:
        return '', 400
    
    return data

@SERVER.route('/character', methods=["GET", "POST"])
def character():
    _data: dict = request.args
    name = _data.get("name")
    server = _data.get("server")
    if not name or not server:
        name = "Safiyah"
        server = "Lordaeron"
    
    name = name.title()
    server = server.title()
    
    spec = _data.get("spec", type=int)
    if spec not in range(1,4):
        spec = None
    
    if request.method == "GET":
        return render_template_wrap(
            'character.html',
            NAME=name,
            **GEAR,
        )

    with DB_LOCK:
        d = logs_top_db.parse_player(server, name, spec=spec)
    
    if not d:
        return '', 400
    return d

@SERVER.route("/ladder")
def ladder():
    return render_template_wrap(
        'ladder.html',
        REPORT_NAME="PvE Ladder",
    )

@SERVER.route("/missing/<type>/<id>", methods=["PUT"])
def missing(type, id):
    if _validate:
        ip = request.remote_addr
        url = request.url
        _limit = _validate.rate_limited_missing(ip, url)
        if _limit:
            add_log_entry(ip, "SPAM", url)
            raise TooManyRequests(retry_after=_limit)
    
    return_code = 400
    if type == "item":
        return_code = logs_item_parser.parse_and_save(id)
    elif type == "enchant":
        return_code = logs_ench_parser.parse_and_save(id)
    elif type == "icon":
        return_code = logs_item_parser.save_icon(id)

    return "", return_code


# def connections():
#     return


# @SERVER.route("/reports/<report_id>/custom_search_post", methods=["POST"])
# def custom_search_post(report_id):
#     data = None
#     try:
#         data = request.get_json(force=True)
#     except Exception:
#         pass
#     if not data:
#         return ('', 204)
#     report = load_report(report_id)
#     return report.logs_custom_search(data)

# @SERVER.route("/reports/<report_id>/custom_search/")
# def custom_search(report_id):
#     report = load_report(report_id)
#     default_params = report.get_default_params(request)
#     segments = default_params["SEGMENTS"]

#     return render_template(
#         'custom_search.html', **default_params,
#     )

# @SERVER.route("/guilds/<server>")
# def guilds(server):
#     return render_template_wrap(
#         'guilds.html',
#         CALEND=test_prev_kills.main(),
#         len=len,
#     )



if __name__ == "__main__":
    SERVER.config["ENV"] = "development"
    SERVER.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

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

    @SERVER.route('/', defaults={'path': ''})
    @SERVER.route('/cache/<path:path>')
    def cache(path):
        p = CACHE_DIR / Path(path)
        if not p.parent.is_dir():
            return {}, 404
        response = send_from_directory(p.parent, p.name, mimetype='application/json')
        return response
    
    SERVER.run(host="0.0.0.0", port=5000, debug=True, reloader_type="stat")
