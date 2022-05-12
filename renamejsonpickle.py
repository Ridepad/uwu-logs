import os

from click import FileError

FILE_NAME = "TIMESTAMP_DATA"

def get_logs(dir, file_name):
    for file in next(os.walk(dir))[2]:
        if file_name in file:
            return file

def doshit(ext, file_name):
    for __dir in next(os.walk('LogsDir'))[1]:
        __dir = f"LogsDir/{__dir}"
        f = get_logs(__dir, file_name)
        if not f:
            print(__dir)
            continue
        print(f)
        current_name = f"{__dir}/{f}"
        new_name = f"{__dir}/{file_name}.{ext}"
        try:
            os.rename(current_name, new_name)
        except FileExistsError:
            print(__dir)

doshit('json', "CLASSES_DATA")