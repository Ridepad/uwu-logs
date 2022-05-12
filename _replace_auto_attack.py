from typing import List
import _main
import constants


@constants.running_time
def join_logs(logs: List[str], sep: str='\n'):
    return sep.join(logs)

@constants.running_time
def write_cut(logs: str, file_name: str):
    with open(file_name, 'w') as f:
        f.write(logs)

NEW_SWING = ["1", "Melee", "0x1"]

def format_line(line: str):
    if "SWING" in line:
        line_ = line.split(',')
        line_[6:6] = NEW_SWING
        line = ','.join(line_)
    return line

def replaced_swings(logs: List[str]):
    return [format_line(line) for line in logs]

def main(name):
    print(name)
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    logs = replaced_swings(logs)
    logs_to_write = join_logs(logs)
    logs_cut_file_name = f"./LogsDir/{name}/Logs_cut.txt"
    write_cut(logs_to_write, logs_cut_file_name)

@constants.running_time
def redo_all():
    import os
    from multiprocessing import Pool
    folders = next(os.walk('./LogsDir/'))[1]
    with Pool(8) as p:
        p.map(main, folders)
    print('done')

if __name__ == "__main__":
    if 0:
        redo_all()
    else:
        name = "21-09-03--21-05--Nomadra"
        main(name)