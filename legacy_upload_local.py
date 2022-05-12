import logs_upload
import constants

import os
from multiprocessing import Pool

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
LOGS_RAW = os.path.join(DIR_PATH, "LogsRaw")
LEGACY_DIR = os.path.join(LOGS_RAW, "legacy")
all_files = constants.get_all_files(LEGACY_DIR, 'zip')

def get_id(filename: str):
    name, ext = filename.split('.')
    return int(name.split('_')[-1])

all_files = sorted(all_files, key=lambda x: get_id(x))

def doshit(name):
    full_name = os.path.join(LEGACY_DIR, name)
    t = logs_upload.upload_legacy(full_name)
    if t is not None:
        t.start()
        t.join()

if __name__ == "__main__":
    # for file in all_files[:50]:
    all_files = all_files[-250:]
    # for file in all_files:
        # doshit(file)
    with Pool(3) as p:
        p.map(doshit, all_files)
