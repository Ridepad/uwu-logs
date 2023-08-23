import json
import os
import shutil
import zlib
from pathlib import Path

real_path = os.path.realpath(__file__)
PATH_DIR = os.path.dirname(real_path)
REPORTS_ALLOWED = os.path.join(PATH_DIR, "__allowed.txt")
REPORTS_PRIVATE = os.path.join(PATH_DIR, "__private.txt")

def get_mtime(path):
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return 0.0

def cache_file_until_new(fname, callback):
    data = None
    last_mtime = -1.0
    def inner():
        nonlocal data, last_mtime
        current_mtime = get_mtime(fname)
        if current_mtime > last_mtime:
            data = callback()
            last_mtime = current_mtime + 10
        return data
    return inner


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def get_backup_folder(folder):
    folder_backup = list(Path(folder).parts)
    folder_backup[1] = "mnt"
    folder_backup = Path(*folder_backup)
    return folder_backup

def new_folder_path(root: str, name: str, check_backup=False):
    folder = os.path.join(root, name)
    if os.path.isdir(folder):
        return folder
    
    if check_backup:
        folder_backup = get_backup_folder(folder)
        if os.path.isdir(folder_backup):
            shutil.copytree(folder_backup, folder)
            return folder

    create_folder(folder)
    return folder

def create_new_folders(root, *names):
    for name in names:
        new_folder_path(root, name)

def fix_extension(ext: str):
    if ext[0] == '.':
        return ext
    return f".{ext}"

def add_extension(path: str, ext=None):
    if ext is not None:
        ext = fix_extension(ext)
        if not path.endswith(ext):
            path = path.split('.')[0]
            return f"{path}{ext}"
    return path

def save_backup(path):
    if os.path.isfile(path):
        old = f"{path}.old"
        if os.path.isfile(old):
            os.remove(old)
        os.rename(path, old)

def json_read(path: str):
    path = add_extension(path, '.json')
    try:
        with open(path) as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}

def json_read_no_exception(path: str):
    path = add_extension(path, '.json')
    with open(path) as file:
        return json.load(file)

def json_write(path: str, data, backup=False, indent=2, sep=None):
    path = add_extension(path, '.json')
    if backup:
        save_backup(path)
    with open(path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, default=sorted, indent=indent, separators=sep)


def bytes_read(path: str, ext=None):
    path = add_extension(path, ext)
    try:
        with open(path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        return b''

def bytes_write(path: str, data: bytes, ext=None):
    path = add_extension(path, ext)
    with open(path, 'wb') as file:
        file.write(data)


def zlib_decompress(data: bytes):
    return zlib.decompress(data)

def zlib_text_read(path: str):
    path = add_extension(path, '.zlib')
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return data.decode()


def file_read(path: str, ext=None):
    path = add_extension(path, ext)
    # try:
    #     raw = bytes_read(path, ext)
    #     return raw.decode()
    # except Exception as e:
    #     print(f"[file_read] {e}")

    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def file_write(path: str, data: str, ext=None):
    path = add_extension(path, ext)
    with open(path, 'w') as f:
        f.write(data)


def get_folders(path) -> list[str]:
    return sorted(next(os.walk(path))[1])

def get_files(path) -> list[str]:
    return sorted(next(os.walk(path))[2])

def get_all_files(path=None, ext=None):
    if path is None:
        path = '.'
    files = get_files(path)
    if ext is None:
        return files
    ext = fix_extension(ext)
    return [file for file in files if file.endswith(ext)]

def get_logs_filter(filter_file: str):
    return file_read(filter_file).splitlines()

def get_folders_filter(folders: list[str], filter_str: str=None, private_only=True):
    if filter_str is not None:
        folders = [name for name in folders if filter_str in name]
    if private_only:
        filter_list = get_logs_filter(REPORTS_PRIVATE)
        folders = [name for name in folders if name not in filter_list]
    return folders

def _get_privated_logs():
    return file_read(REPORTS_PRIVATE).splitlines()

get_privated_logs = cache_file_until_new(REPORTS_PRIVATE, _get_privated_logs)
