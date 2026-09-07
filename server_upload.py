from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from constants import SERVERS
from c_path import Directories
from logs_upload import (
    CurrentUploads,
    LogsArchive,
    UploadChunk,
    LOGGER_UPLOADS,
)

app = FastAPI()
TEMPLATES = Jinja2Templates(directory="templates")

class CurrentUploadsProgress(dict[str, LogsArchive]):
    ...

CURRENT_UPLOADS = CurrentUploads()
CURRENT_UPLOADS_PROGRESS = CurrentUploadsProgress()

def real_ip(request: Request):
    ip = request.client.host
    if not ip:
        ip = request.headers.get('x-real-ip')
    if not ip:
        ip = "0.0.0.0"
    return ip

def check_upload_id_header(request: Request):
    try:
        return request.headers['x-upload-id']
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="must include [x-upload-id] header with a non empty value",
        )

def check_chunk_header(request: Request):
    try:
        return int(request.headers.get('x-chunk'))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="must include [x-upload-id] header with an integer of a chunk",
        )
    
    
@Directories.top.cache_until_new_self
def get_servers(folder):
    print(">>>>>>>>>> get_servers")
    s = set((
        file_path.stem
        for file_path in folder.iterdir()
        if file_path.suffix == ".db"
    ))
    servers = s - set(SERVERS.values())
    return sorted(servers)

@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/upload", response_class=HTMLResponse)
async def upload_get(request: Request):
    return TEMPLATES.TemplateResponse(
        request=request,
        name="upload.html",
        context={
            "SERVERS": get_servers(),
        },
    )

@app.post("/upload")
async def upload_post(request: Request, response: Response):
    ip = real_ip(request)
    current_upload = CURRENT_UPLOADS[ip]

    final_piece = request.headers.get('content-type') == 'application/json'
    if not final_piece:
        data = await request.body()
        upload_id = check_upload_id_header(request)
        chunk_id = check_chunk_header(request)
        chunk = UploadChunk(
            data=data,
            chunk_id=chunk_id,
            upload_id=upload_id,
        )
        current_upload.add_chunk(chunk)
        return None
    
    try:
        file_data = await request.json()
    except Exception:
        file_data = {}
    try:
        archive = current_upload.save_uploaded_file(file_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="file was corrupted during upload",
        )
    except OSError:
        raise HTTPException(
            status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Couldn't complete upload.  No disk space left on the server.",
        )
    
    archive.start_processing()
    CURRENT_UPLOADS_PROGRESS[ip] = archive
    response.status_code = status.HTTP_201_CREATED
    return None

@app.get("/upload_progress")
async def upload_progress(request: Request, response: Response):
    ip = real_ip(request)
    uploads_progress = CURRENT_UPLOADS_PROGRESS.get(ip)
    if uploads_progress is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return
        
    # Build the response before removing the completed upload from memory.
    # The old order deleted the only progress object first, so any exception
    # while serializing status turned into a one-off HTTP 500 and the next poll
    # returned 204, making the original parser error impossible to diagnose.
    try:
        progress = uploads_progress.status_dict
    except Exception as exc:
        LOGGER_UPLOADS.exception("upload_progress status serialization failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload progress failed: {type(exc).__name__}: {exc}",
        ) from exc

    if not uploads_progress.thread.is_alive():
        CURRENT_UPLOADS_PROGRESS.pop(ip, None)

    return progress


if __name__ == "__main__":
    # testing without nginx to prevent cors
    from fastapi.responses import RedirectResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

    from h_other import Ports

    app.mount("/static", StaticFiles(directory="static"))

    @app.get("/")
    def root_path():
        return RedirectResponse("/upload")

    @app.exception_handler(404)
    def not_found_exception_handler(request: Request, exc: HTTPException):
        if request.scope["root_path"] in ["/cache", "/static", ]:
            return Response(
                content="Not Found",
                status_code=404,
            )
        _url = str(request.url).replace(f":{Ports.upload}/", f":{Ports.main}/")
        return RedirectResponse(
            url=_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    print("STARTING UPLOAD SERVER")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Ports.upload)
