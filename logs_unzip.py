import os
import subprocess
import zipfile
from datetime import datetime
from sys import platform

import py7zr

import constants
from constants import UPLOADED


def get_7z_info(full_path) -> tuple[datetime, int]:
    with py7zr.SevenZipFile(full_path) as archive:
        for file in archive.list():
            if file.filename.endswith('.txt'):
                return file.creationtime, file.compressed

def get_zip_info(full_path) -> tuple[datetime, int]:
    with zipfile.ZipFile(full_path) as archive:
        for file in archive.infolist():
            if file.filename.endswith('.txt'):
                return datetime(*file.date_time), file.compress_size

def get_archive_info(full_path):
    try:
        return get_zip_info(full_path)
    except zipfile.BadZipFile:
        try:
            return get_7z_info(full_path)
        except py7zr.exceptions.Bad7zFile:
            return

def extract(full_path, upload_dir):
    print('EXTRACTING:', full_path)
    if platform == "linux" or platform == "linux2":
        file_path = "7zz"
    elif platform == "win32":
        file_path = "7za.exe"
    else:
        print('wtf', platform)
        return
    cmd = [file_path, 'e', full_path, '-aoa', f"-o{upload_dir}", "*.txt"]
    code = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return code

def get_extracted_file(upload_dir):
    for file in os.listdir(upload_dir):
        if ".txt" in file:
            return os.path.join(upload_dir, file)

def new_archive(full_path, upload_dir):
    archive_id = get_archive_info(full_path)
    if archive_id is None:
        return
    
    dt, size = archive_id
    epoch = int(dt.timestamp())
    archive_id = f"{epoch}_{size}"

    if archive_id in UPLOADED:
        return
    
    code = extract(full_path, upload_dir)
    if code == 0:
        extracted_file = get_extracted_file(upload_dir)
        mod_time = constants.logs_edit_time(extracted_file)
        extracted_file_full = os.path.join(upload_dir, extracted_file)
        data = UPLOADED[archive_id] = {"mod_time": mod_time, "file": extracted_file_full, "upload_dir": upload_dir, "year": dt.year}
        return data


def __test():
    name_zip = r"F:\Python\uwulogs\LogsRaw\legacy\upload_11055.zip"
    name_7z = "LogsRaw/22-06-19--04-15--Lismee.7z"
    name = name_7z
    name = r"F:\Python\uwulogs\uploads\legacy\upload_23\t1.7z"
    name = r"F:\Python\uwulogs\uploads\legacy\upload_23\t2.7z"
    name = r"F:\Python\uwulogs\uploads\legacy\upload_23\WoWCombatLog.7z"
    upload_dir = r"F:\Python\uwulogs\uploads\legacy\upload_23"
    name = r"F:\Python\uwulogs\uploads\legacy\upload_23\upload_23.zip"
    data = new_archive(name, upload_dir)
    print(data)
    data = new_archive(name, upload_dir)
    print(data)
    # extract(name, upload_dir)
    # try:
    #     comp, dt = get_zip_info(name)
    # except Exception:
    #     comp, dt = get_7z_info(name)
    # dt = int(dt.timestamp())
    # print(comp, dt)

if __name__ == "__main__":
    __test()
