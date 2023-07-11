import os
import subprocess
from datetime import datetime
from sys import platform

from constants import LOGS_RAW_DIR, PATH_DIR, logs_edit_time

EXTRACTED_LOGS_NAME = "logs.txt"
ARCHIVE_INFO_LABELS = ["date", "time", "attr", "size", "compressed", "name"]

if platform.startswith("linux"):
    EXE_7Z = os.path.join(PATH_DIR, "7zz")
elif platform == "win32":
    EXE_7Z = os.path.join(PATH_DIR, "7z.exe")
else:
    raise RuntimeError("Unsupported OS")

def get_archive_info(full_archive_path):
    cmd_list = [EXE_7Z, "l", full_archive_path]
    with subprocess.Popen(cmd_list, stdout=subprocess.PIPE) as p:
        try:
            return p.stdout.read().decode().splitlines()
        except Exception:
            return

def get_file_info_dict(line: str):
    a = line.split(maxsplit=5)
    if len(a) == 5:
        a.insert(4, "0")
    return dict(zip(ARCHIVE_INFO_LABELS, a))

def get_text_file(full_archive_path):
    archive_output = get_archive_info(full_archive_path)
    output_filtered = [
        get_file_info_dict(line)
        for line in archive_output
        if ".txt" in line
    ]
    try:
        return max(output_filtered, key=lambda x: int(x["size"]))
    except ValueError:
        return

def get_archive_id(full_archive_path: str):
    if not os.path.isfile(full_archive_path):
        return

    archive_output = get_archive_info(full_archive_path)
    last_line = archive_output[-1]
    if "file" not in last_line:
        last_line = archive_output[-3]
        if "file" not in last_line:
            return
    
    date, time, size, _ = last_line.split(maxsplit=3)
    time = time.replace(':', '-')
    return f"{date}--{time}--{size:0>11}"

def get_extracted_file(upload_dir: str):
    for _file_name in os.listdir(upload_dir):
        if _file_name.endswith(".txt"):
            return os.path.join(upload_dir, _file_name)
    
def extract(full_archive_path, file_name, extract_to=None):
    if extract_to is None:
        extract_to = os.path.dirname(full_archive_path)
    cmd = [EXE_7Z, 'e', full_archive_path, f"-o{extract_to}", "-y", "--", file_name]
    subprocess.call(cmd)
    extracted_file = get_extracted_file(extract_to)
    if not extracted_file:
        return
    
    new_name = os.path.join(extract_to, EXTRACTED_LOGS_NAME)
    os.replace(extracted_file, new_name)
    return new_name

def get_archive_data(full_archive_path):
    file_id = get_archive_id(full_archive_path)
    if file_id is None:
        return
    
    text_file = get_text_file(full_archive_path)
    if text_file is None:
        return
    
    extracted_file = extract(full_archive_path, text_file["name"])
    if extracted_file is None:
        return

    mod_time = logs_edit_time(extracted_file)
    mtime = os.path.getmtime(extracted_file)
    year = datetime.fromtimestamp(mtime).year
    return {
        "file_id": file_id,
        "mod_time": mod_time,
        "year": year,
        "path": full_archive_path,
        "extracted": extracted_file,
    }

def valid_raw_logs(logs_id):
    archive_path = os.path.join(LOGS_RAW_DIR, f"{logs_id}.7z")
    return get_archive_id(archive_path) is not None

def archive_file(archive_path: str, file_path: str):
    if os.path.isfile(archive_path):
        os.remove(archive_path)
    cmd = [EXE_7Z, 'a', archive_path, file_path, '-m0=PPMd', '-mo=11', '-mx=9']
    subprocess.call(cmd)
