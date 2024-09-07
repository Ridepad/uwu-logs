from collections import defaultdict
from time import perf_counter

import logs_main
from c_path import Directories
from h_debug import Loggers, get_ms_str, running_time
from constants import TOP_FILE_NAME
from logs_spell_info import (
    AURAS_BOSS_MECHANICS,
    AURAS_CONSUME,
    AURAS_EXTERNAL,
    MULTISPELLS_D,
)

try:
    import _validate
except ImportError:
    _validate = None

LOGGER_REPORTS = Loggers.reports

Z_SPELLS = [AURAS_EXTERNAL, AURAS_CONSUME, AURAS_BOSS_MECHANICS]

HUNGER_FOR_BLOOD = "63848"
FOCUS_MAGIC = "54646"
BATTLE_SQUAWK = "23060"
SPECS_NO_USE_FOR_CHICKEN = {*range(12, 16), *range(20, 24), 29, 31, 33, 35}

def f_auras(auras: dict[str, tuple[int, float]], spec: int):
    if HUNGER_FOR_BLOOD in auras and spec == 25:
        del auras[HUNGER_FOR_BLOOD]
    if FOCUS_MAGIC in auras and spec in range(12, 16):
        del auras[FOCUS_MAGIC]
    if BATTLE_SQUAWK in auras and spec in SPECS_NO_USE_FOR_CHICKEN:
        del auras[BATTLE_SQUAWK]
    
    zz: dict[str, list[int, float, int]] = {}
    for spell_id, (count, uptime) in auras.items():
        spell_id = MULTISPELLS_D.get(spell_id, spell_id)
        for n, auras_dict in enumerate(Z_SPELLS):
            if spell_id not in auras_dict:
                continue
            uptime = round(uptime*100, 1)
            if spell_id in zz:
                count += zz[spell_id][0]
                uptime += zz[spell_id][1]
            zz[spell_id] = [count, uptime, n]
            break

    return [
        [int(spell_id), *spell_data]
        for spell_id, spell_data in zz.items()
    ]

class Top(logs_main.THE_LOGS):
    def make_report_top_wrap(self, rewrite=False):
        top_path = Directories.logs / self.NAME / TOP_FILE_NAME
        if not rewrite and top_path.is_file():
            return
        
        pc = perf_counter()
        q = _validate and _validate.pure_dog_water(self)
        if q:
            report_top = {}
            LOGGER_REPORTS.debug(f'{get_ms_str(pc)} | {self.NAME:50} | Dog water | {q}')
        else:
            report_top = self.make_report_top()
            LOGGER_REPORTS.debug(f'{get_ms_str(pc)} | {self.NAME:50} | Done top')

        top_path.json_write(report_top)
        return report_top

    @running_time
    def make_report_top(self):
        report_top = defaultdict(dict)
        for boss_name, kill_segment in self.gen_kill_segments():
            diff = kill_segment['diff']
            s = kill_segment["start"]
            f = kill_segment["end"]
            report_top[boss_name][diff] = self.make_boss_top(s, f, boss_name)
        return report_top
    

    def get_vali_heal(self, s, f):
        data = defaultdict(lambda: defaultdict(int))
        for line in self.LOGS[s:f]:
            if "_H" not in line:
                continue
            _line = line.split(',', 11)
            data[_line[4]][_line[2]] += int(_line[9]) - int(_line[10])
        return data

    def get_vali_heal_wrap(self, s, f):
        vali_data = self.get_vali_heal(s, f)
        _useful = defaultdict(int)
        _total = defaultdict(int)
        for tguid, sources in vali_data.items():
            # totems worked until ~21-12-20
            # if tguid[5:12] == "0008FB5":
            #     for sguid, v in sources.items():
            #         dmg_useful[_sguid] += v
            if tguid[5:12] == "0008FB5":
                _useful = sources
            for sguid, v in sources.items():
                _sguid = self.get_master_guid(sguid)
                _total[_sguid] += v
        
        return {
            "useful_total": _useful,
            "damage_total": _total,
        }

    @running_time
    def make_boss_top(self, s, f, boss_name: str):
        def is_player(guid):
            if guid in PLAYERS:
                return True
            # LOGGER_REPORTS.error(f"{report.NAME} {boss_name} Missing player {report.guid_to_name(guid)}")
        PLAYERS = self.get_players_guids()
        SPECS = self.get_players_specs_in_segments(s, f)
        DURATION = self.get_slice_duration(s, f)
        AURAS = self.auras_info(s, f)

        if boss_name == "Valithria Dreamwalker":
            _data = self.get_vali_heal_wrap(s, f)
        else:
            _damage = self.target_damage(s, f)
            _total = _damage["total"]
            _no_overkill = _damage["no_overkill"]
            _specific = self.target_damage_specific(s, f, boss_name)
            _data = self.target_damage_combine(_total, _no_overkill, _specific)
        
        all_total = _data["damage_total"]
        all_useful = _data["useful_total"]

        return [
            {
                'r': self.NAME,
                't': DURATION,
                'i': guid[-7:],
                'n': PLAYERS[guid],
                'u': useful,
                'd': all_total[guid],
                's': SPECS[guid],
                'a': f_auras(AURAS[guid], SPECS[guid])
            }
            for guid, useful in all_useful.items()
            if is_player(guid)
        ]

def make_report_top_wrap(report_name, rewrite=False):
    try:
        t = Top(report_name)
        t.make_report_top_wrap(rewrite=rewrite)
        return True
    except Exception:
        LOGGER_REPORTS.exception(report_name)


def _print_boss_top(boss_top: list[dict]):
    for x in sorted(boss_top, key=lambda x: x["u"], reverse=True):
        q = f"{x['n']:12} | {x['u']:>11,} | {x['d']:>11,}"
        print(q)

def _test1():
    make_report_top_wrap("24-05-10--21-04--Jengo--Lordaeron", True)

def _test2():
    # report = Top("24-02-09--20-49--Meownya--Lordaeron")
    report = Top("24-05-10--21-04--Jengo--Lordaeron")
    data = report.make_report_top()
    # lk = data["The Lich King"]["25H"]
    # for x in lk:
    #     print(x)
    # vali = data["Valithria Dreamwalker"]["25H"]
    # _print_boss_top(vali)
    fg = data["Festergut"]["25H"]
    _print_boss_top(fg)

if __name__ == "__main__":
    _test1()
