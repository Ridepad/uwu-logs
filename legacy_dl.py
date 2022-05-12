from concurrent.futures import ThreadPoolExecutor
import requests
import constants
import os
import shutil


HEADERS = {'User-Agent': 'dlspec'}

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
DL_FOLDER = os.path.join(DIR_PATH, "LogsRaw/legacy")
DL_LINKS_FILE = os.path.join(DIR_PATH, "legacy_dl_links.json")
DL_LINKS_DONE_FILE = os.path.join(DIR_PATH, "legacy_done.json")

CHUNK_SIZE = 16*1024
MEGABYTE = 1024*1024

DL_LINKS = constants.json_read(DL_LINKS_FILE)
DL_LINKS_DONE = constants.json_read(DL_LINKS_DONE_FILE)

LINK_MISSING = {
    "https://legacyplayers.com/uploads/upload_0.zip",
    "https://legacyplayers.com/uploads/upload_1.zip"
}

def dl_archive(link: str):
    DL_ID = link.split('/')[-1]
    DL_ID_STR = f"{DL_ID:>17}"
    if link in DL_LINKS_DONE:
        return f"{DL_ID_STR} exists!"
    if link in LINK_MISSING:
        return f"{DL_ID_STR} missing DL link!"
    
    local_filename = os.path.join(DL_FOLDER, DL_ID)
    if os.path.isfile(local_filename):
        saved_file_size = os.path.getsize(local_filename)
    else:
        saved_file_size = 0
    
    with requests.get(link, stream=True) as response:
        r_file_size = response.headers['Content-Length']
        r_file_size = int(r_file_size)
        same_size = r_file_size == saved_file_size
        print(f"{DL_ID_STR}  {int(same_size)} | {r_file_size:>9} | {saved_file_size:>9}")
        if same_size:
            return f"{DL_ID_STR} exists!"
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
    
    return f'{DL_ID_STR} done!'

def main(guild=None):
    _data = constants.json_read("legacy_icc_10h_data.json")
    if guild:
        _data = [report for report in _data if report['guild'] == guild]
    links = [DL_LINKS[report['link']] for report in _data if report['link'] in DL_LINKS]
    # print(links)
    with ThreadPoolExecutor(3) as executor:
        for result in executor.map(dl_archive, links):
            print(result)

def main():
    with ThreadPoolExecutor(3) as executor:
        for result in executor.map(dl_archive, DL_LINKS.values()):
            print(result)
    # for report in raw_data:
    #     if report['guild'] == guild:
    #         print(report['start'])
    #         prep_dl(report['link'])
def main():
    files = constants.get_all_files('LogsRaw/legacy', 'zip')
    files = [f"https://legacyplayers.com/uploads/{filename}" for filename in files]
    # print(files[-20:])
    with ThreadPoolExecutor(3) as executor:
        for result in executor.map(dl_archive, files):
            print(result)
    # constants.json_write(DL_LINKS_DONE_FILE, files, indent=None)

main()
# dl_archive("https://legacyplayers.com/uploads/upload_8918.zip")
