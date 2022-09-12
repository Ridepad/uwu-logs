
from constants import running_time

@running_time
def get_timestamps(logs: list[str]):
    times: list[int] = []
    first_line = logs[0]
    i = first_line.index('.')
    last_minutes, last_seconds = int(first_line[i-5:i-3]), int(first_line[i-2:i])
    for n, line in enumerate(logs):
        try:
            minutes, seconds = int(line[i-5:i-3]), int(line[i-2:i])
        except ValueError:
            # date change or bugged line 
            i = line.index('.')
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
            times.extend([n]*sec_diff)
            last_seconds = seconds
        
    return times
