from datetime import datetime

from flask import (
    Flask, request,
    make_response,
    redirect,
    render_template,
    send_file,
)

from werkzeug.exceptions import (
    BadRequest,
    NotFound,
    TooManyRequests,
)
from werkzeug.middleware.proxy_fix import ProxyFix

import h_cleaner
import logs_calendar
import logs_main
from constants import FLAG_ORDER
from c_bosses import ALL_FIGHT_NAMES, BOSSES_FROM_HTML
from c_path import Directories, Files
from h_datetime import MONTHS, T_DELTA
from h_debug import Loggers

try:
    import _validate
except ImportError:
    _validate = None

try:
    import test_group_bosses
except ImportError:
    test_group_bosses = None


SERVER = Flask(__name__)
SERVER.wsgi_app = ProxyFix(SERVER.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
SERVER.jinja_env.trim_blocks = True
SERVER.jinja_env.lstrip_blocks = True

USE_FILTER = True
MAX_SURVIVE_LOGS = T_DELTA["30MIN"]
IGNORED_PATHS = {"/upload", "/upload_progress"}
LOGS_LIST_MONTHS = list(enumerate(MONTHS))
SERVER_STARTED = datetime.now()
SERVER_STARTED_STR = SERVER_STARTED.strftime("%y-%m-%d")
YEARS = list(range(2018, SERVER_STARTED.year+2))

CACHED_PAGES = {}
OPENED_LOGS: dict[str, logs_main.THE_LOGS] = {}

CLEANER = h_cleaner.MemoryCleaner(OPENED_LOGS)

LOGGER_CONNECTIONS = Loggers.connections
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
    
    if _validate is not None:
        _limit = _validate.rate_limited_reports(ip, "report", report_id)
        if _limit:
            add_log_entry(ip, "SPAM", report_id)
            raise TooManyRequests(retry_after=_limit)
    
    CLEANER.start()
    report = logs_main.THE_LOGS(report_id)
    OPENED_LOGS[report_id] = report
    add_log_entry(ip, "OPENNED", report_id)

    report.last_access = now
    return report

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

@SERVER.errorhandler(Exception)
def handle_exception(e):
    LOGGER_CONNECTIONS.exception(f"{request.remote_addr:>15} | {request.method:<7} | {get_incoming_connection_info()}")
    error_class = f"{e.__class__.__module__}.{e.__class__.__name__}"
    error_msg = ""
    if error_class == "zstd.Error":
        error_msg = "Logs file is corrupted"
    else:
        error_msg = f"{error_class}: {e}"
    if request.method == 'GET':
        return render_template("500.html", ERROR_MESSAGE=error_msg)
    return error_msg, 500

@SERVER.route("/pw_validate", methods=["POST"])
def pw_validate():
    return _validate and _validate.check(request)
    
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

def log_exists(report_id: str):
    report_folder = Directories.logs / report_id
    if not report_folder.is_dir():
        backup_folder = report_folder.backup_path()
        if not backup_folder.is_dir():
            return False
    return True

def format_report_server(report_id: str):
    server = report_id.rsplit("--", 1)[-1]
    server_old = server.replace(" ", "-")
    if "WoW-Circle" in server_old:
        server_old = "WoW-Circle"
    return report_id.replace(server, server_old)

@SERVER.before_request
def before_request():
    log_incoming_connection()

    url_comp = request.path.split('/')
    if url_comp[1] != "reports":
        return

    report_id = url_comp[2]
    if not report_id:
        return redirect("/logs_list")

    if not log_exists(report_id):
        report_id = format_report_server(report_id)
        if log_exists(report_id):
            return redirect(f"/reports/{report_id}")
        raise NotFound()
    
    if not USE_FILTER:
        pass
    elif _validate is None:
        pass
    elif report_id not in Files.reports_private.text_lines():
        pass
    elif _validate.pwcheck.banned(request.remote_addr):
        if request.method == "GET":
            raise NotFound
        return "", 403
    elif not _validate.cookie(request):
        if request.method == "GET":
            return render_template('protected.html'), 401
        return "", 403


@SERVER.route("/")
def home():
    return render_template('home.html')

@SERVER.route("/about")
def about():
    return render_template('about.html')


@Directories.top.cache_until_new_self
def get_servers(folder):
    s = set((
        file_path.stem
        for file_path in folder.iterdir()
        if file_path.suffix == ".db"
    ))
    SERVERS_MAIN = Files.server_main.json_cached_ignore_error()
    new = sorted(s - set(SERVERS_MAIN))
    return SERVERS_MAIN + new

@SERVER.route("/logs_list", methods=['GET', 'POST'])
def show_logs_list():
    if request.method == "POST":
        _filter = logs_calendar.normalize_filter(request.json)
        if not _filter:
            return "", 418
        resp = make_response(logs_calendar.get_logs_list_filter_json(_filter))
        resp.headers.add("Content-Type", "application/json")
        return resp
    
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

    return render_template(
        'logs_list.html',
        MONTH=new_month,
        CALEND=calend,
        CURRENT_MONTH=MONTH_REQUEST,
        CURRENT_YEAR=YEAR_REQUEST,
        CURRENT_SERVER=server,
        MONTHS=LOGS_LIST_MONTHS,
        YEARS=YEARS,
        SERVERS=get_servers(),
        ALL_FIGHT_NAMES=ALL_FIGHT_NAMES,
    )

@SERVER.route("/reports/<report_id>/")
def report_page(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)

    if request.args.get("attempt") == "kill":
        segment = report.request_get_kill_segment(request)
        if segment:
            url = f"/reports/{report_id}/{segment.href}"
            return redirect(url)

    segments = default_params["SEGMENTS"]
    boss_name = request.args.get("boss")
    data = report.get_report_page_all_wrap(segments, boss_name)

    return render_template(
        'report_main.html',
        **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/download")
def download_logs(report_id):
    FILE_NAME = f"{report_id}.7z"
    DIRECTORIES = [
        Directories.archives,
        Directories.archives.backup_path(),
    ]
    for _dir in DIRECTORIES:
        file_path = _dir / FILE_NAME
        if file_path.is_file():
            return send_file(file_path)

    return "", 404

@SERVER.route("/reports/<report_id>/player/<source>/")
def player(report_id, source: str):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    tGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, source, filter_guid=tGUID)

    return render_template(
        'dmg_done2.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/heal/<source_name>/")
def heal(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    tGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, source_name, filter_guid=tGUID, heal=True)

    return render_template(
        'dmg_done2.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/taken/<target_name>/")
def taken(report_id, target_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    sGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, target_name, filter_guid=sGUID, taken=True)

    return render_template(
        'dmg_done2.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/healed/<target_name>/")
def healed(report_id, target_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    tGUID = report.name_to_guid(target_name)

    sGUID = request.args.get('target')
    data = report.get_numbers_breakdown_wrap(segments, target_name, filter_guid=sGUID, heal=True, taken=True)
    
    return render_template(
        'dmg_done2.html', **default_params, **data,
        # ABORBS_DETAILS=report.get_absorbs_details_wrap(segments, tGUID)
    )

@SERVER.route("/reports/<report_id>/casts/<source_name>/")
def casts(report_id, source_name):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    # segments = default_params["SEGMENTS"]

    # data = report.get_spell_history_wrap(segments, source_name)
    return render_template(
        'timeline.html', **default_params,
        # **data,
        FLAG_ORDER=FLAG_ORDER,
        SOURCE_NAME=source_name,
    )

@SERVER.route("/reports/<report_id>/casts/", methods=['POST'])
def casts_post(report_id):
    if not request.is_json:
        return "", 400
    
    _data: dict = request.json
    try:
        boss_name = BOSSES_FROM_HTML[_data.get("boss")]
    except KeyError:
        raise BadRequest(f"[boss_name] is not a valid boss name")
    
    try:
        attempt = int(_data.get("attempt"))
    except (ValueError, TypeError):
        raise BadRequest(f"[attempt] must be a number")
    
    player_name = _data.get("name")
    
    report = load_report(report_id)
    s, f = report.ENCOUNTER_DATA[boss_name][attempt]
    return report.get_spell_history_wrap_json(s, f, player_name)

@SERVER.route("/reports/<report_id>/report_slices/", methods=['POST'])
def report_slices(report_id):
    report = load_report(report_id)
    data = request.get_json(force=True, silent=True)
    return report.get_segments_data_json(data.get("boss"))

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
    _filter = str(data.get("filter", ""))
    return report.filtered_spell_list(_filter)

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

    return render_template(
        'spells_page.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/consumables/")
def consumables(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.potions_all(segments)

    return render_template(
        'consumables.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/entities/")
def entities(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.entities(*segments[0])

    return render_template(
        'entities.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/all_auras/")
def all_auras(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.auras_info_all(segments)

    return render_template(
        'all_auras.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/damage/")
def damage_targets(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    boss_name = request.args.get("boss")
    boss_name = BOSSES_FROM_HTML.get(boss_name, boss_name)
    data = report.damage_to_target_all_formatted(segments, boss_name)

    return render_template(
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
            return "[]"
        
        target = request_data.get('target')
        
        report = load_report(report_id)
        default_params = report.get_default_params(request)
        segments = default_params["SEGMENTS"]
        return report.get_comparison_data(segments, class_name, tGUID=target)

@SERVER.route("/reports/<report_id>/valks/")
def valks(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.valk_info_all(segments)

    return render_template(
        'valks.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/lady_spirits/")
def lady_spirits(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.lady_spirits_wrap(segments)
    return render_template(
        'lady_spirits.html', **default_params,
        PULLS=data,
    )

@SERVER.route("/reports/<report_id>/ucm/")
def ucm(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.parse_ucm_wrap(segments)
    return render_template(
        'ucm.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/toc_valks/")
def toc_valks(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]
    
    data = report.parse_shields_casts_wrap(*segments[0])
    return render_template(
        'toc_valks.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/deaths/")
def deaths(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.get_deaths_v2_wrap(segments)

    return render_template(
        'deaths.html', **default_params, **data,
    )

@SERVER.route("/reports/<report_id>/powers/")
def powers(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.get_powers_all(segments)

    return render_template(
        'powers.html', **default_params, **data
    )

@SERVER.route("/ladder")
def ladder():
    return render_template(
        'ladder.html',
        REPORT_NAME="PvE Ladder",
    )

@SERVER.route("/raid_calendar")
def raid_calendar():
    _calend = test_group_bosses.RaidCalendar()
    return render_template(
        'raid_calendar.html',
        REPORT_NAME="Raid Calendar",
        CALEND_DAYS=_calend.get(),
        HEAD=_calend.heads,
        len=len,
    )

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
#     return render_template(
#         'guilds.html',
#         CALEND=test_prev_kills.main(),
#         len=len,
#     )



if __name__ == "__main__":
    from h_other import Ports

    SERVER.config["ENV"] = "development"
    SERVER.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @SERVER.route('/favicon.ico')
    def favicon():
        file = Directories.static / "favicon.ico"
        response = send_file(file, mimetype='image/x-icon')
        response.cache_control.max_age = 30 * 24 * 60 * 60
        return response

    @SERVER.route('/upload')
    def upload():
        _url = str(request.url).replace(f":{Ports.main}/", f":{Ports.upload}/")
        return redirect(_url)
    
    SERVER.run(host="0.0.0.0", port=Ports.main, debug=True, reloader_type="stat")
