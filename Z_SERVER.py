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

CLEANER = []
USE_FILTER = True
FILTER_TYPE = "private"
MAX_SURVIVE_LOGS = T_DELTA["30SEC"]
ALLOWED_EXTENSIONS = {'zip', '7z', }
OPENED_LOGS: dict[str, logs_main.THE_LOGS] = {}
NEW_UPLOADS: dict[str, logs_upload.FileSave] = {}
CACHED_PAGES = {}

def render_template_wrap(file: str, **kwargs):
    path = kwargs.get("PATH", "")
    query = kwargs.get("QUERY", "")
    pages = CACHED_PAGES.setdefault(path, {})
    page = render_template(file, **kwargs)
    pages[query] = page
    return page

def load_report(name: str):
    if name in OPENED_LOGS:
        report = OPENED_LOGS[name]
    else:
        report = logs_main.THE_LOGS(name)
        OPENED_LOGS[name] = report
        print('[SERVER] LOGS OPENED:', name)
    
    report.last_access = datetime.now()
    return report

def default_params(report_id, request):
    report = load_report(report_id)
    report_name = report.get_formatted_name()
    parsed = report.parse_request(request)
    classes_names = report.get_classes_with_names()
    segm_links = report.get_segment_queries()
    duration = report.get_fight_duration_total_str(parsed["segments"])
    query = request.query_string.decode()
    query = f"?{query}" if query else ""

    return {
        "REPORT_ID": report_id,
        "REPORT_NAME": report_name,
        "PATH": request.path,
        "QUERY": query,
        "SLICE_NAME": parsed["slice_name"],
        "SLICE_TRIES": parsed["slice_tries"],
        "SEGMENTS_LINKS": segm_links,
        "CLASS_DATA": classes_names,
        "DURATION": duration,
        "boss_name": parsed["boss_name"],
        "segments": parsed["segments"],
    }

@SERVER.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(PATH_DIR, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@SERVER.errorhandler(404)
def method404(e):
    return render_template('404.html')

@SERVER.errorhandler(500)
def method500(e):
    return render_template('500.html')

def _cleaner():
    now = datetime.now()
    for name, report in dict(OPENED_LOGS).items():
        if now - report.last_access > MAX_SURVIVE_LOGS:
            del OPENED_LOGS[name]
    
@SERVER.teardown_request
def after_request_callback(response):
    if not CLEANER:
        t = threading.Thread(target=_cleaner)
        t.start()
        CLEANER.append(t)
    elif not CLEANER[0].is_alive():
        CLEANER.clear()
    return response

@SERVER.route("/pw_validate", methods=["POST"])
def pw_validate():
    if _validate.pw(request):
        resp = make_response('Success')
        _validate.set_cookie(resp)
        return resp
    
    attempts_left = wrong_pw(request.remote_addr)
    return f'{attempts_left}', 401

@SERVER.before_request
def before_request():
    if banned(request.remote_addr):
        return render_template('home.html')

    req = f"{request.remote_addr:>15} | {request.method:<7} | {request.full_path} | {request.headers.get('User-Agent')}"
    LOGGER_CONNECTIONS.info(req)

    if request.path.startswith('/reports/'):
        pages = CACHED_PAGES.get(request.path, {})
        query = request.query_string.decode()
        query = f"?{query}" if query else ""
        if query in pages:
            return pages[query]

        url_comp = request.path.split('/')
        report_id = url_comp[2]
        if not report_id:
            return

        report_path = os.path.join(LOGS_DIR, report_id)
        if not os.path.isdir(report_path):
            return render_template('404.html')
        
        elif USE_FILTER:
            _filter = get_logs_filter(FILTER_TYPE)
            if FILTER_TYPE == "private" and report_id in _filter and not _validate.cookie(request):
                return render_template('protected.html')

        request.default_params = default_params(report_id, request)


@SERVER.route("/")
def home():
    return render_template('home.html')

@SERVER.route("/logs_list")
@SERVER.route("/reports/")
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

def allowed_file(filename: str):
    if '.' in filename:
        return filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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
    
    status_str = new_upload.upload_thread.status_json
    if new_upload.upload_thread.status_dict.get('done') == 1:
        del NEW_UPLOADS[ip]
    
    return status_str

@SERVER.route("/upload", methods=['GET', 'POST'])
def upload():
    ip = request.remote_addr

    if request.method == 'GET':
        return render_template('upload.html')

    new_upload = NEW_UPLOADS.get(ip)
    if new_upload is None:
        new_upload = NEW_UPLOADS[ip] = logs_upload.FileSave()
    
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
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.get_report_page_all(segments)

    return render_template_wrap(
        'report_main.html', **_default,
        **data,
        ICON_CDN_LINK=ICON_CDN_LINK,
    )

@SERVER.route("/reports/<report_id>/download")
def download_logs(report_id):
    return send_from_directory(LOGS_RAW_DIR, f"{report_id}.7z")

@SERVER.route("/reports/<report_id>/player/<source_name>/")
def player(report_id, source_name):
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')
    sGUID = report.name_to_guid(source_name)
    tGUID = request.args.get('target')
    data = report.player_info_all(segments, sGUID, tGUID)

    return render_template_wrap(
        'dmg_done2.html', **_default,
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

@SERVER.route("/reports/<report_id>/spell/<spell_id>/")
def spells(report_id, spell_id: str):
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.spell_count_all(segments, spell_id)

    return render_template_wrap(
        'spells_page.html', **_default,
        **data,
    )

@SERVER.route("/reports/<report_id>/consumables/")
def consumables(report_id):
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.potions_all(segments)

    return render_template_wrap(
        'consumables.html', **_default,
        **data,
    )

@SERVER.route("/reports/<report_id>/all_auras/")
def all_auras(report_id):
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

    data = report.auras_info_all(segments)

    return render_template_wrap(
        'all_auras.html', **_default,
        **data,
    )

@SERVER.route("/reports/<report_id>/damage/")
def damage_targets(report_id):
    _default = request.default_params
    segments = _default.pop('segments')
    report = load_report(report_id)
    data = report.useful_damage_all(segments, _default["boss_name"])

    return render_template_wrap(
        'damage_target.html', **_default,
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
        _default = request.default_params

        return render_template(
            'compare.html', **_default,
        )
    elif request.method == 'POST':
        request_data = request.get_json(force=True, silent=True)
        if request_data is None:
            request_data = request.form
        class_name = request_data.get('class')
        if not class_name:
            return "{}"
        
        _default = request.default_params
        segments = _default.pop('segments')
        report = load_report(report_id)
        return report.get_comp_data(segments, class_name)

@SERVER.route("/reports/<report_id>/valks/")
def valks(report_id):
    _default = request.default_params
    segments = _default.pop('segments')
    report = load_report(report_id)
    data = report.valk_info_all(segments)

    return render_template_wrap(
        'valks.html', **_default,
        **data,
    )

@SERVER.route("/reports/<report_id>/deaths/")
def deaths(report_id):
    _default = request.default_params
    segments = _default.pop('segments')
    report = load_report(report_id)
    guid = request.args.get("target")
    data = report.get_deaths(segments, guid)

    return render_template_wrap(
        'deaths.html', **_default,
        **data,
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
    _default = default_params(report_id, request)
    report = load_report(report_id)
    segments = _default.pop('segments')

    return render_template(
        'custom_search.html', **_default,
    )
        

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

@SERVER.route("/reports/<report_id>/player_auras/<player_name>/")
def player_auras(report_id, player_name):
    _default = request.default_params
    report = load_report(report_id)
    segments = _default.pop('segments')

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
        'player_auras.html', **_default,
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


if __name__ == "__main__":
    SERVER.run(host="0.0.0.0", port=5000, debug=True)
