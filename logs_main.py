import json
import os
from collections import defaultdict
from datetime import datetime

import auras
import logs_check_difficulty
import constants
import dmg_breakdown
import dmg_heals
import dmg_useful
import logs_fight_separator
import logs_get_time
import logs_player_class
import logs_spell_info
import logs_spells_list
import logs_units_guid
import logs_valks3

from constants import is_player, running_time, sort_dict_by_value, add_new_numeric_data, add_space

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
LOGS_DIR = os.path.join(DIR_PATH, "LogsDir")

IGNORED_ADDS = ['Treant', 'Shadowfiend', 'Ghouls']
PLAYER = "0x0"

def separate_thousands(num):
    if not num: return ""
    v = f"{num:,}" if type(num) == int else f"{num:,.1f}"
    return v.replace(",", " ")

def format_total_data(data: dict):
    data["Total"] = sum(data.values())
    return {k: separate_thousands(v) for k, v in data.items()}

def calc_percent(value: int, max_value: int):
    return int(value / max_value * 100)

def calc_per_sec(value: int, duration: float, precision: int=1):
    v = value / (duration or 1)
    precision = 10**precision
    v = int(v * precision) / precision
    return separate_thousands(v)

def convert_to_table(data: dict[str, int], duration):
    if not data:
        return []
    _data = list(data.items())
    max_value = _data[0][1]
    return [
        (
            name,
            separate_thousands(value),
            calc_per_sec(value, duration),
            calc_percent(value, max_value),
        )
        for name, value in _data
    ]

def count_total(spell_data: dict[str, dict[str, list[int]]]):
    return {
        spell_id: sum(sum(x) for x in d.values())
        for spell_id, d in spell_data.items()
    }

def count_total(spell_data: dict[str, dict[str, list[int]]]):
    new = {
        spell_id: sum(sum(x) for x in d.values())
        for spell_id, d in spell_data.items()
    }
    total = sum(new.values())
    new["Total"] = total
    total = total or 1
    return {
        spell_id: (separate_thousands(value), f"{separate_thousands(value / total * 100)}%")
        for spell_id, value in new.items()
    }

def format_totals(data: dict):
    return {k:separate_thousands(v) for k,v in data.items()}

def format_raw(raw_total: dict[int, int]):
    total = sum(raw_total.values())
    return {
        spell_id: (separate_thousands(value), separate_thousands(value / total * 100))+"%"
        for spell_id, value in raw_total.items()
    }

def build_query(boss_name_html, mode, s, f, attempt):
    slice_q = f"s={s}&f={f}" if s and f else ""
    
    if boss_name_html:
        query = f"boss={boss_name_html}"
        if mode:
            query = f"{query}&mode={mode}"
        query = f"{query}&{slice_q}"
        if attempt is not None:
            query = f"{query}&attempt={attempt}"
    else:
        query = slice_q
    
    if query:
        return f"?{query}"
    return ""

def convert_duration(t):
    milliseconds = int(t % 1 * 1000)
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = t // 3600
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0<3}"

def combine_durations(durations: list):
    return convert_duration(sum(durations))
    
@constants.running_time
def get_targets(logs_slice: list[str], source=PLAYER, target="0xF1"):
    _targets: set[str] = set()
    for line in logs_slice:
        if "_DAMAGE" not in line:
            continue
        if source not in line:
            continue
        _, _, sguid, _, tguid, _ = line.split(',', 5)
        if source in sguid and target in tguid:
            _targets.add(tguid)
    target_ids = {x[6:-6] for x in _targets}
    # print(target_ids)
    return {
        target_id: {x for x in _targets if target_id in x}
        for target_id in target_ids
    }


def group_targets(targets: set[str]):
    target_ids = {guid[:-6] for guid in targets}
    return {
        target_id: {guid for guid in targets if target_id in guid}
        for target_id in target_ids
    }

def regroup_targets(data):
    grouped_targets = group_targets(data)
    targets_players = set()
    for x in grouped_targets:
        if x[:3] == PLAYER:
            targets_players = grouped_targets.pop(x, set())
            break
    return set(grouped_targets) | targets_players

def convert_to_html_name(name: str):
    return name.lower().replace(' ', '-').replace("'", '')

def slice_apply_shift(p):
    return


class THE_LOGS:
    # GUIDS: dict[str, dict[str, str]]
    # PLAYERS: dict[str, str]
    
    def __init__(self, logs_name: str) -> None:
        self.NAME = logs_name
        self.PATH = os.path.join(LOGS_DIR, logs_name)
        if not os.path.exists(self.PATH):
            os.makedirs(self.PATH, exist_ok=True)
            print('LOG: Created folder:', self.PATH)

        self.last_access = datetime.now()

        self.bosses_convert: dict[str, str] = {}
        self.DURATIONS: dict[str, float] = {}
        self.TARGETS: dict[str, dict[str, set[str]]] = {}
        self.CACHE: dict[str, dict[str, dict]] = {x: {} for x in dir(self) if "__" not in x}
        self.CONTROLLED_UNITS: dict[str, set[str]] = {}

    def relative_path(self, s: str):
        return os.path.join(self.PATH, s)

    def get_logger(self):
        try:
            return self.LOGGER
        except AttributeError:
            log_file = self.relative_path('log.log')
            logger = constants.setup_logger(f"{self.NAME}_logger", log_file)
            self.LOGGER = logger
            return logger
    
    def cache_files_missing(self, files):
        try:
            return not os.path.isfile(files)
        except TypeError:
            return not all(os.path.isfile(file) for file in files)
    
    def get_fight_targets(self, s, f):
        return self.TARGETS[f"{s}_{f}"]
    
    def get_logs(self, s=None, f=None):
        try:
            logs = self.LOGS
        except AttributeError:
            logs_cut_file_name = self.relative_path("LOGS_CUT")
            logs_raw = constants.zlib_text_read(logs_cut_file_name)
            logs = constants.logs_splitlines(logs_raw)
            self.LOGS = logs
        
        return logs[s:f]
    
    def logs_first_last_line(self, s, f):
        logs_slice = self.get_logs(s, f)
        return logs_slice[0], logs_slice[-1]
    
    def get_fight_duration(self, s, f):
        slice_ID = f"{s}_{f}"
        if slice_ID in self.DURATIONS:
            return self.DURATIONS[slice_ID]
        first_line, last_line = self.logs_first_last_line(s, f)
        dur = constants.get_fight_duration(first_line, last_line)
        self.DURATIONS[slice_ID] = dur
        return dur
        
    def get_enc_data(self, rewrite=False):
        try:
            return self.ENCOUNTER_DATA
        except AttributeError:
            enc_data_file_name = self.relative_path("ENCOUNTER_DATA.json")
            if rewrite or self.cache_files_missing(enc_data_file_name):
                logs = self.get_logs()
                self.ENCOUNTER_DATA = logs_fight_separator.main(logs)
                constants.json_write(enc_data_file_name, self.ENCOUNTER_DATA, indent=None)
            else:
                self.ENCOUNTER_DATA: dict[str, list[tuple[int, int]]] = constants.json_read(enc_data_file_name)
            return self.ENCOUNTER_DATA
    
    def new_guids(self, guids_data_file_name, players_data_file_name, classes_data_file_name):
        logs = self.get_logs()
        enc_data = self.get_enc_data()
        parsed = logs_units_guid.guids_main(logs, enc_data)
        _guids = parsed['everything']
        _players = parsed['players']
        _classes = parsed['classes']
        constants.json_write(guids_data_file_name, _guids)
        constants.json_write(players_data_file_name, _players)
        constants.json_write(classes_data_file_name, _classes)
        return _guids, _players, _classes
    
    def get_guids(self, rewrite=False):
        try:
            return self.GUIDS, self.PLAYERS, self.CLASSES
        except AttributeError:
            _guids: dict[str, dict[str, str]]
            _players: dict[str, str]
            _classes: dict[str, str]

            files = [
                self.relative_path("GUIDS_DATA.json"),
                self.relative_path("PLAYERS_DATA.json"),
                self.relative_path("CLASSES_DATA.json")
            ]
            
            if rewrite or self.cache_files_missing(files):
                _guids, _players, _classes = self.new_guids(*files)
            else:
                _guids, _players, _classes = [
                    constants.json_read_no_exception(_file_name)
                    for _file_name in files
                ]
            
            self.GUIDS, self.PLAYERS, self.CLASSES = _guids, _players, _classes
            return self.GUIDS, self.PLAYERS, self.CLASSES

    def get_all_guids(self):
        return self.get_guids()[0]

    def get_players_guids(self, filter_guids=None, filter_names=None):
        players = self.get_guids()[1]
        if filter_guids is not None:
            return {k:v for k,v in players.items() if k in filter_guids}
        elif filter_names is not None:
            return {k:v for k,v in players.items() if v in filter_names}
        else:
            return players

    def get_classes(self):
        return self.get_guids()[2]

    def guid_to_player_name(self):
        try:
            return self.PLAYERS_NAMES
        except AttributeError:
            players = self.get_players_guids()
            self.PLAYERS_NAMES = {v:k for k,v in players.items()}
            return self.PLAYERS_NAMES
        
    def get_all_players_pets(self):
        try:
            return self.ALL_PETS
        except AttributeError:
            guids = self.get_all_guids()
            self.ALL_PETS = {
                guid
                for guid, p in guids.items()
                if p.get("master_guid", "").startswith(PLAYER)
            }
            return self.ALL_PETS

    def get_players_and_pets_guids(self):
        try:
            return self.PLAYERS_AND_PETS
        except AttributeError:
            players = set(self.get_players_guids())
            pets = self.get_all_players_pets()
            self.PLAYERS_AND_PETS = players | pets
            return self.PLAYERS_AND_PETS
        
    # def get_classes(self, rewrite=False):
    #     try:
    #         return self.CLASSES
    #     except AttributeError:
    #         classes_data_file_name = self.relative_path("CLASSES_DATA.json")
    #         if rewrite or self.cache_files_missing(classes_data_file_name):
    #             logs = self.get_logs()
    #             players = self.get_players_guids()
    #             self.CLASSES = logs_player_class.get_classes(logs, players)
    #             constants.json_write(classes_data_file_name, self.CLASSES)
    #         else:
    #             self.CLASSES: dict[str, str] = constants.json_read(classes_data_file_name)
    #         return self.CLASSES
            
    def get_classes_with_names(self):
        try:
            return self.CLASSES_NAMES
        except AttributeError:
            classes = self.get_classes()
            players = self.get_players_guids()
            self.CLASSES_NAMES = {players[guid]: class_name for guid, class_name in classes.items()}
            return self.CLASSES_NAMES
        
    def get_spells(self, rewrite=False):
        try:
            return self.SPELLS
        except AttributeError:
            spells_data_file_name = self.relative_path("SPELLS_DATA.json")
            if rewrite or self.cache_files_missing(spells_data_file_name):
                logs = self.get_logs()
                self.SPELLS = logs_spells_list.get_all_spells(logs)
                constants.json_write(spells_data_file_name, self.SPELLS)
            else:
                _spells = constants.json_read_no_exception(spells_data_file_name)
                self.SPELLS = logs_spells_list.spell_id_to_int(_spells)
            return self.SPELLS
        
    def get_timestamp(self, rewrite=False) -> list[int]:
        try:
            return self.TIMESTAMP
        except AttributeError:
            timestamp_data_file_name = self.relative_path("TIMESTAMP_DATA.json")
            if rewrite or self.cache_files_missing(timestamp_data_file_name):
                logs = self.get_logs()
                self.TIMESTAMP = logs_get_time.ujiowfuiwefhuiwe(logs)
                constants.json_write(timestamp_data_file_name, self.TIMESTAMP, indent=None)
            else:
                self.TIMESTAMP: list[int] = constants.json_read(timestamp_data_file_name)
            return self.TIMESTAMP
        
    # @constants.running_time
    # def get_difficulty(self):
    #     try:
    #         return self.SEGMENTS
    #     except AttributeError:
    #         logs = self.get_logs()
    #         enc_data = self.get_enc_data()
    #         report_id = self.NAME
    #         data = check_difficulty.diff_gen(logs, enc_data, report_id)
    #         self.SEGMENTS = data['segments']
    #         return self.SEGMENTS

    def get_spells_colors(self, spells) -> dict[int, str]:
        if not spells:
            return {}
        all_spells = self.get_spells()
        return {
            spell_id: all_spells[abs(spell_id)]['color']
            for spell_id in spells
            if abs(spell_id) in all_spells
        }

    def boss_full_slice(self, boss_name):
        boss_name = self.bosses_convert.get(boss_name, boss_name)
        logs = self.get_logs()
        enc_data = self.get_enc_data()
        _slice = enc_data[boss_name]
        s = _slice[0][0]
        f = _slice[-1][-1]
        return s, f
    
    def find_index(self, n, shift=0):
        if n is None:
            return
        ts = self.get_timestamp()
        for i, line_n in enumerate(ts, -shift):
            if n <= line_n:
                return max(i, 0)

    def attempt_time(self, boss_name, attempt, shift=0):
        enc_data = self.get_enc_data()
        s, f = enc_data[boss_name][attempt]
        s = self.find_index(s, 2+shift)
        f = self.find_index(f, 1)
        return s, f

    # def format_attempt(self, boss_name: str, attempt: int, shift: int, _stats: list[str, bool, str]):
    #     diff, kill, slice_duration = _stats
    #     boss_name_html = boss_name.lower().replace(' ', '-')
    #     self.bosses_convert[boss_name_html] = boss_name
        
    #     s, f = self.attempt_time(boss_name, attempt)
    #     link = f'/reports/{self.NAME}/?s={s}&f={f}&boss={boss_name_html}&attempt={attempt}'
        
    #     segment_name = f"{slice_duration[2:]} | {diff} {boss_name}"
    #     is_kill = "kill"
    #     if not kill:
    #         segment_name = f"{segment_name} | Try {attempt-shift+1}"
    #         is_kill = "try"
    #     return {
    #         "segment_name": segment_name,
    #         "link": link,
    #         "is_kill": is_kill,
    #     }
    
    # def format_attempts(self) -> dict[str, list[tuple[str]]]:
    #     try:
    #         return self.FORMATED_DIFFICULTY
    #     except AttributeError:
    #         difficulty_data = self.get_difficulty()
    #         diffs = self.FORMATED_DIFFICULTY = {}
    #         _bosses = self.BOSSES_HTML = {}
    #         for boss_name, d in difficulty_data.items():
    #             boss_html = convert_to_html_name(boss_name)
    #             _bosses[boss_name] = f'/reports/{self.NAME}/?boss={boss_html}'
                
    #             q = diffs[boss_name] = []
    #             shift = 0
    #             for attempt, _stats in enumerate(d):
    #                 if _stats[1]:
    #                     shift = attempt+1
    #                 formatted = self.format_attempt(boss_name, attempt, shift, _stats)
    #                 q.append(list(formatted.values()))
    #         return diffs
        
    # def make_segment_queries(self, data):
    #     boss_links = {}
    #     diff_links = {}
    #     segm_links = []
    #     segm_links2 = {}
    #     report_id = self.NAME
    #     boss_html = self.BOSSES_TO_HTML
    #     for boss_name, diffs in data.items():
    #         href1 = f"?boss={boss_html[boss_name]}"
    #         # href1 = f"/reports/{report_id}/?boss={boss_html[boss_name]}"
    #         a = f'<a href="{href1}" class="boss-link">All {boss_name} segments</a>'
    #         boss_links[boss_name] = a
    #         diff_links_boss = diff_links[boss_name] = {}
    #         for diff, segments in diffs.items():
    #             href2 = f'''{href1}&mode={diff}'''
    #             a = f'''<a href="{href2}" class="boss-link">{diff} {boss_name}</a>'''
    #             # a = f'''<a href="{href2}" class="boss-link">{diff} {boss_name} segments</a>'''
    #             diff_links_boss[diff] = a
    #             for seg_info in segments:
    #                 attempt = seg_info['attempt']
    #                 s, f = self.attempt_time(boss_name, attempt)
    #                 href3 = f'''{href2}&s={s}&f={f}&attempt={attempt}'''
    #                 segment_str = f"{seg_info['slice_duration'][2:]} | {seg_info['segment_type']}"
    #                 # segment_str = f"{seg_info['slice_duration']} | {boss_name} | {seg_info['segment_type']}"
    #                 a = f'''<a href="{href3}" class="{seg_info['attempt_type']}-link">{segment_str}</a>'''
    #                 segm_links.append(a)
    #                 segm_links2.setdefault(boss_name, {}).setdefault(diff, []).append(a)
    #     return {
    #         "boss_links": boss_links,
    #         "diff_links": diff_links,
    #         "segm_links": segm_links2,
    #     }
        
    # def make_segment_queries(self, data):
    #     segm_links = {}
    #     # report_id = self.NAME
    #     boss_html = self.BOSSES_TO_HTML
    #     for boss_name, diffs in data.items():
    #         href1 = f"?boss={boss_html[boss_name]}"
    #         # href1 = f"/reports/{report_id}/?boss={boss_html[boss_name]}"
    #         a = f'<a href="{href1}" class="boss-link">All {boss_name} segments</a>'
    #         boss_data = segm_links[boss_name] = {'link': a}
    #         boss_links = boss_data['links'] = {}
    #         for diff_id, segments in diffs.items():
    #             href2 = f"{href1}&mode={diff_id}"
    #             a = f'''<a href="{href2}" class="boss-link">{diff_id} {boss_name}</a>'''
    #             # a = f'''<a href="{href2}" class="boss-link">{diff} {boss_name} segments</a>'''
    #             diff_data = boss_links[diff_id] = {'link': a}
    #             diff_links = diff_data['links'] = []
    #             for seg_info in segments:
    #                 attempt = seg_info['attempt']
    #                 s, f = self.attempt_time(boss_name, attempt)
    #                 href3 = f"{href2}&s={s}&f={f}&attempt={attempt}"
    #                 segment_str = f"{seg_info['slice_duration'][2:]} | {seg_info['segment_type']}"
    #                 # segment_str = f"{seg_info['slice_duration']} | {boss_name} | {seg_info['segment_type']}"
    #                 a = f'''<a href="{href3}" class="{seg_info['attempt_type']}-link">{segment_str}</a>'''
    #                 diff_links.append(a)
    #                 # diff_links.setdefault(boss_name, {}).setdefault(diff_id, []).append(a)
    #     return {
    #         "segm_links": segm_links,
    #     }
        
    def make_segment_query_segment(self, seg_info, boss_name, href2):
        attempt = seg_info['attempt']
        s, f = self.attempt_time(boss_name, attempt)
        href3 = f"{href2}&s={s}&f={f}&attempt={attempt}"
        class_name = f"{seg_info['attempt_type']}-link"
        segment_str = f"{seg_info['duration_str']} | {seg_info['segment_type']}"
        return {"href": href3, "class_name": class_name, "text": segment_str}
    
    def make_segment_query_diff(self ,segments, boss_name, href1, diff_id):
        href2 = f"{href1}&mode={diff_id}"
        a = {"href": href2, "class_name": "boss-link", "text": f"{diff_id} {boss_name}"}
        return {
            'link': a,
            'links': [
                self.make_segment_query_segment(seg_info, boss_name, href2)
                for seg_info in segments
            ]
        }

    def make_segment_queries(self, data):
        segm_links = {}
        boss_html = self.BOSSES_TO_HTML
        for boss_name, diffs in data.items():
            href1 = f"?boss={boss_html[boss_name]}"
            a = {"href": href1, "class_name": "boss-link", "text": f"All {boss_name} segments"}
            boss_data = segm_links[boss_name] = {'link': a}
            boss_links = boss_data['links'] = {}
            for diff_id, segments in diffs.items():
                href2 = f"{href1}&mode={diff_id}"
                a = {"href": href2, "class_name": "boss-link", "text": f"{diff_id} {boss_name}"}
                boss_links[diff_id] = {
                    'link': a,
                    'links': [
                        self.make_segment_query_segment(seg_info, boss_name, href2)
                        for seg_info in segments
                    ]
                }
        return {
            "segm_links": segm_links,
        }

    def make_segment_queries(self, data):
        segm_links = {}
        boss_html = self.BOSSES_TO_HTML
        for boss_name, diffs in data.items():
            href1 = f"?boss={boss_html[boss_name]}"
            a = {"href": href1, "class_name": "boss-link", "text": f"All {boss_name} segments"}
            boss_data = segm_links[boss_name] = {'link': a}
            boss_data['links'] = {
                diff_id: self.make_segment_query_diff(segments, boss_name, href1, diff_id)
                for diff_id, segments in diffs.items()
            }
        return {
            "segm_links": segm_links,
        }

    def format_attempts(self) -> dict[str, list[tuple[str]]]:
        try:
            return self.SEGMENTS
        except AttributeError:
            logs = self.get_logs()
            enc_data = self.get_enc_data()
            _data = logs_check_difficulty.get_segments2(logs, enc_data)

            segments = _data['segments']
            self.SEGMENTS = segments
            bosses_html = _data['boss_html']
            self.BOSSES_TO_HTML = bosses_html
            self.BOSSES_CONVERT = {v:k for k, v in bosses_html.items()}
            
            separated = logs_check_difficulty.separate_modes(segments)
            self.SEGMENTS_SEPARATED = separated
            self.SEGMENTS_QUERIES = self.make_segment_queries(separated)

            return self.SEGMENTS



    def get_spells_lower(self):
        try:
            return self.SPELLS_LOWER
        except AttributeError:
            spells = self.get_spells()
            self.SPELLS_LOWER = {spell_id: v["name"].lower() for spell_id, v in spells.items()}
            return self.SPELLS_LOWER

    def get_spells_ids(self):
        try:
            return self.SPELLS_IDS
        except AttributeError:
            spells = self.get_spells()
            self.SPELLS_IDS = {spell_id: str(spell_id) for spell_id in spells}
            return self.SPELLS_IDS

    @running_time
    def filtered_spell_list(self, request: dict[str, str]):
        if 'filter' not in request:
            return {}
        
        INPUT = request['filter'].lower()
        SPELLS = self.get_spells()

        _spells = self.get_spells_ids() if INPUT.isdigit() else self.get_spells_lower()

        return {
            spell_id: SPELLS[spell_id]['name']
            for spell_id, spell_v in _spells.items()
            if INPUT in spell_v
        }

    # @running_time
    # def filtered_spell_list(self, data: dict[str, str]):
    #     INPUT = data['filter'].lower()
    #     QUERY = data['query']
    #     SPELL_LINK_BASE = f'/reports/{self.NAME}/spell'
    #     SPELLS = self.get_spells()
    #     SPELLS_LOWER = self.get_spells_lower()

    #     def make_spell_html(spell_id):
    #         spell_name = SPELLS[int(spell_id)]['name']
    #         url = f'{SPELL_LINK_BASE}/{spell_id}/{QUERY}'
    #         return f'<a href="{url}"><span>{spell_id}</span><span>{spell_name}</span></a>'

    #     z = []

    #     if INPUT.isdigit():
    #         z = [
    #             make_spell_html(spell_id)
    #             for spell_id in map(str, SPELLS)
    #             if INPUT in spell_id
    #         ]
    #     else:
    #         z = [
    #             make_spell_html(spell_id)
    #             for spell_id, spell_name in SPELLS_LOWER.items()
    #             if INPUT in spell_name
    #         ]
    #     if not z:
    #         return 'Spell not found'
        
    #     return ''.join(sorted(z))

    
    def convert_slice_to_time(self, s=None, f=None):
        ts = self.get_timestamp()
        if s is not None:
            s = ts[s]
        if f is not None:
            f = ts[f]
        return s, f

    
    def parse_request(self, request, shift=0):
        args: dict = request.args
        segments = self.format_attempts()
        enc_data = self.get_enc_data()
        ts = self.get_timestamp()
        separated = self.SEGMENTS_SEPARATED

        boss_name_id = "Custom Slice"
        boss_name_html = args.get("boss")
        boss_name = self.BOSSES_CONVERT.get(boss_name_html, "")
        segment_difficulty = args.get("mode")
        attempt = args.get("attempt", type=int)
        if boss_name:
            boss_name_id = self.BOSSES_CONVERT[boss_name_html]
            if attempt is not None:
                boss_name_id = f"{boss_name_id} | Try {attempt+1}"
                segments = [enc_data[boss_name][attempt], ]
            elif segment_difficulty:
                boss_name_id = f"{boss_name_id} | {segment_difficulty}"
                segments = [
                    [segment["start"], segment["end"]]
                    for segment in separated[boss_name][segment_difficulty]
                ]
            else:
                segments = enc_data[boss_name]

            # print(f"[parse_request] segments {segments}")
            # print(f"[parse_request] segments {shift}")

            if shift:
                for i, (seg_s, seg_f) in enumerate(segments):
                    seg_s_shifted = self.find_index(seg_s) - shift
                    seg_s_shifted_t = ts[seg_s_shifted]
                    segments[i] = [seg_s_shifted_t, seg_f]

            s = self.find_index(segments[0][0])
            f = self.find_index(segments[-1][-1])
        
        else:
            s = args.get("s", type=int)
            f = args.get("f", type=int)
            segments = [[ts[s], ts[f]]] if s and f else [[None, None], ]
        
        query = build_query(boss_name_html, segment_difficulty, s, f, attempt)

        return {
            "segments": segments,
            "boss_name_id": boss_name_id,
            "query": query,
            "boss_name": boss_name,
        }

    @constants.running_time
    def get_spell_count(self, spell_id_str: str, logs_slice):
        # add another dict with timestamps
        spells = self.get_spells()
        spell_id = int(spell_id_str)
        if spell_id not in spells:
            print('ERROR: spell_id not in spells:', spell_id)
            return {}
        spells: dict[str, dict[str, int]] = {}
        SPELL = "SWING_" if spell_id == 1 else "SPELL_"
        for line in logs_slice:
            if spell_id_str not in line:
                continue
            if SPELL not in line:
                continue
            line = line.split(',')
            flag, source_name, target_name = line[1], line[3], line[5]
            _spell_id = line[9] if flag == "SPELL_DISPEL" else line[6]
            if _spell_id == spell_id_str:
                flag_info = spells.setdefault(flag, {"sources": {}, "targets": {}})
                flag_info["sources"][source_name] = flag_info["sources"].get(source_name, 0) + 1
                flag_info["targets"][target_name] = flag_info["targets"].get(target_name, 0) + 1
        for flag_info in spells.values():
            for sources, sources_info in flag_info.items():
                flag_info[sources] = sort_dict_by_value(sources_info)
        spells = {x: spells[x] for x in constants.FLAG_ORDER if x in spells}
        return spells
    
    def name_to_guid(self, name: str) -> str:
        guids = self.get_all_guids()
        players_names = self.guid_to_player_name()

        if name in players_names:
            return players_names[name]
        for guid, data in guids.items():
            if data['name'] == name:
                return guid
    
    def guid_to_name(self, guid: str) -> str:
        guids = self.get_all_guids()
        try:
            return guids[guid]["name"]
        except KeyError:
            for full_guid, p in guids.items():
                if guid in full_guid:
                    return p['name']
        
    def get_master_guid(self, guid: str):
        guids = self.get_all_guids()
        master_guid = guids[guid].get('master_guid')
        if not master_guid:
            return guid
        return guids.get(master_guid, {}).get('master_guid', master_guid)

    def get_units_controlled_by(self, master_guid: str):
        if master_guid in self.CONTROLLED_UNITS:
            return self.CONTROLLED_UNITS[master_guid]
        
        all_guids = self.get_all_guids()
        controlled_units = {
            guid
            for guid, p in all_guids.items()
            if p.get("master_guid") == master_guid
        }
        controlled_units.add(master_guid)
        self.CONTROLLED_UNITS[master_guid] = controlled_units
        return controlled_units

    def dmg_taken(self, logs_slice, filter_guids=None, players=False):
        if filter_guids is None:
            filter_guid = PLAYER if players else '0xF1'
            dmg = dmg_heals.parse_dmg_taken_single(logs_slice, filter_guid)
        else:
            dmg = dmg_heals.parse_dmg_taken(logs_slice, filter_guids)
        new_data: dict[str, dict[str, int]] = {}
        for tguid, sources in dmg.items():
            name = self.guid_to_name(tguid)
            q = new_data.setdefault(name, {})
            for sguid, value in sources.items():
                sguid = self.get_master_guid(sguid)
                q[sguid] = q.get(sguid, 0) + value
        b = next(iter(new_data))
        new_data[b] = sort_dict_by_value(new_data[b])
        for name in IGNORED_ADDS:
            new_data.pop(name, None)
        for d in new_data.values():
            d.pop('nil', None)
        players = self.get_players_guids()
        return {
            target_name: {players[guid]: separate_thousands(value) for guid, value in sources.items() if guid in players}
            for target_name, sources in new_data.items()
        }

    def convert_data_to_names(self, data: dict):
        guids = self.get_all_guids()
        data = sort_dict_by_value(data)
        return [(guids[guid]["name"], separate_thousands(v)) for guid, v in data.items()]

    @constants.running_time
    def valk_info(self, logs_slice):
        v = logs_valks3.Valks(self)
        all_grabs, details = v.main()

        guids = self.get_all_guids()
        valks_dmg = dmg_useful.get_valks_dmg(logs_slice)
        valks_overkill = dmg_useful.combine_pets(valks_dmg['overkill'], guids)
        valks_overkill = self.convert_data_to_names(valks_overkill)
        valks_useful = dmg_useful.combine_pets(valks_dmg['useful'], guids)
        valks_useful = self.convert_data_to_names(valks_useful)
        valks_damage = {
            'useful': valks_useful,
            'overkill': valks_overkill,
        }
        return all_grabs, details, valks_damage




    @constants.running_time
    def report_page(self, s, f) -> tuple[dict[str, int], dict[str, int]]:
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['report_page']
        if slice_ID in cached_data:
            return cached_data[slice_ID]
        
        logs_slice = self.get_logs(s, f)
        players_and_pets = self.get_players_and_pets_guids()
        data = dmg_heals.parse_both(logs_slice, players_and_pets)
        
        units = set(data["damage"]) | set(data["heal"])
        players = self.get_players_guids(filter_guids=units)
        classes = self.get_classes()
        if s is None and f is None:
            logs_slice = self.get_logs(None, 50000)
        data['specs'] = logs_player_class.get_specs(logs_slice, players, classes)

        data['first_hit'] = logs_slice[0]
        data['last_hit'] = logs_slice[-1]
        # print(data['damage'])
        # print(data['heal'])
        # print(data['specs'])

        cached_data[slice_ID] = data
        return data
    
    def dry_data(self, data, slice_duration):
        guids = self.get_all_guids()
        data_with_pets = dmg_heals.add_pets(data, guids)
        data_sorted = sort_dict_by_value(data_with_pets)
        return convert_to_table(data_sorted, slice_duration)

    def report_add_missing_specs(self, specs, damage, heals):
        classes_names = self.get_classes_with_names()
        damage_set = {x[0] for x in damage}
        heal_set = {x[0] for x in heals}
        another_units: set[str] = damage_set | heal_set

        for unit_name in another_units:
            if unit_name.endswith('-A'):
                specs[unit_name] = ('Mutated Abomination', 'ability_rogue_deviouspoisons')
            elif unit_name not in specs and unit_name in classes_names:
                player_class = classes_names[unit_name]
                specs[unit_name] = logs_player_class.get_spec_info(player_class)
                print(f"{unit_name} doenstt have spec!")
            # elif unit_name not in classes_names:
            #     print(f"{unit_name} not in classes_names!")


    def get_report_page_all(self, segments):
        return_dict = {}
        durations = []
        damage = defaultdict(int)
        heal = defaultdict(int)
        specs = {}

        for s, f in segments:
            durations.append(self.get_fight_duration(s, f))

            _data = self.report_page(s, f)
            add_new_numeric_data(damage, _data["damage"])
            add_new_numeric_data(heal, _data["heal"])
            specs |= _data['specs']
            return_dict["FIRST_HIT"] = _data['first_hit']
            return_dict["LAST_HIT"] = _data['last_hit']

        total_duration = sum(durations)
        total_duration_str = convert_duration(total_duration)

        damage = self.dry_data(damage, total_duration)
        heal = self.dry_data(heal, total_duration)

        self.report_add_missing_specs(specs, damage, heal)

        return return_dict | {
            "DAMAGE": damage,
            "HEAL": heal,
            "DURATION": total_duration_str,
            "SPECS": specs,
        }

    def player_info(self, s, f, sGUID, tGUID=None):
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['player_info'].setdefault(sGUID, {}).setdefault(tGUID, {})
        if slice_ID in cached_data:
            return cached_data[slice_ID]

        logs_slice = self.get_logs(s, f)
        controlled_units = self.get_units_controlled_by(sGUID)
        all_player_pets = self.get_players_and_pets_guids()
        data = dmg_breakdown.parse_logs(logs_slice, sGUID, controlled_units, all_player_pets, tGUID)
        cached_data[slice_ID] = data
        return data

    def player_info_all_add(self, segments, sGUID, tGUID=None):
        info_data = defaultdict(lambda: defaultdict(int))
        durations: list[int] = []
        info_data['durations'] = durations
        targets: set[str] = set()
        info_data['targets'] = targets
        actual = defaultdict(lambda: defaultdict(list))
        info_data['actual'] = actual

        for s, f in segments:
            durations.append(self.get_fight_duration(s, f))

            data = self.player_info(s, f, sGUID, tGUID)

            for k, v in data.items():
                if k == "targets":
                    targets.update(v)
                elif k == "actual":
                    for spell_id, cats in v.items():
                        spells = actual[spell_id]
                        for hit_type, hits in cats.items():
                            spells[hit_type].extend(hits)
                else:
                    add_new_numeric_data(info_data[k], v)

        return info_data

    @constants.running_time
    def player_info_all(self, segments, sGUID, tGUID=None):
        spell_data = self.get_spells()
        def spell_name(spell_id):
            try:
                if spell_id < 0:
                    return f"{spell_data[-spell_id]['name']} (Pet)"
                return f"{spell_data[spell_id]['name']}"
            except KeyError:
                return spell_id

        _data = self.player_info_all_add(segments, sGUID, tGUID)

        slice_duration = combine_durations(_data['durations'])

        targets_set = regroup_targets(_data['targets'])
        targets = {self.guid_to_name(gid): gid for gid in sorted(targets_set)}
        targets = dict(sorted(targets.items()))
        
        actual = _data['actual']
        hits_data = dmg_breakdown.hits_data(actual)
        actual_sum = {
            spell_id: sum(sum(x) for x in d.values())
            for spell_id, d in actual.items()
        }
        actual_sorted = sort_dict_by_value(actual_sum)
        spell_names = {spell_id: spell_name(spell_id) for spell_id in actual_sorted}
        spell_colors = self.get_spells_colors(spell_names)
        
        reduced = _data['reduced']
        reduced_formatted = format_total_data(reduced)
        reduced_percent = {
            spell_id: f"{(((value + reduced[spell_id]) / value - 1) * 100):.1f}%"
            for spell_id, value in actual_sum.items()
            if reduced.get(spell_id)
        }
        
        actual_formatted = format_total_data(actual_sum)
        actual_total = actual_sum['Total'] or 1
        actual_percent =  {
            spell_id: f"{(value / actual_total * 100):.1f}%"
            for spell_id, value in actual_sum.items()
        }

        return {
            "DURATION": slice_duration,
            "TARGETS": targets,
            "NAMES": spell_names,
            "COLORS": spell_colors,
            "ACTUAL": actual_formatted,
            "ACTUAL_PERCENT": actual_percent,
            "REDUCED": reduced_formatted,
            "REDUCED_PERCENT": reduced_percent,
            "HITS": hits_data,
        }
    
    def get_comp_data(self, segments, class_filter: str, tGUID=None):
        class_filter = class_filter.lower()
        response = {}
        for guid, class_name in self.get_classes().items():
            if class_name != class_filter:
                continue
            name = self.guid_to_name(guid)
            data = {
                "name": name,
                "data": self.player_info_all(segments, guid, tGUID)
            }
            yield f"{json.dumps(data, separators=(',', ':'))}\n"
            # response[name] = self.player_info_all(segments, guid, tGUID)
            # yield json.dumps(response)

    
    # POTIONS

    def potions_info(self, s, f) -> dict[str, dict[str, int]]:
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['potions_info']
        if slice_ID in cached_data:
            return cached_data[slice_ID]

        logs_slice = self.get_logs(s, f)
        data = logs_spell_info.get_potions_count(logs_slice)
        cached_data[slice_ID] = data
        return data
    
    def convert_dict_guids_to_name(self, data: dict):
        return {self.guid_to_name(guid): v for guid, v in data.items()}

    def add_missing_players(self, data, default=0):
        players = self.get_players_guids()
        for guid in players:
            if guid not in data:
                data[guid] = default
        return data
    
    def potions_all(self, segments):
        durations = []
        potions = defaultdict(lambda: defaultdict(int))

        for s, f in segments:
            durations.append(self.get_fight_duration(s, f))

            _potions = self.potions_info(s, f)
            for spell_id, sources in _potions.items():
                add_new_numeric_data(potions[spell_id], sources)
        
        slice_duration = combine_durations(durations)

        pots = {x: self.convert_dict_guids_to_name(y) for x,y in potions.items()}
        
        p_total = logs_spell_info.count_total(potions)
        p_total = sort_dict_by_value(p_total)
        p_total = self.add_missing_players(p_total)
        p_total = self.convert_dict_guids_to_name(p_total)

        return {
            "DURATION": slice_duration,
            "ITEM_INFO": logs_spell_info.ITEM_INFO,
            "ITEMS_TOTAL": p_total,
            "ITEMS": pots,
        }

    def auras_info(self, s, f):
        data: defaultdict[str, dict[str, tuple[int, float]]]
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['auras_info']
        if slice_ID in cached_data:
            data = cached_data[slice_ID]
            return data

        logs_slice = self.get_logs(s, f)
        data = logs_spell_info.get_raid_buff_count(logs_slice)
        data = logs_spell_info.get_auras_uptime(logs_slice, data)
        cached_data[slice_ID] = data
        return data

    def auras_info_all(self, segments, trim_non_players=True):
        durations = []
        auras_uptime = defaultdict(lambda: defaultdict(list))
        auras_count = defaultdict(lambda: defaultdict(int))

        for s, f in segments:
            durations.append(self.get_fight_duration(s, f))

            _auras = self.auras_info(s, f)
            for guid, aura_data in _auras.items():
                if trim_non_players and not is_player(guid):
                    continue
                for spell_id, (count, uptime) in aura_data.items():
                    auras_count[guid][spell_id] += count
                    auras_uptime[guid][spell_id].append(uptime)

        slice_duration = combine_durations(durations)

        aura_info_set = set()
        auras_uptime_formatted = defaultdict(lambda: defaultdict(float))
        for guid, aura_data in auras_uptime.items():
            for spell_id, uptimes in aura_data.items():
                aura_info_set.add(spell_id)
                v = sum(uptimes) / len(uptimes) * 100
                auras_uptime_formatted[guid][spell_id] = f"{v:.2f}"
        
        self.add_missing_players(auras_count, {})
        self.add_missing_players(auras_uptime, {})

        auras_count_with_names = self.convert_dict_guids_to_name(auras_count)
        auras_uptime_with_names = self.convert_dict_guids_to_name(auras_uptime_formatted)

        filtered_aura_info = logs_spell_info.get_filtered_info(aura_info_set)

        return {
            "DURATION": slice_duration,
            "AURA_UPTIME": auras_uptime_with_names,
            "AURA_COUNT": auras_count_with_names,
            "AURA_INFO": filtered_aura_info,
        }


    @constants.running_time
    def spell_count(self, s, f, spell_id_str) -> dict[str, dict[str, int]]:
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['spell_count'].setdefault(spell_id_str, {})
        if slice_ID in cached_data:
            return cached_data[slice_ID]
            
        logs_slice = self.get_logs(s, f)
        spells = logs_spell_info.get_spell_count(logs_slice, spell_id_str)

        cached_data[slice_ID] = spells
        return spells
    
    def spell_count_all(self, segments, spell_id: str):
        spell_id = spell_id.replace("-", "")
        all_spells = self.get_spells()
        if int(spell_id) not in all_spells:
            print('ERROR: spell_id not in spells:', spell_id)
            return {
                "DURATION": "",
                "SPELLS": {},
                "TABS": {},
            }
        
        durations = []
        spells: dict[str, dict[str, dict[str, int]]] = {}

        for s, f in segments:
            _spells = self.spell_count(s, f, spell_id)
            durations.append(self.get_fight_duration(s, f))
            for flag, _types in _spells.items():
                _flag = spells.setdefault(flag, {})
                for _type, names in _types.items():
                    _t = _flag.setdefault(_type, {})
                    for name, value in names.items():
                        _t[name] = _t.get(name, 0) + value
        
        slice_duration = combine_durations(durations)

        spells = {x: spells[x] for x in constants.FLAG_ORDER if x in spells}

        for flag_info in spells.values():
            for sources, sources_info in flag_info.items():
                flag_info[sources] = sort_dict_by_value(sources_info)
        
        tabs = [(flag.lower().replace('_', '-'), flag) for flag in spells]

        _spells = self.get_spells()
        s_id = abs(int(spell_id))
        spell_name = _spells.get(s_id, {}).get('name', '')
        spell_name = f"{spell_id} {spell_name}"

        return {
            "DURATION": slice_duration,
            "SPELLS": spells,
            "TABS": tabs,
            "SPELL_NAME": spell_name,
            "SPELL_ID": s_id,
        }


    # def useful_damage_combined(self, s, f, targets, boss_name):
    #     logs_slice = self.get_logs(s, f)
    #     data.update(dmg_useful.get_dmg(logs_slice, targets))
    #     return

    def useful_damage(self, s, f, targets, boss_name) -> dict[str, dict[str, int]]:
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['useful_damage']
        if slice_ID in cached_data:
            return cached_data[slice_ID]

        logs_slice = self.get_logs(s, f)

        data: dict[str, dict[str, int]] = {}
        data |= dmg_useful.specific_useful(logs_slice, boss_name)
        data |= dmg_useful.get_dmg(logs_slice, targets)
        
        cached_data[slice_ID] = data
        return data

    def add_total_and_names(self, data: dict):
        # print(data)
        data_sum = sum(data.values())
        return dict([
            ("Total", separate_thousands(data_sum)),
            *self.convert_data_to_names(data)
        ])
        # new_data = 
        # new_data.insert(0, ("Total", num_format(data_sum)))
        # return dict(new_data)

    @running_time
    def useful_damage_all(self, segments, boss_name):
        durations = []
        all_data = defaultdict(lambda: defaultdict(int))

        boss_guid_id = self.name_to_guid(boss_name)
        targets_useful, targets_all = dmg_useful.get_all_targets(boss_name, boss_guid_id)

        for s, f in segments:
            durations.append(self.get_fight_duration(s, f))

            data = self.useful_damage(s, f, targets_all, boss_name)
            for guid_id, _dmg_new in data.items():
                add_new_numeric_data(all_data[guid_id], _dmg_new)

        slice_duration = combine_durations(durations)

        guids = self.get_all_guids()
        all_data = dmg_useful.combine_pets_all(all_data, guids, trim_non_players=True)
    
        if "Valks Useful" in all_data:
            targets_useful["Valks Useful"] = "Valks Useful"
    
        targets_useful_dmg = dmg_useful.combine_targets(all_data, targets_useful)
        targets_useful_dmg = self.add_total_and_names(targets_useful_dmg)

        _formatted_dmg = {
            guid_id: self.add_total_and_names(_data)
            for guid_id, _data in all_data.items()
            if _data
        }

        table_heads = ["", "Total Useful"]
        if boss_name == "The Lich King":
            table_heads.append("Valks Useful")
        table_heads.extend([targets_all[guid_id] for guid_id in _formatted_dmg if guid_id in targets_all])

        return {
            "DURATION": slice_duration,
            "HEADS": table_heads,
            "TOTAL": targets_useful_dmg,
            "FORMATTED": _formatted_dmg,
        }


    def get_auras(self, s, f, filter_guid):
        logs_slice = self.get_logs(s, f)
        a = auras.AurasMain(logs_slice)
        data = a.main(filter_guid)
        spell_colors = self.get_spells_colors(data['spells'])
        all_spells = self.get_spells()
        segment_duration = self.get_fight_duration(s, f)
        return {
            'DURATION': convert_duration(segment_duration),
            'BUFFS': data['buffs'],
            'DEBUFFS': data['debuffs'],
            'COLORS': spell_colors,
            'ALL_SPELLS': all_spells,
            "BUFF_UPTIME": data['buffs_uptime'],
            "DEBUFF_UPTIME": data['debuffs_uptime'],
        }

    def get_auras_all(self, segments, player_name):
        durations = []

        filter_guid = self.name_to_guid(player_name)

        for s, f in segments:
            data = self.get_auras(s, f, filter_guid)
            buffs = data['buffs']
            durations.append(self.get_fight_duration(s, f))
    


    def logs_custom_search(self, query: dict[str, str]):
        logs = self.get_logs()
        # for 
        return 'Spell not found'


    def pretty_print_players_data(self, data):
        guids = self.get_all_guids()
        data = sort_dict_by_value(data)
        for guid, value in data.items():
            print(f"{guids[guid]['name']:<12} {add_space(value):>13}")

    def get_players_specs_in_segments(self, s, f):
        logs_slice = self.get_logs(s, f)
        players = self.get_players_guids()
        classes = self.get_classes()
        return logs_player_class.get_specs_no_names(logs_slice, players, classes)
