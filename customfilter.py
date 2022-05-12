import _main

def main(logs):
    # if name, guid, spellname filter x in line
    for line in logs:
        if 'Nomadra' in line:
            print(line)

if __name__ == "__main__":
    name = "210702-Illusion"
    LOGS = _main.THE_LOGS(name)
    logs = LOGS.get_logs()
    enc_data = LOGS.get_enc_data()
    s,f = enc_data['rotface'][-1]
    logs = logs[s:f]
    main(logs)