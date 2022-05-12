# count npc
# biggest count == boss
# get all lines
# split if big gap 

import _main
import check_difficulty

# def npccount(logs: list[str], guids):
#     q = {}
#     for line in logs:
#         _, _, sGUID, _, tGUID, _ = line.split(',', 5)
#         q[tGUID] = q.get(tGUID, 0) + 1
#         # q[sGUID] = q.get(sGUID, 0) + 1
#     # print(q)
#     # print(z1)
#     new_total = {}
#     for guid, c in q.items():
#         if guid.startswith('0x06'):
#             continue
#         d = guids.get(guid)
#         if not d:
#             print(guid)
#             continue
#         name = d['name']
#         new_total[name] = new_total.get(name, 0) + c
#     z1 = sorted(new_total.items(), key=lambda x: x[1], reverse=True)
#     for name, c in z1:
#         print(f"{name:<30} {c:>6}")

IGNORED_NAMES = {'Mirror Image', 'Treant', 'Shadowfiend'}

def print_by_guid(data, guids):
    z1 = sorted(data.items(), key=lambda x: x[1], reverse=True)
    s = 0
    t = 0
    for guid, c in z1:
        if guid.startswith('0x06') or guid.startswith('0xF14'):
            continue
        if not guids.get(guid):
            continue
        print(f"{guids[guid]['name']:<30} {c:>6}")
        s += c
        t += 1
    print(s, t, s/t)

def combine_names(data, guids):
    newd = {}
    for guid, c in data.items():
        if guid.startswith('0x06') or guid.startswith('0xF14'):
            continue
        d = guids.get(guid)
        if d is None:
            continue
        name = d['name']
        if name in IGNORED_NAMES:
            continue
        newd[name] = newd.get(name, 0) + c
    __sorted = sorted(newd.items(), key=lambda x: x[1], reverse=True)
    print(list(dict(__sorted)))
    # for name, c in __sorted:
        # print(f"{name:<30} {c:>6}")
    return

def npc_count(logs: list[str]):
    q = {}
    for line in logs:
        _, _, _, _, tGUID, _ = line.split(',', 5)
        # _, _, sGUID, _, tGUID, _ = line.split(',', 5)
        # q[sGUID] = q.get(sGUID, 0) + 1
        q[tGUID] = q.get(tGUID, 0) + 1
    return q


def convert_to_html_name(name: str):
    return name.lower().replace(' ', '-').replace("'", '')
def asdf(slice_duration, boss_name, kill, attempt):
    segment_name = f"{slice_duration[2:]} | {boss_name}"
    is_kill = "kill"
    if not kill:
        segment_name = f"{segment_name} | Try {attempt+1}"
        is_kill = "try"
    return is_kill, segment_name

SPACES = [
    "",
    " "*2,
    " "*4,
    " "*6,
    " "*8,
    " "*10,
    " "*12,
]

def attempts_block(boss_name, link, diff, segments):
    data = []
    for attempt, __segment in enumerate(segments):
        is_kill, slice_duration, s, f = __segment
        is_kill, segment_name = asdf(slice_duration, boss_name, is_kill, attempt)
        a = f'{SPACES[5]}<a href="{link}&diff={diff}&s={s}&f={f}" class="{is_kill}-link">{segment_name}</a>'
        data.append(a)
    return '\n'.join(data)
def diff_block():
    return

def bosses_block():
    return

def main():
    report_id = "22-03-26--22-02--Nomadra"
    report_id = "22-03-25--22-02--Nomadra"
    report = _main.THE_LOGS(report_id)
    logs = report.get_logs()
    guids = report.get_all_guids()
    enc = report.get_enc_data()
    print(enc)
    # npccount(logs,guids )
    new_data = {}
    for boss_name, _slice in enc.items():
        q = {}
        for s, f in _slice:
            logs_slice = logs[s:f]
            diff, is_kill, duration = check_difficulty.make_line(logs, s, f, boss_name)
            q.setdefault(diff, []).append((is_kill, duration, s, f))
            # z = npc_count(logs_slice)
            # combine_names(z, guids)
        new_data[boss_name] = dict(sorted(q.items()))
    # print(new_data)
    data1 = []
    for boss_name, diffs in new_data.items():
        boss_html = convert_to_html_name(boss_name)
        link = f'/reports/{report_id}/?boss={boss_html}'

        data2 = []
        for diff, segments in diffs.items():
            data3 = []
            for attempt, __segment in enumerate(segments):
                is_kill, slice_duration, s, f = __segment
                is_kill, segment_name = asdf(slice_duration, boss_name, is_kill, attempt)
                # q = [
                #     f'{SPACES[5]}<li>',
                #     f'{SPACES[6]}<a href="{link}&diff={diff}&s={s}&f={f}" class="{is_kill}-link">{segment_name}</a>',
                #     f'{SPACES[5]}</li>',
                # ]
                # data3.append('\n'.join(q))
                q = f'{SPACES[5]}<li><a href="{link}&diff={diff}&s={s}&f={f}" class="{is_kill}-link">{segment_name}</a></li>'
                data3.append(q)
            
            data3j = '\n'.join(data3)
            q = [
                f'{SPACES[3]}<li>',
                f'{SPACES[4]}<a href="{link}&diff={diff}" class="boss-link">{diff} {boss_name} segments</a>',
                f'{SPACES[4]}<ul class="bosses-seg">\n{data3j}\n{SPACES[4]}</ul>',
                f'{SPACES[3]}</li>',
            ]
            data2.append('\n'.join(q))
        data2j = '\n'.join(data2)
        q = [
            f"{SPACES[1]}<li>",
            f'{SPACES[2]}<a href="{link}" class="boss-link">All {boss_name} segments</a>',
            f'{SPACES[2]}<ul class="bosses-diff">\n{data2j}\n{SPACES[2]}</ul>',
            f"{SPACES[1]}</li>",
        ]
        data1.append('\n'.join(q))
    data1j = '\n'.join(data1)
    # print(f'<ul id="bosses-list">\n{data1}\n</ul>')
    html = f'{SPACES[0]}<ul class="bosses-diff">\n{data1j}\n{SPACES[0]}</ul>'
    print(html)

if __name__ == "__main__":
    main()
