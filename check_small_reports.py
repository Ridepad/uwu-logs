import os
import constants
import shutil

SIZE_CHECK = 4*1024*1024

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
LOGS_DIR = os.path.join(DIR_PATH, "LogsDir")
TRASH = os.path.join(DIR_PATH, "trash")
UPLOADS_DIR = os.path.join(DIR_PATH, "uploads")
PARSED_DIR = os.path.join(UPLOADS_DIR, "__parsed__")

files = constants.get_all_files(PARSED_DIR, 'txt')

def move_shit(file: str):
    report_id = file.split('.')[0]
    folder1 = os.path.join(LOGS_DIR, report_id)
    constants.create_folder(folder1)
    folder2 = os.path.join(TRASH, report_id)
    filename = os.path.join(PARSED_DIR, file)
    filename_trash = os.path.join(folder2, file)
    print(folder1)
    print(folder2)
    print(filename)
    print(filename_trash)
    shutil.move(folder1, folder2)
    shutil.move(filename, filename_trash)
    return report_id

s = set()
for file in files:
    filename = os.path.join(PARSED_DIR, file)
    if os.path.getsize(filename) < SIZE_CHECK:
        move_shit(file)
        # report_id = file.split('.')[0]
        # print(file, os.path.getsize(filename))
        # s.add(report_id)
# z = sorted(s)
# print(z)
# report_id = z[0]
# folder1 = f"{LOGS_DIR}\{report_id}"
# folder2 = f"{TRASH}\{report_id}"
# print(folder1)
# print(folder2)
# shutil.move(folder1, folder2)