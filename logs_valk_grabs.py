from collections import defaultdict

from constants import sort_dict_by_value, running_time

mobs = {"008EF5", "009342", "008F5D"}
REMORSELESS_WINTER_TRANSITION_1 = {"68981", "74271", "74270", "74272"}
REMORSELESS_WINTER_TRANSITION_2 = {"72259", "74274", "74273", "74275"}
REMORSELESS_WINTER = REMORSELESS_WINTER_TRANSITION_1 | REMORSELESS_WINTER_TRANSITION_2
FLAGS = ['SPELL_CAST_START', "SWING_DAMAGE", "RANGE_DAMAGE", "SPELL_CAST_SUCCESS", "ENVIRONMENTAL_DAMAGE"]
# 8/28 00:21:30.020  ENVIRONMENTAL_DAMAGE,0x0000000000000000,nil,0x80000000,0x070000000070C7FA,"Lomphidon",0x514,FALLING,626,0,1,0,0,0,nil,nil,nil

@running_time
def find_tanks(logs_slice: list[str]):
    dmg_taken = defaultdict(int)
    for line in logs_slice:
        if ',SWING_' not in line:
            continue
        line = line.split(',', 5)
        if line[2][6:-6] in mobs:
            dmg_taken[line[4]] += 1
    dmg_taken = sort_dict_by_value(dmg_taken)
    return set(list(dmg_taken)[:2])

@running_time
def get_valks_summon_time(logs_slice: list[str]):
    valks: dict[str, int] = {}
    for line in logs_slice:
        if '_SUMMON' in line and ",0xF150008F01" in line:
            guid = line.split(',', 5)[4]
            valks[guid] = logs_slice.index(line)
    return valks

@running_time
def get_valks_first_cast(logs_slice: list[str]):
    valks: dict[str, int] = {}
    for line in logs_slice:
        if '_START' not in line:
            continue
        guid = line.split(',', 3)[2]
        if guid[6:-6] == "008F01" and guid not in valks:
            valks[guid] = logs_slice.index(line)
    return valks
    
@running_time
def get_valk_phase(logs_slice: list[str]):
    start = None
    end = None
    for line in logs_slice:
        if line[-5:] != ",BUFF":
            continue
        if '0008EF5' not in line:
            continue
        try:
            _line = line.split(',', 7)
            if _line[6] not in REMORSELESS_WINTER:
                continue
            if _line[6] in REMORSELESS_WINTER_TRANSITION_1:
                if _line[1] == "SPELL_AURA_REMOVED":
                    start = logs_slice.index(line)
            elif _line[1] == "SPELL_AURA_APPLIED":
                end = logs_slice.index(line)
                return start, end
        except IndexError:
            pass
    
    return start, end

def get_valk_waves(logs_slice_t2):
    valks_summon = get_valks_summon_time(logs_slice_t2)
    print(valks_summon)
    valks_cast = get_valks_first_cast(logs_slice_t2)
    print(valks_cast)
    valks = list(valks_summon)
    valks = [valks[x:x+3] for x in range(0, len(valks), 3)]
    print(valks)
    VALK_WAVES = [
        (
            valks_summon[wave[-1]],
            min(valks_cast.get(x, -1) for x in wave)
        )
        for wave in valks
    ]

    last_valk_wave_end = VALK_WAVES[-1][1]
    if last_valk_wave_end == -1:
        del VALK_WAVES[-1]
        
    return VALK_WAVES

def get_casts(logs_slice: list[str]):
    casts = defaultdict(int)
    for line in logs_slice:
        _, flag, guid, _ = line.split(',', 3)
        if flag in FLAGS:
            casts[guid] += 1
    return sort_dict_by_value(casts)

@running_time
def get_casters(logs_slice: list[str]):
    print(len(logs_slice))
    casters: list[str] = []
    for line in logs_slice:
        _, flag, guid, _ = line.split(',', 3)
        if flag in FLAGS and guid not in casters:
            casters.append(guid)
    return casters

def convert_to_uptime(a):
    return [
        x if x < 0 else x*1000//max(a)/10
        for x in a
    ]
def get_players_alive_after_waves(valk_waves, logs_slice):
    AFTER_WAVES: list[set[str]] = []
    for x, y in zip(valk_waves, valk_waves[1:]):
        ws, wf = x[1], y[0]
        ws = wf - (wf-ws) // 4
        _slice = logs_slice[ws:wf]
        c = get_casters(_slice)
        AFTER_WAVES.append(c)
    _slice = logs_slice[y[1]:]
    c = get_casters(_slice)
    AFTER_WAVES.append(c)
    return AFTER_WAVES

def get_players_alive_after_waves(valk_waves, logs_slice):
    AFTER_WAVES: list[set[str]] = []
    for x, y in zip(valk_waves, valk_waves[1:]):
        _slice = logs_slice[x[1]:y[0]]
        c = get_casters(_slice)
        AFTER_WAVES.append(c)
    _slice = logs_slice[y[1]:]
    c = get_casters(_slice)
    AFTER_WAVES.append(c)
    return AFTER_WAVES

def get_players_alive_after_waves(valk_waves, logs_slice):
    AFTER_WAVES: list[set[str]] = []
    for x, y in zip(valk_waves, valk_waves[1:]):
        ws, wf = x[1], y[0]
        wf = ws + (wf-ws) // 4
        _slice = logs_slice[ws:wf]
        c = get_casters(_slice)
        AFTER_WAVES.append(c)
    _slice = logs_slice[y[1]:]
    c = get_casters(_slice)
    AFTER_WAVES.append(c)
    return AFTER_WAVES


@running_time
def get_env_deaths(logs_slice: list[str]):
    dropped: set[str] = set()
    for line in logs_slice:
        if "FALLING" not in line:
            continue
        guid = line.split(',', 5)[4]
        dropped.add(guid)
    return dropped

def get_players_deaths_after_waves(valk_waves, logs_slice):
    AFTER_WAVES: list[set[str]] = []
    for x, y in zip(valk_waves, valk_waves[1:]):
        ws, wf = x[1], y[0]
        wf = ws + (wf-ws) // 2
        _slice = logs_slice[ws:wf]
        c = get_env_deaths(_slice)
        AFTER_WAVES.append(c)
    ws, wf = y[1], len(logs_slice)
    wf = ws + (wf-ws) // 2
    _slice = logs_slice[ws:wf]
    c = get_env_deaths(_slice)
    AFTER_WAVES.append(c)
    return AFTER_WAVES

def get_grabs(data: dict[str, list], i: int):
    new_data = {k: v[i] for k, v in data.items() if v[i] != -1}
    new_data = sort_dict_by_value(new_data)
    valks = 3
    if len(new_data) < 11:
        valks = 1
    return set(list(new_data)[-valks:])

def present_players(logs_slice):
    players = set()
    for line in logs_slice:
        if "0x0" not in line:
            continue
        players.add(line.split(',', 5)[4])
    return

@running_time
def main(logs_slice: list[str], players: dict[str, str]):
    t2s, t2f = get_valk_phase(logs_slice)
    if t2s is None:
        return
    
    logs_slice_t2 = logs_slice[t2s:t2f]
    VALK_WAVES = get_valk_waves(logs_slice_t2)
    if len(VALK_WAVES) < 2:
        return

    AFTER_WAVES = get_players_alive_after_waves(VALK_WAVES, logs_slice_t2)
    AFTER_WAVES_DROPS = get_players_deaths_after_waves(VALK_WAVES, logs_slice_t2)

    TANKS = find_tanks(logs_slice[:t2s])
    # print(TANKS)
    # _players = set(players) - TANKS
    players_present = get_casters(logs_slice[t2s:t2s+VALK_WAVES[0][0]])
    players_present = set(players_present) & set(players) - TANKS
    # players_present = set()
    # for d in AFTER_WAVES:
    #     players_present.update(set(d) & _players)
    # players_present = {x for x in players_present if x in players and x not in TANKS}
    print(players_present)

    GRABS = defaultdict(list)
    for (ws, wf), _casts, _drops in zip(VALK_WAVES, AFTER_WAVES, AFTER_WAVES_DROPS):
        CASTS = get_casts(logs_slice_t2[ws:wf])
        print(_drops)
        for pguid in players_present:
            pname = players[pguid]
            if pguid in _drops:
                print(pname, 'was dropped')
                v = -2
            elif pguid in CASTS:
                v = CASTS[pguid]
            elif pguid not in _casts:
                print(pname, 'is dead')
                v = -1
            else:
                v = 0
            GRABS[pname].append(v)
    
    print(GRABS)
    GRABS = {k: convert_to_uptime(v) for k,v in GRABS.items()}
    
    waves_len = len(list(GRABS.values())[0])

    return [
        get_grabs(GRABS, x)
        for x in range(waves_len)
    ]
    

GRABS = {
    "22-08-27--20-19--Deydraenna--Icecrown": [
        {"Parsifai", "Kikepatrol", "Kardiokill"},
        {"Bdsmka", "Skvig", "Kardiokill"},
        {"Kikepatrol", "Wopka", "Legendarnox"},
    ],
    "22-08-26--21-03--Nomadra--Lordaeron": [
        {"Dlt", "Wakemeup", "Stanicenemy"},
        {"Nolfein", "Etnica", "Dotq"},
        {"Risli", "Stanicenemy", "Arthemiis"},
    ],
    "22-08-18--20-31--Meownya--Lordaeron": [
        {"Narzisse", "Quarthon", "Yarel"},
        {"Zibra", "Cocainomado", "Whiterplanet"},
        {"Zibra", "Ahcelf", "Dim"},
        {"Zibra", "Quarthon", "Dim"},
    ],
    "22-08-25--20-20--Jebber--Lordaeron": [
        {"Sana", "Luw", "Jengo"},
        {"Syella", "Sharpshady", "Matan"},
        {"Sharpshady", "Lockver", "Dodgypsy"},
    ],
    "22-08-18--20-00--Lockver--Lordaeron": [
        {"Orkleczyc", "Sharpshady", "Murmaider"},
        {"Orkleczyc", "Tmsdk", "Pingpong"},
        {"Sharpshady", "Jengo", "Murmaider"},
        {"Orkleczyc", "Triwoll", "Alpinae"},
    ],
}

def __test(name, attempt=-2):
    report = logs_main.THE_LOGS(name)
    enc_data = report.get_enc_data()
    S, F = enc_data["The Lich King"][attempt]
    logs_slice = report.get_logs(S, F)
    players = report.get_players_guids()
    data = main(logs_slice, players)
    print(data)

    for x, y in zip(data, GRABS[name]):
        print(x == y)

if __name__ == "__main__":
    import logs_main
    # for x in GRABS:
    #     __test(x)
    __test(list(GRABS)[-1])
