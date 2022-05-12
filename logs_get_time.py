import _main
import constants

@constants.running_time
def ujiowfuiwefhuiwe_back_up(logs: list[str]) -> list[int]:
    times = []
    l0 = logs[0]
    i = l0.index('.')
    last_minutes, last_seconds = int(l0[i-5:i-3]), int(l0[i-2:i])
    for n, line in enumerate(logs):
        i = line.index('.')
        minutes, seconds = int(line[i-5:i-3]), int(line[i-2:i])
        sec_diff = seconds - last_seconds
        min_diff = minutes - last_minutes
        if min_diff:
            if min_diff < 0:
                min_diff += 60
            sec_diff += min_diff * 60
            last_minutes = minutes
        if sec_diff:
            for _ in range(sec_diff):
                times.append(n)
            last_seconds = seconds
    return times

@constants.running_time
def ujiowfuiwefhuiwe(logs: list[str]) -> list[int]:
    times = []
    l0 = logs[0]
    i = l0.index('.')
    if i != logs[-1].index('.'):
        return ujiowfuiwefhuiwe_back_up(logs)
    last_minutes, last_seconds = int(l0[i-5:i-3]), int(l0[i-2:i])
    for n, line in enumerate(logs):
        minutes, seconds = int(line[i-5:i-3]), int(line[i-2:i])
        sec_diff = seconds - last_seconds
        min_diff = minutes - last_minutes

        if min_diff:
            if min_diff < 0:
                min_diff += 60
            sec_diff += min_diff * 60
            last_minutes = minutes
        
        if sec_diff:
            for _ in range(sec_diff):
                times.append(n)
            last_seconds = seconds
        
    return times

def check_if_same_length(logs, times):
    l0 = logs[0].split(',')[0]
    ll = logs[-1].split(',')[0]
    d0 = constants.to_dt(l0)
    dd = constants.to_dt(ll)
    L = (dd-d0).seconds
    print(f'LEN LOGS:      {L}')
    print(f'LEN TIMES:     {len(times)}')

def __redo(name):
    print(name)
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    data = ujiowfuiwefhuiwe(logs)
    path = report.relative_path('TIMESTAMP_DATA')
    constants.json_write(path, data, indent=None)

if __name__ == '__main__':
    __redo("22-04-14--20-27--Inia")
    # constants.redo_data(__redo)
