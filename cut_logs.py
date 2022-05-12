from typing import List
import constants

ENV_DAMAGE = constants.ENV_DAMAGE

@constants.running_time
def logs_format(logs: str):
    '''replaces shit in logs to make it consistent, then splitlines'''
    logs = logs.replace('"', '')   # names are covered in this shit
    logs = logs.replace('  ', ',') # spaces after timestamp
    logs = logs.replace(', ', ' ') # some spells have "," in name, why?
    return logs.splitlines()

def env_f(line: list[str]):
    name = line[6]
    _hex = hex(int(line[9]))
    if name in ENV_DAMAGE:
        _id = ENV_DAMAGE[name]
    else:
        _id = str(int(max(ENV_DAMAGE.values())) + 1)
        ENV_DAMAGE[_id] = name
        n = f"unusual_spells/ENVIRONMENTAL_DAMAGE-{name}-{_hex}"
        open(n, 'w').close()
    return [_id, name, _hex]

@constants.running_time
def trim_logs(logs: List[str]):
    LOST_SWING = ["1", "Melee", "0x1"]
    SWINGS = {'SWING_MISSED', 'SWING_DAMAGE'}
    _join = ','.join
    
    new_logs: list[str] = []
    _l_a = new_logs.append
    
    for line in logs:
        if line.count('/') > 1:
            continue
        try:
            line = line.split(',')
            if line[1] == 'SPELL_CAST_FAILED':
                continue
            del line[7], line[4]
            if line[1] in SWINGS:
                line[6:6] = LOST_SWING
            elif line[1] == "ENVIRONMENTAL_DAMAGE":
                line[6:7] = env_f(line)
            _l_a(_join(line))
        except IndexError:
            pass
    return new_logs

@constants.running_time
def trim_logs_valid(logs: List[str], validate=False):
    def sort_values(d):
        return {k:sorted(v) for k, v in d.items()}
    LOST_SWING = ["1", "Melee", "0x1"]
    SWINGS = {'SWING_MISSED', 'SWING_DAMAGE'}
    _join = ','.join
    
    new_logs = []
    _l_a = new_logs.append
    
    d = {}

    for line in logs:
        if line.count('/') > 1:
            continue
        try:
            line = line.split(',')
            if line[1] == 'SPELL_CAST_FAILED':
                continue
            del line[7], line[4]
            if line[1] in SWINGS:
                line[6:6] = LOST_SWING
            _line = _join(line)
            _l_a(_line)
            d.setdefault(line[0], []).append(_line)
        except IndexError:
            pass
    if not validate:
        return new_logs
    d = sort_values(d)
    is_valid = d == dict(sorted(d.items()))
    return new_logs, is_valid

@constants.running_time
def join_logs(logs: List[str], sep: str='\n'):
    return sep.join(logs)

@constants.running_time
def write_cut(logs: str, file_name: str):
    with open(file_name, 'w') as f:
        f.write(logs)



def __redo_raw(name):
    name = "21-06-06--19-29--Meownya"
    logs_raw_file_name = r"F:\Python\wow_logs\LogsDir\21-05-09--19-29--Meownya\210509-ATM.txt"
    logs_raw = constants.file_read(logs_raw_file_name)
    logs_raw_formatted = logs_format(logs_raw)
    logs = trim_logs(logs_raw_formatted)
    logs_to_write = join_logs(logs)
    logs_cut_file_name = r"F:\Python\wow_logs\LogsDir\21-05-09--19-29--Meownya\Logs_cut.txt"
    write_cut(logs_to_write, logs_cut_file_name)
    
def __do(logs: List[str]):
    for line in logs:
        if "ENVIRONMENTAL_DAMAGE" in line:
            line = line.split(',')
            line[6:7] = env_f(line)
            line = ','.join(line)
        yield line

@constants.running_time
def __redo(name):
    print(name)
    p = f"./LogsDir/{name}/Logs_cut.txt"
    f = constants.file_read(p)
    logs = f.splitlines()
    ff = __do(logs)
    ff_join = join_logs(ff)
    write_cut(ff_join, p)
    print("DONE:   ", name)

def __redo_all():
    import os
    from multiprocessing import Pool
    folders = next(os.walk('./LogsDir/'))[1]
    with Pool(4) as p:
        p.map(__redo, folders)

if __name__ == '__main__':
    # __redo_all()
    pass