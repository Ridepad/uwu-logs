from pydantic import BaseModel
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)

import parser_all
from api_db import DataCompressed
from top_gear import GearDB
from h_debug import Loggers

try:
    import _validate
except ImportError:
    _validate = None

app = FastAPI()
LOGGER = Loggers.server_gear

def add_log_entry(ip, method, msg):
    LOGGER.info(f"{ip:>15} | {method:<7} | {msg}")

def real_ip(request: Request):
    ip = request.client.host
    if not ip:
        ip = request.headers.get('x-real-ip')
    if not ip:
        ip = "0.0.0.0"
    return ip

def request_format(request: Request):
    try:
        msg = request.scope["path"]
        if request.query_params:
            msg = f"{msg}?{request.query_params}"
    except KeyError:
        msg = str(request.url)

    return f"{msg} | {request.headers.get('User-Agent')}"

def add_log_entry_wrap(request: Request, method: str=None):
    ip = real_ip(request)
    msg = request_format(request)
    if not method:
        method = request.method
    add_log_entry(ip, method, msg)

@app.middleware("http")
async def log_connection(request: Request, call_next):
    add_log_entry_wrap(request)
    return await call_next(request)

def make_response_compressed_headers(z: DataCompressed):
    response = Response(content=z.data, media_type="application/json")
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = str(z.size_compressed)
    response.headers["Content-Length-Full"] = str(z.size)
    return response

@app.get('/gear/{server}/{player_name}')
def rank(server: str, player_name: str):
    try:
        z = GearDB(server).get_player_data(player_name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    r = make_response_compressed_headers(z)
    r.headers["Cache-Control"] = "public, max-age=900"
    r.headers["ETag"] = z.gear_id()
    return r

def check_rate_limit(request: Request, type: str, id: str):
    if not _validate:
        return
    
    ip = real_ip(request)
    _limit = _validate.rate_limited_missing(ip, type, id)
    if not _limit:
        return

    add_log_entry_wrap(request, "SPAM")

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
def missing(request: Request, response: Response, resource: Missing = Depends()):
    check_rate_limit(request, type=resource.type, id=resource.id)

    return_code = 400
    if resource.type == "enchant":
        return_code = parser_all.Ench(resource.id).load()
    elif resource.type == "icon":
        return_code = parser_all.Icon(resource.id).load()
    elif resource.type == "item":
        return_code = parser_all.Item(resource.id).load()
    response.status_code = return_code
