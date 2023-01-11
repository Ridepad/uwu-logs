import os
import threading
from datetime import datetime

from flask import (
    Flask, request,
    make_response, render_template, send_from_directory)
from werkzeug.middleware.proxy_fix import ProxyFix

import logs_calendar
import logs_main
import logs_upload
import logs_top_server
from constants import (
    ICON_CDN_LINK, LOGGER_CONNECTIONS, LOGS_DIR, LOGS_RAW_DIR, MONTHS, PATH_DIR, T_DELTA, TOP_DIR,
    banned, get_folders, get_logs_filter, wrong_pw)

try:
    import _validate
except ImportError:
    pass

SERVER = Flask(__name__)
SERVER.wsgi_app = ProxyFix(SERVER.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
SERVER.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
SERVER.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300

LOGGER_CONNECTIONS.debug("Starting server...")

CLEANER: threading.Thread = None
USE_FILTER = True
MAX_SURVIVE_LOGS = T_DELTA["30SEC"]
ALLOWED_EXTENSIONS = {'zip', '7z', }
OPENED_LOGS: dict[str, logs_main.THE_LOGS] = {}
NEW_UPLOADS: dict[str, logs_upload.FileSave] = {}
CACHED_PAGES = {}
IGNORED_PATHS = {"upload_progress"}

def render_template_wrap(file: str, **kwargs):
    path = kwargs.get("PATH", "")
    query = kwargs.get("QUERY", "")
    page = render_template(file, **kwargs)
    pages = CACHED_PAGES.setdefault(path, {})
    pages[query] = page
    return page

def load_report(name: str):
    if name in OPENED_LOGS:
        report = OPENED_LOGS[name]
    else:
        report = logs_main.THE_LOGS(name)
        OPENED_LOGS[name] = report
        LOGGER_CONNECTIONS.info(f"{request.remote_addr:>15} | LOGS OPENED | {name}")
    
    report.last_access = datetime.now()
    return report

def get_formatted_query_string():
    query = request.query_string.decode()
    if not query:
        return ""
    return f"?{query}"

def get_default_params_wrap(report_id: str):
    return load_report(report_id).get_default_params(request)

@SERVER.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(PATH_DIR, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    # response = send_from_directory(os.path.join(PATH_DIR, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    # response.cache_control.max_age = 30 * 24 * 60 * 60
    # return response

@SERVER.route('/class_icons.jpg')
def class_icons():
    response = send_from_directory(os.path.join(PATH_DIR, 'static'), 'class_icons.jpg', mimetype='image/jpeg')
    response.cache_control.max_age = 30 * 24 * 60 * 60
    return response

@SERVER.errorhandler(404)
def method404(e):
    return render_template("404.html")

@SERVER.errorhandler(500)
def method500(e):
    return render_template("500.html")

def _cleaner():
    now = datetime.now()
    for name, report in dict(OPENED_LOGS).items():
        if now - report.last_access > MAX_SURVIVE_LOGS:
            del OPENED_LOGS[name]

@SERVER.teardown_request
def after_request_callback(response):
    global CLEANER

    if CLEANER is None:
        CLEANER = threading.Thread(target=_cleaner)
        CLEANER.start()
    elif not CLEANER.is_alive():
        CLEANER = None
    
    return response

@SERVER.route("/pw_validate", methods=["POST"])
def pw_validate():
    if _validate.pw(request):
        resp = make_response('Success')
        _validate.set_cookie(resp)
        return resp
    
    attempts_left = wrong_pw(request.remote_addr)
    return f'{attempts_left}', 401

def log_incoming_connection():
    # for k in dir(request):
    #     print(k, getattr(request, k))
    path = request.path
    if path in IGNORED_PATHS:
        return
    if request.query_string:
        path = f"{path}?{request.query_string.decode()}"

    req = f"{request.remote_addr:>15} | {request.method:<7} | {path} | {request.json} | {request.headers.get('User-Agent')}"
    LOGGER_CONNECTIONS.info(req)

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
        _filter = get_logs_filter("private")
        if report_id in _filter and not _validate.cookie(request):
            return render_template('protected.html')

    if request.path in CACHED_PAGES:
        query = get_formatted_query_string()
        pages = CACHED_PAGES[request.path]
        if query in pages:
            pass
            # return pages[query]


@SERVER.route("/")
def home():
    return render_template('home.html')

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
        return '', 205
    
    new_upload = NEW_UPLOADS[ip]
    if new_upload.upload_thread is None:
        return '', 204
    
    status_str = new_upload.upload_thread.status_json
    if new_upload.upload_thread.status_dict.get('done') == 1:
        del NEW_UPLOADS[ip]
    
    return status_str

@SERVER.route("/upload", methods=['GET', 'POST'])
def upload():
    IP = request.remote_addr

    if request.method == 'GET':
        return render_template('upload.html')

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
        'report_main.html', **default_params,
        **data,
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
    data = report.player_info_all(segments, sGUID, tGUID)

    return render_template_wrap(
        'dmg_done2.html', **default_params,
        **data,
        SOURCE_NAME=source_name,
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
    return report.get_dps(data)

@SERVER.route("/reports/<report_id>/spell/<spell_id>/")
def spells(report_id, spell_id: str):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.spell_count_all(segments, spell_id)

    return render_template_wrap(
        'spells_page.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/consumables/")
def consumables(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.potions_all(segments)

    return render_template_wrap(
        'consumables.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/all_auras/")
def all_auras(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.auras_info_all(segments)

    return render_template_wrap(
        'all_auras.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/damage/")
def damage_targets(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.useful_damage_all(segments, default_params["BOSS_NAME"])

    return render_template_wrap(
        'damage_target.html', **default_params,
        **data,
    )

# @SERVER.route("/reports/<report_id>/heal/")
# def heal_targets(report_id):
#     _default = request.default_params
#     segments = _default.pop('segments')
#     report = load_report(report_id)
#     data = report.useful_damage_all(segments, _default["boss_name"])

#     return render_template_wrap(
#         'heal_target.html', **_default,
#         **data,
#     )

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
        'valks.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/deaths/")
def deaths(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    guid = request.args.get("target")
    data = report.get_deaths(segments, guid)

    return render_template_wrap(
        'deaths.html', **default_params,
        **data,
    )

@SERVER.route("/reports/<report_id>/powers/")
def powers(report_id):
    report = load_report(report_id)
    default_params = report.get_default_params(request)
    segments = default_params["SEGMENTS"]

    data = report.get_powers_all(segments)

    return render_template_wrap(
        'powers.html', **default_params,
        **data
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
        'player_auras.html', **default_params,
        **data,
        SOURCE_NAME=player_name,
        # checkboxes=checkboxes, intable=intable, 
    )


@SERVER.route('/top', methods=["GET", "POST"])
def top():
    if request.method == "GET":
        servers = get_folders(TOP_DIR)
        return render_template('top.html', SERVERS=servers)
     
    content = logs_top_server.new_request(request.json)
    response = make_response(content)
    response.headers['Content-length'] = len(content)
    response.headers['Content-Encoding'] = 'gzip'
    return response


def connections():
    return

if __name__ == "__main__":
    SERVER.run(host="0.0.0.0", port=5000, debug=True)
