import constants

@constants.running_time
def logs_format(logs):
    logs = logs.replace('"', '')
    logs = logs.replace('  ', ',')
    return logs.splitlines()

@constants.running_time
def combine(logs, line_separator):
    return line_separator.join(logs)

@constants.running_time
def write_cut(logs, name):
    with open(name, 'w') as f:
        f.write(logs)

@constants.running_time
def main(logs):
    z = []
    for line in logs:
        line = line.split(',')
        if line[1] == 'SPELL_CAST_FAILED':
            continue
        del line[7]
        del line[4]
        z.append(','.join(line))
    return z

@constants.running_time
def main2(logs):
    z = []
    _append = z.append
    _join = ','.join
    for line in logs:
        line = line.split(',')
        if line[1] == 'SPELL_CAST_FAILED':
            continue
        del line[7]
        del line[4]
        _append(_join(line))
    return z

if __name__ == '__main__':
    LINE_SEPARATOR = constants.LINE_SEPARATOR
    logs_raw_name = constants.LOGS_RAW_NAME
    logs_cut_name = constants.LOGS_CUT_NAME

    logs = constants.logs_read(logs_raw_name)
    logs_raw = logs_format(logs)
    logs = main2(logs_raw)
    logs = main(logs_raw)
    logs = main2(logs_raw)
    logs = main(logs_raw)
    logs2 = main2(logs_raw)
    logs1 = main(logs_raw)
    logs2 = combine(logs2, LINE_SEPARATOR)
    logs1 = combine(logs1, LINE_SEPARATOR)
    print(logs1==logs2)
    # write_cut(logs, logs_cut_name)
