
from constants import running_time

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

@running_time
def ujiowfuiwefhuiwe(logs: list[str]) -> list[int]:
    times = []
    l0 = logs[0]
    i = l0.index('.')
    if i != logs[-1].index('.'):
        return ujiowfuiwefhuiwe_back_up(logs)
    last_minutes, last_seconds = int(l0[i-5:i-3]), int(l0[i-2:i])
    for n, line in enumerate(logs):
        try:
            minutes, seconds = int(line[i-5:i-3]), int(line[i-2:i])
        except ValueError:
            continue
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
