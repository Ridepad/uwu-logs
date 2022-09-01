import os
import subprocess
import zipfile
from datetime import datetime
from sys import platform
from time import perf_counter

import py7zr

from constants import LOGS_RAW_DIR, LOGGER_UPLOADS, logs_edit_time, get_ms_str

PATH_7Z = "7z"
if platform == "linux" or platform == "linux2":
    PATH_7Z = "7zz"
elif platform == "win32":
    PATH_7Z = "7za.exe"

def get_file_info(file):
    filename: str
    ctime: datetime
    compressed: int
    filename, ctime, compressed = file.filename, file.creationtime, file.compressed
    return filename, ctime, compressed

def get_7z_info(full_path):
    try:
        with py7zr.SevenZipFile(full_path) as archive:
            for file in archive.list():
                if file.filename.endswith('.txt'):
                    return get_file_info(file)
    except (FileNotFoundError, py7zr.exceptions.Bad7zFile):
        return None

def get_zip_info(full_path):
    try:
        with zipfile.ZipFile(full_path) as archive:
            for file in archive.infolist():
                if file.filename.endswith('.txt'):
                    return file.filename, datetime(*file.date_time), file.compress_size
    except (FileNotFoundError, zipfile.BadZipFile):
        return None

def get_archive_info(full_path):
    return get_zip_info(full_path) or get_7z_info(full_path)

def extract(full_path, upload_dir):
    pc = perf_counter()
    cmd = [PATH_7Z, 'e', full_path, '-aoa', f"-o{upload_dir}", "*.txt"]
    code = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    LOGGER_UPLOADS.debug(f'{full_path} | Extracted in {get_ms_str(pc)}')
    return code

def get_extracted_file(upload_dir, file_name):
    for _file_name in os.listdir(upload_dir):
        if _file_name == file_name:
            return os.path.join(upload_dir, _file_name)

def get_archive_id(path):
    _id = get_archive_info(path)
    if _id is None:
        return
    
    name, dt, size = _id
    epoch = int(dt.timestamp())
    return f"{epoch}_{size}"

def new_archive(full_path, upload_dir):
    file_id = get_archive_info(full_path)
    if file_id is None:
        return
    
    name, dt, size = file_id
    epoch = int(dt.timestamp())
    file_id = f"{epoch}_{size}"
    
    code = extract(full_path, upload_dir)
    if code != 0:
        return

    extracted_file = get_extracted_file(upload_dir, name)
    if extracted_file is None:
        return
    
    mod_time = logs_edit_time(extracted_file)
    extracted_file_full = os.path.join(upload_dir, extracted_file)
    mtime = os.path.getmtime(extracted_file_full)
    year = datetime.fromtimestamp(mtime).year
    data = {
        "file_id": file_id,
        "mod_time": mod_time,
        "year": year,
        "path": full_path,
    }
    return data, extracted_file

def bytes_write(data: str, path):
    with open(path, 'wb') as f:
        f.write(data.encode())

def valid_raw_logs(logs_id):
    archive_path = os.path.join(LOGS_RAW_DIR, f"{logs_id}.7z")
    return get_7z_info(archive_path) is not None

def save_raw_logs(logs_id: str, upload_dir: str, forced=False):
    archive_path = os.path.join(LOGS_RAW_DIR, f"{logs_id}.7z")
    if not forced and get_7z_info(archive_path) is not None:
        LOGGER_UPLOADS.debug(f'{logs_id} | Exists')
        return
    
    pc = perf_counter()
    tmp_file_name = os.path.join(upload_dir, f"{logs_id}.txt")
    if not os.path.isfile(tmp_file_name):
        LOGGER_UPLOADS.error(f'{logs_id} | Cache txt not found')
        return
    if forced and os.path.isfile(archive_path):
        os.remove(archive_path)
    
    cmd = [PATH_7Z, 'a', archive_path, tmp_file_name, '-m0=PPMd', '-mo=11', '-mx=9']
    subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    LOGGER_UPLOADS.debug(f'{logs_id} | Done in {get_ms_str(pc)}')

def __test():
    from multiprocessing import Process
    from constants import file_read
    logs_raw = file_read(r"F:\Python\uwulogs\uploads\_test.txt")
    p = Process(target=save_raw_logs, args=('tst', logs_raw, r"F:\Python\uwulogs\uploads"))
    p.start()
    p.join()

if __name__ == "__main__":
    __test()
