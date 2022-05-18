import os

import constants
import logs_upload

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
LOGS_RAW = os.path.join(DIR_PATH, "LogsRaw")
LEGACY_DIR = os.path.join(LOGS_RAW, "legacy")
UPLOADS_DIR = os.path.join(DIR_PATH, "uploads")
PARSED_DIR = os.path.join(UPLOADS_DIR, "__parsed__")

def get_id(filename: str):
    name, ext = filename.split('.')
    return int(name.split('_')[-1])

def save_error(name):
    full_name = os.path.join(PARSED_DIR, f"{name}.error")
    open(full_name, 'w').close()
REDO = False
def doshit(name):
    full_name = os.path.join(LEGACY_DIR, name)
    t = logs_upload.upload_legacy(full_name, redo=REDO)
    if t is not None:
        try:
            t.start()
            t.join()
        except:
            save_error(name)

if __name__ == "__main__":
    from multiprocessing import Pool
    # for file in all_files[:50]:
    all_files = [
        # 'upload_12198.zip',
        # 'upload_12225.zip',
        # 'upload_12205.zip',
        # 'upload_10982.zip',
        # 'upload_10254.zip',
        # 'upload_10253.zip',
    ]
    all_files = constants.get_all_files(LEGACY_DIR, 'zip')
    all_files = sorted(all_files, key=lambda x: get_id(x))
    all_files = all_files[::-1]
    all_files = all_files[800:1000]
    total_len = len(all_files)
    for n, file in enumerate(all_files, 1):
        print(f"[UPLOAD PROGRESS] {n:>5} /{total_len:>5}")
        doshit(file)
        
    # with Pool(3) as p:
        # p.map(doshit, all_files)
