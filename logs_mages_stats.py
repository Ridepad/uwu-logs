import constants

SPELLS = {
    '42891': 'Pyroblast on Lich King',
    '42833': 'Fireball on Lich King',
    '55362': 'Living Bomb on Lich King',
    '55360': 'Living Bomb periodic on Lich King',
}

PERIODIC = {'55360', }

def get_avgs(guid, _data):
    crits = _data['1']
    nocrits = _data['nil']
    len_crits = len(crits)
    len_nocrits = len(nocrits)
    total_casts = len_crits + len_nocrits
    avg_crit = sum(crits)/ len_crits
    avg_nocrit = sum(nocrits) / len_nocrits
    avg_hit = (sum(crits)+sum(nocrits))  / total_casts
    chance = len_crits / total_casts * 100
    return {
        'guid': guid,
        'chance': chance,
        'avg_crit': avg_crit,
        'avg_nocrit': avg_nocrit,
        'avg_hit': avg_hit,
        'casts': total_casts
    }

HEADER_LINE = "PLAYER NAME  | CRIT % |  HITS |  AVGHIT |  AVGCRT | AVGNOTC"

def print_report_line(p_data, players):
    __data = [
        f"{players[p_data['guid']]:<12}",
        f"{p_data['chance']:>5.2f}%",
        f"{p_data['casts']:>5}",
        f"{p_data['avg_hit']:>7.1f}",
        f"{p_data['avg_crit']:>7.1f}",
        f"{p_data['avg_nocrit']:>7.1f}",
    ]
    print(' | '.join(__data))



# @constants.running_time
def get_all_spell_data(logs: list[str], spell_id: str):
    data = {}
    DAMAGE = "C_DAMAGE," if spell_id in PERIODIC else "L_DAMAGE,"

    for line in logs:
        if spell_id not in line:
            continue

        if '0xF130008EF5' not in line:
            continue

        if DAMAGE not in line:
            continue

        _, flag, sguid, _, tguid, _, sp_id, _, _, dmg, over, _, res, _, absrb, crit, _ = line.split(',', 16)
        if '0xF130008EF5' not in tguid:
            continue
        if sp_id != spell_id:
            continue
        d = int(dmg) - int(over) + int(res)
        data.setdefault(sguid, {}).setdefault(crit, []).append(d)

    __data = [get_avgs(guid, _data) for guid, _data in data.items()]
    return sorted(__data, reverse=True, key=lambda x: x['chance'])

def main():
    import logs_main

    name = "22-03-12--21-04--Nomadra"
    name = "22-03-05--20-56--Nomadra"
    name = "22-03-26--22-02--Nomadra"
    name = "22-04-09--21-05--Nomadra"
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    players = report.get_players_guids()
    s,f = enc_data["The Lich King"][-2]
    logs = logs[s:f]
    # path = f"LogsDir/{name}"
    # logs_path = f"{path}/LOGS_CUT"
    # logs_raw = constants.zlib_text_read(logs_path)
    # logs = constants.logs_splitlines(logs_raw)
    # players = constants.json_read(f"{path}/PLAYERS_DATA")
    # enc_data = constants.json_read(f"{path}/ENC_DATA")
    for spell_id, desc in SPELLS.items():
        sorted_data = get_all_spell_data(logs, spell_id)
        print()
        print(desc)
        print(HEADER_LINE)
        for __player in sorted_data:
            print_report_line(__player, players)


main()