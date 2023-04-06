import os
import subprocess
from datetime import datetime
from sys import platform
from time import perf_counter

from constants import LOGGER_UPLOADS, LOGS_RAW_DIR, PATH_DIR, get_ms_str, logs_edit_time

ARCHIVE_INFO_LABELS = ["date", "time", "attr", "size", "compressed", "name"]
PATH_7Z = None

def get_7zip_linux():
    path_7z_tarxz = os.path.join(PATH_DIR, "7z.tar.xz")
    cmd = ["wget", "https://www.7-zip.org/a/7z2201-linux-x64.tar.xz", "-O", path_7z_tarxz]
    code = subprocess.call(cmd)
    if code != 0:
        LOGGER_UPLOADS.error(f'Error downloading 7z with code: {code}')
        return
    
    path_7z = os.path.join(PATH_DIR, "7zz")
    cmd = ["tar", "-xf", path_7z_tarxz, path_7z]
    code = subprocess.call(cmd)
    if code != 0:
        LOGGER_UPLOADS.error(f'Error extracting 7z with code: {code}')
        return

    cmd = ["unlink", path_7z_tarxz]
    code = subprocess.call(cmd)
    if code != 0:
        LOGGER_UPLOADS.error(f'Error deleting 7z with code: {code}')
        return
    
    return True

def get_7zip_windows():
    print("Downloading 7z...")
    cmd = ["powershell", "-command", "wget", "https://www.7-zip.org/a/7zr.exe", "-O", "7zr.exe"]
    code = subprocess.call(cmd)
    if code != 0:
        LOGGER_UPLOADS.error(f'Error downloading 7z with code: {code}')
        return
    
    return True

def get_7z_path():
    global PATH_7Z
    
    if PATH_7Z is not None:
        pass
    elif platform.startswith("linux"):
        PATH_7Z = os.path.join(PATH_DIR, "7zz")
        if not os.path.isfile(PATH_7Z):
            get_7zip_linux()
    elif platform == "win32":
        PATH_7Z = os.path.join(PATH_DIR, "7zr.exe")
        if not os.path.isfile(PATH_7Z):
            get_7zip_windows()

    return PATH_7Z


def get_archive_info(full_archive_path):
    cmd_list = [get_7z_path(), "l", full_archive_path]
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
    output_filtered = [get_file_info_dict(line) for line in archive_output if ".txt" in line]
    try:
        return max(output_filtered, key=lambda x: int(x["size"]))
    except ValueError:
        return

def get_archive_id(full_archive_path: str):
    archive_output = get_archive_info(full_archive_path)
    last_line = archive_output[-1]
    print(last_line)
    if "file" not in last_line:
        return
    
    a = last_line.split(maxsplit=4)
    date = a[0]
    time = a[1].replace(':', '-')
    size = a[2]
    return f"{date}--{time}--{size:0>11}"

def get_extracted_file(upload_dir: str):
    for _file_name in os.listdir(upload_dir):
        if _file_name.endswith(".txt"):
            return os.path.join(upload_dir, _file_name)
    
def extract(full_archive_path, upload_dir, file_name):
    pc = perf_counter()
    cmd = [get_7z_path(), 'e', full_archive_path, f"-o{upload_dir}", "-y", "--", file_name]
    subprocess.call(cmd)
    extracted_file = get_extracted_file(upload_dir)
    if not extracted_file:
        return
    
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {upload_dir} | Extracted')
    new_name = os.path.join(upload_dir, "logs.txt")
    
    if os.path.isfile(new_name):
        os.remove(new_name)
    
    if extracted_file != new_name:
        os.rename(extracted_file, new_name)
    
    return new_name

def new_archive(full_archive_path, upload_dir):
    file_id = get_archive_id(full_archive_path)
    if file_id is None:
        return
    
    text_file = get_text_file(full_archive_path)
    if text_file is None:
        return
    
    extracted_file = extract(full_archive_path, upload_dir, text_file["name"])
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

def save_raw_logs(logs_id: str, upload_dir: str, forced=False):
    archive_path = os.path.join(LOGS_RAW_DIR, f"{logs_id}.7z")
    if not forced and valid_raw_logs(logs_id):
        LOGGER_UPLOADS.debug(f'            | Exists | {logs_id}')
        return
    
    logs_txt_file = os.path.join(upload_dir, f"{logs_id}.txt")
    if not os.path.isfile(logs_txt_file):
        LOGGER_UPLOADS.error(f'{logs_id} | Cache txt not found')
        return
    
    if forced and os.path.isfile(archive_path):
        os.remove(archive_path)
    
    pc = perf_counter()
    cmd = [get_7z_path(), 'a', archive_path, logs_txt_file, '-m0=PPMd', '-mo=11', '-mx=9']
    subprocess.call(cmd)
    LOGGER_UPLOADS.debug(f'{get_ms_str(pc)} | {logs_id} | Saved raw')


def __test():
    _name = r"77.137.195.179--23-04-05--12-08-01--23_03_24_21_58_Safiyah_Lordaeron.7z"
    _name = r"F:\Python\uwulogs\uploads\uploaded\localhost--22-09-18--09-15-23--upload_9089.zip"
    _name = r"F:\Python\uwulogs\uploads\uploaded\192.168.1.102--22-11-24--00-29-11--wtf.7z"
    _name = r"F:\Python\uwulogs\uploads\uploaded\onefolder.7z"
    _name = r"F:\Python\uwulogs\uploads\uploaded\zerofiles.zip"
    _name = r"F:\Python\uwulogs\uploads\uploaded\twofolders.7z"
    print(_name)
    archive_output = get_archive_info(_name)
    print("="*100)
    for x in archive_output:
        print(x)
    print("="*100)
    text_file = get_text_file(_name)
    print(text_file)
    print(get_archive_id(_name))
    # extract(_name, UPLOADS_DIR, text_file["name"])

if __name__ == "__main__":
    __test()
