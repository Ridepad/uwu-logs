from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import parser_all
from api_top_db_v2 import TopDataCompressed
from c_path import Directories, Files
from constants import GEAR
from h_debug import Loggers
from top_character import Character, CharacterValidation
from top import Top, TopValidation
from top_points import Points, PointsValidation
from top_pve_stats import PveStats, PveStatsValidation, SPECS_DATA_NOT_IGNORED
from top_raid_rank import RaidRank, RaidRankValidation
from top_speedrun import Speedrun, SpeedrunValidation

from top_gear import GearDB

try:
    import _validate
except ImportError:
    _validate = None


app = FastAPI(
    swagger_ui_parameters={"syntaxHighlight.theme": "arta"},
)
TEMPLATES = Jinja2Templates(directory="templates")
TEMPLATES.env.trim_blocks = True
TEMPLATES.env.lstrip_blocks = True

LOGGER_CONNECTIONS = Loggers.connections

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

def add_log_entry(ip, method, msg):
    LOGGER_CONNECTIONS.info(f"{ip:>15} | {method:<7} | {msg}")

def real_ip(request: Request):
    ip = request.client.host
    if not ip:
        ip = request.headers.get('x-real-ip')
    if not ip:
        ip = "0.0.0.0"
    return ip

async def add_log_entry_wrap(request: Request, method: str=None):
    ip = real_ip(request)
    msg = await request_format(request)
    if not method:
        method = request.method
    LOGGER_CONNECTIONS.info(f"{ip:>15} | {method:<7} | {msg}")

async def request_format(request: Request):
    msg = str(request.url)
    try:
        data = await request.body()
        msg = f"{msg} | {data.decode()}"
    except UnicodeDecodeError:
        pass
    return f"{msg} | {request.headers.get('User-Agent')}"

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    await add_log_entry_wrap(request)
    return await call_next(request)


def make_response_compressed_headers(z: TopDataCompressed):
    response = Response(content=z.data, media_type="application/json")
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = str(z.size_compressed)
    response.headers["Content-Length-Full"] = str(z.size)
    return response

@app.post('/top_points')
async def top_post(request: Request, data: PointsValidation):
    mimetype = request.headers.get('Content-Type')
    if mimetype != "application/json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="requires [application/json] mimetype/content-type",
        )
    
    z = Points(data).parse_top_points()
    return make_response_compressed_headers(z)

@app.post('/top_speedrun')
async def rank(data: SpeedrunValidation):
    z = Speedrun(data).data()
    return make_response_compressed_headers(z)

@app.post('/top')
async def top_post(request: Request, data: TopValidation):
    mimetype = request.headers.get('Content-Type')
    if mimetype != "application/json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="requires [application/json] mimetype/content-type",
        )
    
    z = Top(data).get_data()
    return make_response_compressed_headers(z)

@app.post('/pve_stats')
async def pve_stats(data: PveStatsValidation):
    return PveStats(data).get_data()

@app.post('/character')
async def character(data: CharacterValidation):
    return Character(data).get_player_data()

@app.get('/character/{server}/{name}/{spec}')
async def character(server, name, spec):
    data = CharacterValidation(server=server, name=name, spec=spec)
    return Character(data).get_player_data()

@app.post('/rank')
async def rank(data: RaidRankValidation):
    return RaidRank(data).points()

@app.get('/gear/{server}/{player_name}')
async def rank(server: str, player_name: str):
    z = GearDB(server).get_player_data(player_name)
    r = make_response_compressed_headers(z)
    r.headers["Cache-Control"] = "public, max-age=900"
    r.headers["ETag"] = z.gear_id()
    return r

async def check_rate_limit(request: Request, type: str, id: str):
    if not _validate:
        return
    
    ip = real_ip(request)
    _limit = _validate.rate_limited_missing(ip, type, id)
    if not _limit:
        return

    await add_log_entry_wrap(request, "SPAM")
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=str(_limit),
        headers={
            "Retry-After": str(_limit),
        }
    )

class Missing(BaseModel):
    id: str
    type: str

@app.put("/missing")
async def missing(item: Missing, request: Request, response: Response):
    await check_rate_limit(request, type=item.type, id=item.id)

    return_code = 400
    if item.type == "enchant":
        return_code = parser_all.Ench(item.id).load()
    elif item.type == "icon":
        return_code = parser_all.Icon(item.id).load()
    elif item.type == "item":
        return_code = parser_all.Item(item.id).load()
    response.status_code = return_code


######## Get endpoints to prevent cors

@app.get("/")
def root_path():
    return RedirectResponse("/top")

@app.get("/top", deprecated=True, description="Used to prevent CORS")
def top_get(request: Request):
    servers = get_servers()
    return TEMPLATES.TemplateResponse(
        request=request,
        name="top.html",
        context={
            "SERVERS": servers,
            "REPORT_NAME": "Top",
        },
    )

@app.get("/character", deprecated=True, description="Used to prevent CORS")
def character_get(request: Request):
    servers = get_servers()
    return TEMPLATES.TemplateResponse(
        request=request,
        name="character.html",
        context={
            "SERVERS": servers,
        } | GEAR,
    )

@app.get("/pve_stats", deprecated=True, description="Used to prevent CORS")
def pve_stats_get(request: Request):
    servers = get_servers()
    return TEMPLATES.TemplateResponse(
        request=request,
        name="pve_stats.html",
        context={
            "SPECS_BASE": SPECS_DATA_NOT_IGNORED,
            "SERVERS": servers,
        },
    )


if __name__ == "__main__":
    # testing without nginx
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import RedirectResponse

    from h_other import Ports

    app.mount("/static", StaticFiles(directory=Directories.static))

    _NO_REDIRECT_ROOTS = [
        "/static",
    ]

    def redirect_to_main_server(url):
        _url = str(url).replace(f":{Ports.top}/", f":{Ports.main}/")
        return RedirectResponse(
            url=_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    
    @app.exception_handler(404)
    def not_found_exception_handler(request: Request, exc: HTTPException):
        if request.scope["root_path"] not in _NO_REDIRECT_ROOTS:
            return redirect_to_main_server(request.url)
        
        return Response(
            content="Not Found",
            status_code=404,
        )

    print("STARTING TOP DB SERVER")
    uvicorn.run(app, host="0.0.0.0", port=Ports.top)
