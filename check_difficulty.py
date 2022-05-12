from collections import defaultdict

import constants

DIFFICULTY = ('10N', '10H', '25N', '25H')
DEFAULT_DIFFICULTY = "TBD"
SPELLS: dict[str, tuple[str, tuple[str]]] = {
    # "Lord Marrowgar": ("Bone Spike Graveyard", ("69057", "72088", "70826", "72089")),
    "Lord Marrowgar": ("Coldflame", ("69146", "70824", "70823", "70825")),
    "Lady Deathwhisper": ("Shadow Bolt", ("71254", "72503", "72008", "72504")),
    "Gunship": ("Shoot", ("70162", "72567", "72566", "72568")),
    # "Gunship2": ("Shoot", ("", "69974", "", "71144")),
    "Gunship2": ("Hurl Axe", ("70161", "72540", "72539", "72541")),
    "Deathbringer Saurfang": ("Rune of Blood", ("72409", "72448", "72447", "72449")),
    "Festergut": ("Gastric Bloat", ("72219", "72552", "72551", "72553")),
    "Rotface": ("Mutated Infection", ("69674", "73022", "71224", "73023")),
    "Professor Putricide": ("Mutated Transformation", ("70402", "72512", "72511", "72513")),
    "Professor Putricide2": ("Unstable Experiment", ("70351", "71967", "71966", "71968")),
    # "Blood Prince Council": ("Empowered Shock Vortex", ("72039", "73038", "73037", "73039")),
    "Blood Prince Council": ("Shadow Lance", ("71405", "72804", "72805", "72806")),
    "Blood-Queen Lana'thel": ("Shroud of Sorrow", ("70985", "71699", "71698", "71700")),
    "Valithria Dreamwalker": ("Frostbolt Volley", ("70759", "72015", "71889", "72016")),
    "Sindragosa": ("Frost Aura", ("70084", "71051", "71050", "71052")),
    "The Lich King": ("Infest", ("70541", "73780", "73779", "73781")),
    
    "Saviana Ragefire": ("Flame Breath", ("74403", "", "74404", "")),
    "General Zarithrian": ("Lava Gout", ("74394", "", "74395", "")),
    "Halion": ("Flame Breath", ("74525", "74527", "74526", "74528")),

    "Northrend Beasts": ("Impale", ("66331", "67478", "67477", "67479")),
    "Lord Jaraxxus": ("Fel Fireball", ("66532", "66964", "66963", "66965")),
    "Faction Champions": ("Dispel Magic", ("65546", "68625", "68624", "68626")),
    "Faction Champions2": ("Earth Shock", ("65868", "68101", "68100", "68102")),
    # "Faction Champions": ("Shoot", ("65868", "67989", "67988", "67990")),
    # "Faction Champions": ("Frostbolt", ("65807", "68004", "68003", "68005")),
    # "Faction Champions": ("Frost Strike", ("66047", "67936", "67935", "67937")),
    # "Faction Champions": ("Shadowstep", ("66178", "68760", "68759", "68761")),
    # "Faction Champions2": ("Mana Burn", ("66100", "68027", "68026", "68028")),
    # "Faction Champions": ("Fan of Knives", ("65955", "68098", "68097", "68099")),
    # "Faction Champions2": ("Shadow Bolt", ("65821", "68152", "68151", "68153")),
    "Twin Val'kyr": ("Light Surge", ("65767", "67275", "67274", "67276")),
    "Anub'arak": ("Penetrating Cold", ("66013", "68509", "67700", "68510")),
    
    "Onyxia": ("Flame Breath", ("18435", "", "68970", "")),
    "Malygos": ("Arcane Storm", ("61693", "", "61694", "")),
    "Sartharion": ("Flame Breath", ("56908", "", "58956", "")),

    "Toravon the Ice Watcher": ("Frozen Orb", ("72082", "", "72097", "")),
    "Koralon the Flame Watcher": ("Burning Breath", ("66670", "", "67329", "")),
    "Archavon the Stone Watcher": ("Rock Shards", ("58696", "", "60884", "")),
    "Emalon the Storm Watcher": ("Chain Lightning", ("64213", "", "64215", "")),
}


def get_diff(logs_slice: list[str], boss_name: str) -> str:
    if boss_name not in SPELLS:
        return DEFAULT_DIFFICULTY
    spell_name, ids = SPELLS[boss_name]
    for line in logs_slice:
        if spell_name not in line:
            continue
        for n, id_ in enumerate(ids):
            if id_ and id_ in line:
                return DIFFICULTY[n]
    boss_ver_2 = f"{boss_name}2"
    if boss_ver_2 in SPELLS:
        return get_diff(logs_slice, boss_ver_2)
    return DEFAULT_DIFFICULTY

def is_kill(last_line: str):
    if 'UNIT_DIED' in last_line:
        return True
    # if "008FB5" in last_line or "00915F" in last_line or "0092A4" in last_line:
        # return last_line.split(',')[10] != '0'
    # return False
    try:
        return last_line.split(',')[10] != '0'
    except IndexError:
        return False

def has_fury_of_frostmourne(logs_slice: list[str]):
    return any(
        '72350' in line
        and '8EF5' in line
        and 'SPELL' in line
        and '_CAST' not in line
        for line in logs_slice
    )

def get_slice_duration(logs_slice):
    s, f = logs_slice[0], logs_slice[-1]
    dur = constants.get_fight_duration(s, f)
    return constants.convert_duration(dur)

def make_line(logs, s, f, boss_name):
    logs_slice = logs[s:f+1]
    diff = get_diff(logs_slice, boss_name)
    kill = is_kill(logs_slice[-1])
    if not kill and boss_name == "The Lich King":
        kill = has_fury_of_frostmourne(logs[f:f+20])
    slice_duration = get_slice_duration(logs_slice)
    return diff, kill, slice_duration


def diff_gen(logs: list[str], enc_data: dict[str, list[tuple[int]]]):
    _diff = defaultdict(list)
    for boss_name, attempts in enc_data.items():
        for s, f in attempts:
            logs_slice = logs[s:f+1]
            diff = get_diff(logs_slice, boss_name)
            kill = is_kill(logs_slice[-1])
            if not kill and boss_name == "The Lich King":
                kill = has_fury_of_frostmourne(logs[f:f+20])
            
            slice_duration = get_slice_duration(logs_slice)
            # v = make_line(logs, s, f, boss_name)
            _diff[boss_name].append((diff, kill, slice_duration))
    return _diff

def convert_to_html_name(name: str):
    return name.lower().replace(' ', '-').replace("'", '')

def format_attempt(logs: list[str], segment: tuple[int, int], boss_name: str, attempt: int, shift: int):
    s, f = segment
    
    logs_slice = logs[s:f+1]
    diff = get_diff(logs_slice, boss_name)
    
    slice_duration = get_slice_duration(logs_slice)

    kill = is_kill(logs_slice[-1])
    if not kill and boss_name == "The Lich King":
        kill = has_fury_of_frostmourne(logs[f:f+20])
    if kill:
        attempt_type = "kill"
        segment_type = "Kill"
        # segment_str = f"{slice_duration[2:]} | {diff} {boss_name}"
    else:
        attempt_type = "wipe"
        segment_type = f"Wipe {attempt-shift+1}"
        # segment_str = f"{slice_duration[2:]} | {diff} {boss_name} | Try {attempt-shift+1}"
    
    return {
        "start": s,
        "end": f,
        "diff": diff,
        "attempt": attempt,
        "attempt_type": attempt_type,
        "segment_type": segment_type,
        "slice_duration": slice_duration,
    }


def sadfksadfopk(logs, segments, boss_name):
    boss_data: dict[str, list[dict[str, str]]] = {}
    shift = 0
    for attempt, segment in enumerate(segments):
        segment_data = format_attempt(logs, segment, boss_name, attempt, shift)
        if segment_data["attempt_type"] == "kill":
            shift = attempt+1
        diff = segment_data['diff']
        boss_data.setdefault(diff, []).append(segment_data)
    return boss_data

def diff_gen(logs: list[str], enc_data: dict[str, list[tuple[int]]], report_id):
    new_data = {}
    boss_to_html = {}
    for boss_name, segments in enc_data.items():
        boss_html = convert_to_html_name(boss_name)
        boss_to_html[boss_name] = boss_html
        link = f"/reports/{report_id}/?boss={boss_html}"

        boss_data = sadfksadfopk(logs, segments, boss_name)

        _data_with_links = {}
        data_sorted = sorted(boss_data.items())
        for diff, segments in data_sorted:
            link2 = f"{link}&diff={diff}"
            for seg_info in segments:
                seg_info['link'] = f"{link2}{seg_info['link']}"
            _data_with_links[diff] = {
                'link': link2,
                'data': segments,
            }

        new_data[boss_name] = {
            'link': link,
            'data': _data_with_links,
        }
    
    return {
        "segments": new_data,
        "html": boss_to_html,
    }
    
def ggygiogigio(data):
    for boss_name, diffs in data.items():
        print(f'''<a href="{diffs["link"]}" class="boss-link">All {boss_name} segments</a>''')
        for diff, segments in diffs["data"].items():
            a = f'''  <a href="{segments["link"]}" class="boss-link">{diff} {boss_name} segments</a>'''
            print(a)
            for segment_info in segments["data"]:
                a = f'''    <a href="{segment_info["link"]}" class="{segment_info["kill_str"]}-link">{segment_info["segment_name"]}</a>'''
                # a = f'''    <a href="{segment_info["link"]}" class="boss-link">{diff} {boss_name} segments</a>'''
                print(a)

def __test():
    import _main
    report_id = "22-03-24--20-36--Inia"
    report = _main.THE_LOGS(report_id)
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    data = diff_gen(logs, enc_data, report_id)
    SEGMENTS_QUERIES = data['segments']
    to_html = data['html']
    ggygiogigio(SEGMENTS_QUERIES)


    

def get_segments2(logs, enc_data: dict[str, list[tuple[int, int]]]):
    new_data = {}
    boss_to_html = {}
    for boss_name, segments in enc_data.items():
        boss_html = convert_to_html_name(boss_name)
        boss_to_html[boss_name] = boss_html

        boss_data = []
        shift = 0
        for attempt, segment in enumerate(segments):
            segment_data = format_attempt(logs, segment, boss_name, attempt, shift)
            if segment_data["attempt_type"] == "kill":
                shift = attempt+1
            boss_data.append(segment_data)
        new_data[boss_name] = boss_data
    
    return {
        "segments": new_data,
        "boss_html": boss_to_html,
    }

def separate_modes(data):
    separated: dict[str, dict[str, list[list]]] = {}
    for boss_name, segments in data.items():
        new_segments: dict[str, list[list]] = {}
        for segment in segments:
            diff = segment['diff']
            new_segments.setdefault(diff, []).append(segment)
        separated[boss_name] = new_segments
    return separated


def __test():
    import _main
    report_id = "22-03-24--20-36--Inia"
    report = _main.THE_LOGS(report_id)
    logs = report.get_logs()
    enc_data = report.get_enc_data()
    data = get_segments2(logs, enc_data)
    boss_html = data['boss_html']
    separated = separate_modes(data['segments'])
    ggygiogigio(separated, report_id, boss_html)
    # print(data['segments'])

if __name__ == "__main__":
    import _main
    __test()
