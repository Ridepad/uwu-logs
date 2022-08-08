from time import perf_counter
import dmg_heals
import logs_dmg_useful
import logs_main
import constants
from logs_spell_info import AURAS_EXTERNAL, AURAS_CONSUME, AURAS_BOSS_MECHANICS, MULTISPELLS_D

z_spells = [AURAS_EXTERNAL, AURAS_CONSUME, AURAS_BOSS_MECHANICS]


def f_auras(auras, spec):
    if spec == 25 and "63848" in auras:
        del auras["63848"]
    elif spec in range(12,16) and "54646" in auras:
        del auras["54646"]
    
    zz = {}
    for spell_id, (count, uptime) in auras.items():
        spell_id = MULTISPELLS_D.get(spell_id, spell_id)
        for n, a in enumerate(z_spells):
            if spell_id in a:
                uptime = round(uptime*100, 1)
                zz[spell_id] = [count, uptime, n]
                break
    return zz

def find_kill(segments):
    for segment_info in segments:
        if segment_info['attempt_type'] == 'kill':
            yield segment_info

def doshit(report: logs_main.THE_LOGS, boss_name: str, kill_segment: dict):
    S, F = kill_segment['start'], kill_segment['end']
    GUIDS = report.get_all_guids()

    boss_guid_id = report.name_to_guid(boss_name)
    targets = logs_dmg_useful.get_all_targets(boss_name, boss_guid_id)
    
    useful_data = report.useful_damage(S, F, targets["all"], boss_name)
    if "Valks Useful" in useful_data:
        targets["useful"]["Valks Useful"] = "Valks Useful"
    useful_data = logs_dmg_useful.combine_pets_all(useful_data, GUIDS, trim_non_players=True, ignore_abom=True)
    targets_useful_dmg = logs_dmg_useful.combine_targets(useful_data, targets["useful"])

    logs_slice = report.get_logs(S, F)
    players_and_pets = report.get_players_and_pets_guids()
    total_dmg = dmg_heals.parse_only_dmg_no_friendly(logs_slice, players_and_pets)
    # print(total_dmg)
    data_with_pets_d = dmg_heals.add_pets_guids(total_dmg, GUIDS)
    data_with_pets = data_with_pets_d["players"]
    # print(data_with_pets)

    specs = report.get_players_specs_in_segments(S, F)

    duration = report.get_fight_duration(S, F)
    auras = report.auras_info(S, F)
    
    players = report.get_players_guids()
    report_name = report.NAME
    return [
        {
            'i': guid[-7:],
            'n': players[guid],
            'r': report_name,
            'ua': useful,
            'ud': round(useful/duration, 2),
            'ta': data_with_pets[guid],
            'td': round(data_with_pets[guid]/duration, 2),
            't': duration,
            's': specs[guid],
            'a': f_auras(auras[guid], specs[guid])
        }
        for guid, useful in targets_useful_dmg.items()
    ]

BOSSES = ['The Lich King',
    'Lord Marrowgar', 'Lady Deathwhisper', 'Deathbringer Saurfang',
    'Festergut', 'Rotface', 'Professor Putricide',
    'Blood Prince Council', "Blood-Queen Lana'thel",
    'Sindragosa',
    'Halion', 'Baltharus the Warborn', 'General Zarithrian', 'Saviana Ragefire',
    "Anub'arak", 'Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions', "Twin Val'kyr",
    'Toravon the Ice Watcher', 'Archavon the Stone Watcher', 'Emalon the Storm Watcher', 'Koralon the Flame Watcher',
    'Onyxia']

def make_report_top(name: str):
    report = logs_main.THE_LOGS(name)
    top_path = report.relative_path('top.json')
    # if os.path.isfile(top_path):
    #     return
    print(name)
    pc = perf_counter()
    top = {}
    segments = report.get_segments_data()
    for boss_name, boss_segments in segments.items():
        if boss_name not in BOSSES:
            continue
        boss_top = top.setdefault(boss_name, {})
        for kill_segment in find_kill(boss_segments):
            diff = kill_segment['diff']
            data = doshit(report, boss_name, kill_segment)
            boss_top[diff] = data

    constants.json_write(top_path, top, indent=None)
    print(f'{name:<50} | Done in {constants.get_ms(pc):>6} ms')

def main_wrap(name):
    try:
        make_report_top(name)
    # except IndexError:
        # constants.LOGGER_MAIN.debug(f'{name}')
        # print(name)
    except Exception:
        constants.LOGGER_MAIN.exception(f'{name}')


if __name__ == "__main__":
    # make_report_top('22-07-29--21-00--Safiyah--Lordaeron')
    import _redo
    _redo.redo_data(main_wrap, proccesses=4)
    # _redo.redo_data(main_wrap, filter="Lordaeron", startfrom=-50, proccesses=4)
