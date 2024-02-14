import json
import os
from collections import defaultdict

import logs_absorbs
import logs_spells_order
import file_functions
import logs_check_difficulty
import logs_deaths
import logs_dmg_breakdown
import logs_dmg_heals
import logs_dmg_useful
import logs_dps
import logs_fight_separator
import logs_get_time
import logs_player_spec
import logs_power
import logs_spell_info
import logs_spells_list
import logs_top_db
import logs_units_guid
import logs_lady_spirits
import logs_valk_grabs
from constants import (
    BOSSES_FROM_HTML,
    CLASSES,
    COMBINE_SPELLS,
    CUSTOM_SPELL_NAMES,
    FLAG_ORDER,
    LOGGER_REPORTS,
    LOGGER_UNUSUAL_SPELLS,
    LOGS_CUT_NAME_OLD,
    LOGS_DIR,
    LOGS_CUT_NAME,
    MONTHS,
    convert_to_html_name,
    duration_to_string,
    get_now,
    get_report_name_info,
    is_player,
    running_time,
    separate_thousands,
    setup_logger,
    sort_dict_by_value,
    to_dt_year_precise,
)

PLAYER = "0x0"
SHIFT = {
    'spell': 10,
    'consumables': 10,
    'player_auras': 10,
}
PASSIVE_SPELLS = {
    49497: {
        'name': 'Spell Deflection',
        'school': '0x1',
        'color': 'physical',
        'icon': 'spell_deathknight_spelldeflection'
    },
    52286: {
        'name': 'Will of the Necropolis',
        'school': '0x1',
        'color': 'physical',
        'icon': 'ability_creature_cursed_02'
    },
}

UNKNOWN_ICON = "inv_misc_questionmark"
DEFAULT_ICONS = [
    UNKNOWN_ICON,
    "ability_rogue_deviouspoisons",
    "ability_hunter_readiness",
    "ability_druid_catform",
]
_ICONS = [
    list(specs.values())
    for specs in CLASSES.values()
]
_ICONS.insert(0, DEFAULT_ICONS)
SPEC_ICON_TO_POSITION = {
    icon: (class_i, spec_i)
    for class_i, specs in enumerate(_ICONS)
    for spec_i, icon in enumerate(specs)
}
BOSSES_SKIP_POINTS = {
    "Valithria Dreamwalker",
    "Gunship",
    "Heroic Training Dummy",
    "Highlord's Nemesis Trainer",
}

TYPES = (str, bool, type(None))
HIT_KEYS = {"CAST", "HIT", "PERIODIC"}
REDUCED_KEYS = {"OVERKILL", "OVERHEAL", "ABSORBED", "RESISTED", "GLANCING", "BLOCKED"}
MISS_KEYS = {"MISS", "PARRY", "DODGE", "ABSORB", "RESIST", "REFLECT", "IMMUNE", "DEFLECT", "EVADE", "BLOCK", "GLANCED"}

def get_shift(request_path: str):
    url_comp = request_path.split('/')
    try:
        return SHIFT.get(url_comp[3], 0)
    except IndexError:
        return 0

def add_new_numeric_data(data_total: defaultdict, data_new: dict[str, int]):
    for source, amount in data_new.items():
        data_total[source] += amount

def format_report_page_data(value: int, duration: float, max_value: int):
    return {
        "value": separate_thousands(value),
        "per_second": separate_thousands(calc_per_sec(value, duration)),
        "percent": calc_percent(value, max_value),
    }

def format_total_data(data: dict):
    data["Total"] = sum(data.values())
    return {k: separate_thousands(v) for k, v in data.items()}

def format_percentage(v, total):
    if not total:
        total = 1
    return f"{(v / total * 100):.1f}%"

def calc_percent(value: int, max_value: int):
    return value * 100 // max_value

def calc_per_sec(value: int, duration: float, precision: int=1):
    v = value / (duration or 1)
    precision = 10**precision
    return int(v * precision) / precision

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

def sort_by_name_type(targets: list[tuple[str, str]]):
    targets = sorted(targets, key=lambda x: x[1])
    targets.sort(key=lambda x: x[0][:3] == "0x0")
    targets.sort(key=lambda x: x[0][:5] == "0xF14")
    return dict(targets)

def get_dict_int(d: dict, key, default=None):
    try:
        v = d[key]
        try:
            return int(v)
        except Exception:
            return default
    except KeyError:
        return default


def cache_wrap(func):
    def cache_inner(self, s, f, *args, **kwargs):
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE[func.__name__]
        for arg in args:
            if not isinstance(arg, TYPES):
                break
            cached_data = cached_data[arg]
            
        if slice_ID in cached_data:
            return cached_data[slice_ID]
        
        data = func(self, s, f, *args, **kwargs)
        cached_data[slice_ID] = data
        return data

    return cache_inner


class THE_LOGS:
    def __init__(self, logs_name: str) -> None:
        self.NAME = logs_name

        self.year = int(logs_name[:2]) + 2000

        self.last_access = get_now()

        self.CACHE = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.CONTROLLED_UNITS: dict[str, set[str]] = {}

    @property
    def path(self):
        try:
            return self.__path
        except AttributeError:
            self.__path = file_functions.new_folder_path(LOGS_DIR, self.NAME, check_backup=True)
            return self.__path

    def relative_path(self, s: str):
        return os.path.join(self.path, s)

    @property
    def FORMATTED_NAME(self):
        try:
            return self.__FORMATTED_NAME
        except AttributeError:
            report_name_info = get_report_name_info(self.NAME)
            time = report_name_info['time'].replace('-', ':')
            year, month, day = report_name_info['date'].split("-")
            month = MONTHS[int(month)-1][:3]
            date = f"{day} {month} {year}"
            author = report_name_info['author']
            self.__FORMATTED_NAME = f"{date}, {time} - {author}"
            return self.__FORMATTED_NAME

    @property
    def LOGGER(self):
        try:
            return self.__LOGGER
        except AttributeError:
            log_file = self.relative_path('log.log')
            self.__LOGGER = setup_logger(f"{self.NAME}_logger", log_file)
            return self.__LOGGER
    
    def cache_files_missing(self, files):
        try:
            return not os.path.isfile(files)
        except TypeError:
            return not all(os.path.isfile(file) for file in files)
        
    @running_time
    def __open_logs(self):
        logs_cut_file_name = self.relative_path(LOGS_CUT_NAME)
        if os.path.isfile(logs_cut_file_name):
            return file_functions.zstd_text_read(logs_cut_file_name).splitlines()
        
        logs_cut_file_name_old = self.relative_path(LOGS_CUT_NAME_OLD)
        if os.path.isfile(logs_cut_file_name_old):
            return file_functions.zlib_text_read(logs_cut_file_name_old).splitlines()

        return []
        
    @property
    def LOGS(self):
        try:
            return self.__LOGS
        except AttributeError:
            self.__LOGS = self.__open_logs()
            return self.__LOGS
    
    def get_logs(self, s=None, f=None):
        if not s and f is None:
            return self.LOGS
        return self.LOGS[s:f]

    def get_timedelta(self, last, now):
        return to_dt_year_precise(now, self.year) - to_dt_year_precise(last, self.year)
    
    @cache_wrap
    def get_slice_duration(self, s: int=None, f: int=None):
        if s is None:
            s = 0
        if f is None:
            f = 0
        first_line = self.LOGS[s]
        last_line = self.LOGS[f-1]
        return self.get_timedelta(first_line, last_line).total_seconds()

    def get_fight_duration_total(self, segments):
        return sum(self.get_slice_duration(s, f) for s, f in segments)

    def get_enc_data(self, rewrite=False):
        try:
            return self.ENCOUNTER_DATA
        except AttributeError:
            enc_data_file_name = self.relative_path("ENCOUNTER_DATA.json")
            if rewrite or self.cache_files_missing(enc_data_file_name):
                self.ENCOUNTER_DATA = logs_fight_separator.Fights(self.LOGS).main()
                file_functions.json_write(enc_data_file_name, self.ENCOUNTER_DATA, indent=None)
            else:
                enc_data: dict[str, list[tuple[int, int]]]
                enc_data = file_functions.json_read(enc_data_file_name)
                self.ENCOUNTER_DATA = enc_data
            return self.ENCOUNTER_DATA
    
    def new_guids(self):
        enc_data = self.get_enc_data()
        parsed = logs_units_guid.guids_main(self.LOGS, enc_data)

        if parsed['missing_owner']:
            LOGGER_REPORTS.error(f"{self.NAME} | Missing owners: {parsed['missing_owner']}")
        
        guids_data_file_name = self.relative_path("GUIDS_DATA.json")
        players_data_file_name = self.relative_path("PLAYERS_DATA.json")
        classes_data_file_name = self.relative_path("CLASSES_DATA.json")

        _guids = parsed['everything']
        _players = parsed['players']
        _classes = parsed['classes']
        
        file_functions.json_write(guids_data_file_name, _guids)
        file_functions.json_write(players_data_file_name, _players)
        file_functions.json_write(classes_data_file_name, _classes)
        
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
                _guids, _players, _classes = self.new_guids()
            else:
                try:
                    _guids, _players, _classes = [
                        file_functions.json_read_no_exception(_file_name)
                        for _file_name in files
                    ]
                except Exception:
                    return self.get_guids(rewrite=True)
            self.GUIDS, self.PLAYERS, self.CLASSES = _guids, _players, _classes
            return self.GUIDS, self.PLAYERS, self.CLASSES

    def get_all_guids(self):
        return self.get_guids()[0]

    def get_players_guids(self, whitelist_guids=None, whitelist_names=None):
        players = self.get_guids()[1]
        if whitelist_guids is not None:
            return {k:v for k,v in players.items() if k in whitelist_guids}
        elif whitelist_names is not None:
            return {k:v for k,v in players.items() if v in whitelist_names}
        else:
            return players

    def get_classes(self):
        return self.get_guids()[2]

    @cache_wrap
    def get_players_specs_in_segments(self, s, f) -> dict[str, int]:
        '''specs = {guid: spec_index}'''
        logs_slice = self.LOGS[s:f]
        players = self.get_players_guids()
        classes = self.get_classes()
        return logs_player_spec.get_specs(logs_slice, players, classes)
        
    @property
    def PLAYERS_NAMES(self):
        try:
            return self.__PLAYERS_NAMES
        except AttributeError:
            players = self.get_players_guids()
            self.__PLAYERS_NAMES = {v:k for k,v in players.items()}
            return self.__PLAYERS_NAMES

    def name_to_guid(self, name: str) -> str:
        if name.startswith("0x"):
            return name

        if name in self.PLAYERS_NAMES:
            return self.PLAYERS_NAMES[name]
        
        guids = self.get_all_guids()
        for guid, data in guids.items():
            if data['name'] == name:
                return guid
    
    def guid_to_name(self, guid: str) -> str:
        guids = self.get_all_guids()
        players = self.get_players_guids()
        try:
            if guid in players:
                return players[guid]
            return guids[guid]["name"]
        except KeyError:
            for full_guid, p in guids.items():
                if guid in full_guid:
                    return p['name']

    def convert_dict_guids_to_names(self, data: dict[str]):
        return {
            self.guid_to_name(guid): value
            for guid, value in data.items()
        }
    
    def get_master_guid(self, guid: str):
        guids = self.get_all_guids()
        master_guid = guids[guid].get('master_guid')
        if not master_guid:
            return guid
        return guids.get(master_guid, {}).get('master_guid', master_guid)
    
    def get_pet_name(self, guid):
        is_pet = guid != self.get_master_guid(guid)
        if is_pet:
            return self.guid_to_name(guid)
        return None

    def get_units_controlled_by(self, master_guid: str):
        if not master_guid.startswith("0x"):
            master_guid = self.name_to_guid(master_guid)

        if master_guid in self.CONTROLLED_UNITS:
            return self.CONTROLLED_UNITS[master_guid]
        
        all_guids = self.get_all_guids()
        controlled_units = {
            guid
            for guid, p in all_guids.items()
            if p.get("master_guid") == master_guid or master_guid in guid
        }
        controlled_units.add(master_guid)
        self.CONTROLLED_UNITS[master_guid] = controlled_units
        return controlled_units
    
    @property
    def PLAYERS_PETS(self):
        try:
            return self.__PLAYERS_PETS
        except AttributeError:
            guids = self.get_all_guids()
            self.__PLAYERS_PETS = {
                guid
                for guid, p in guids.items()
                if p.get("master_guid", "").startswith(PLAYER)
            }
            return self.__PLAYERS_PETS


    def get_players_and_pets_guids(self):
        try:
            return self.PLAYERS_AND_PETS
        except AttributeError:
            players = set(self.get_players_guids())
            self.PLAYERS_AND_PETS = players | self.PLAYERS_PETS
            return self.PLAYERS_AND_PETS
            
    @property
    def CLASSES_NAMES(self):
        try:
            return self.__CLASSES_NAMES
        except AttributeError:
            classes = self.get_classes()
            _classes_names: dict[str, str] = self.convert_dict_guids_to_names(classes)
            self.__CLASSES_NAMES = _classes_names
            return _classes_names

    def get_classes_with_names_json(self):
        return json.dumps(self.CLASSES_NAMES)
        
    
    def get_timestamp(self, rewrite=False):
        try:
            return self.TIMESTAMP
        except AttributeError:
            timestamp_data_file_name = self.relative_path("TIMESTAMP_DATA.json")
            if rewrite or self.cache_files_missing(timestamp_data_file_name):
                self.TIMESTAMP = logs_get_time.get_timestamps(self.LOGS)
                file_functions.json_write(timestamp_data_file_name, self.TIMESTAMP, indent=None, sep=(",", ""))
            else:
                timestamp_data: list[int]
                timestamp_data = file_functions.json_read(timestamp_data_file_name)
                self.TIMESTAMP = timestamp_data
            return self.TIMESTAMP
    
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
        
    def make_segment_query_segment(self, seg_info, boss_name, href_prefix):
        attempt = seg_info['attempt']
        s, f = self.attempt_time(boss_name, attempt)
        href = f"{href_prefix}&s={s}&f={f}&attempt={attempt}"
        class_name = f"{seg_info['attempt_type']}-link"
        segment_str = f"{seg_info['duration_str']} | {seg_info['segment_type']}"
        return {
            "href": href,
            "class_name": class_name,
            "text": segment_str,
        }
    
    def make_segment_query_diff(self, segments, boss_name, href_prefix, diff_id):
        href = f"{href_prefix}&mode={diff_id}"
        return {
            "href": href,
            "class_name": "boss-link",
            "text": f"{diff_id} {boss_name}",
            "children": [
                self.make_segment_query_segment(seg_info, boss_name, href)
                for seg_info in segments
            ]
        }
    
    def make_segment_query_boss(self, boss_name: str, diffs: dict=None):
        href = f"?boss={convert_to_html_name(boss_name)}"

        if boss_name == "all":
            text = f"All boss segments"
        else:
            text = f"All {boss_name} segments"
        
        if diffs is None:
            diffs = {}
        
        return {
            "href": href,
            "class_name": "boss-link",
            "text": text,
            "children": [
                self.make_segment_query_diff(segments, boss_name, href, diff_id)
                for diff_id, segments in diffs.items()
            ]
        }

    @property
    def SEGMENTS(self):
        try:
            return self.__SEGMENTS
        except AttributeError:
            enc_data = self.get_enc_data()
            self.__SEGMENTS = logs_check_difficulty.get_segments(self.LOGS, enc_data)
            return self.__SEGMENTS
        
    @property
    def SEGMENTS_SEPARATED(self):
        try:
            return self.__SEGMENTS_SEPARATED
        except AttributeError:
            self.__SEGMENTS_SEPARATED = logs_check_difficulty.separate_modes(self.SEGMENTS)
            return self.__SEGMENTS_SEPARATED

    @property
    def SEGMENTS_QUERIES(self):
        try:
            return self.__SEGMENTS_QUERIES
        except AttributeError:
            segm_links = [
                self.make_segment_query_boss(boss_name, diffs)
                for boss_name, diffs in self.SEGMENTS_SEPARATED.items()
            ]
            segm_links.insert(0, self.make_segment_query_boss("all"))
            self.__SEGMENTS_QUERIES = segm_links
            return segm_links

    def get_segments_data_json(self):
        _data = {
            convert_to_html_name(fight_name): v
            for fight_name, v in self.SEGMENTS.items()
        }
        return json.dumps(_data)
    
    def segments_apply_shift(self, segments, shift_s=0, shift_f=0):
        if not shift_s and not shift_f:
            return
        
        ts = self.get_timestamp()
        for i, (seg_s, seg_f) in enumerate(segments):
            if shift_s:
                seg_s_shifted = self.find_index(seg_s, shift_s)
                seg_s = ts[seg_s_shifted]
            if shift_f:
                seg_f_shifted = self.find_index(seg_f, shift_f)
                seg_f = ts[seg_f_shifted]
            segments[i] = [seg_s, seg_f]
    
    def parse_request(self, path: str, args: dict) -> dict:
        segment_difficulty = args.get("mode")
        attempt = get_dict_int(args, "attempt")
        boss_name = args.get("boss")
        ts = self.get_timestamp()
        sc = get_dict_int(args, "sc")
        fc = get_dict_int(args, "fc")
        if sc and fc and sc > 0 and fc < len(ts):
            slice_name = "Custom Slice"
            slice_tries = ""
            segments = [[ts[sc], ts[fc]]]
        
        elif boss_name == "all":
            enc_data = self.get_enc_data()
            slice_name = "Bosses"
            segments = [x for y in enc_data.values() for x in y]
            slice_tries = "All"
        
        elif boss_name not in BOSSES_FROM_HTML:
            slice_name = "Custom Slice"
            slice_tries = ""
            s = get_dict_int(args, "s")
            f = get_dict_int(args, "f")
            if s and f:
                segments = [[ts[s], ts[f]]]
            else:
                segments =  [[None, None]]
        
        else:
            enc_data = self.get_enc_data()
            boss_name = BOSSES_FROM_HTML[boss_name]
            slice_name = boss_name
            if attempt is not None:
                segments = [enc_data[boss_name][attempt], ]
                slice_tries = f"Try {attempt+1}"
                for diff, segm_data in self.SEGMENTS_SEPARATED[boss_name].items():
                    for segm in segm_data:
                        if segm.get("attempt") == attempt:
                            segment_type = segm.get("segment_type", "")
                            slice_tries = f"{diff} {segment_type}"
                            break
            elif segment_difficulty:
                slice_tries = f"{segment_difficulty} All"
                segments = [
                    [segment["start"], segment["end"]]
                    for segment in self.SEGMENTS_SEPARATED[boss_name][segment_difficulty]
                ]
            else:
                slice_tries = "All"
                segments = enc_data[boss_name]
            
            shift = get_shift(path)
            self.segments_apply_shift(segments, shift_s=shift)
        
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": slice_name,
            "SLICE_TRIES": slice_tries,
            "BOSS_NAME": boss_name,
        }
    
    # def get_default_params(self, path: str, query: str, args: dict) -> dict:
    def get_default_params(self, request) -> dict:
        PATH: str = request.path
        QUERY: str = request.query_string.decode()
        if QUERY:
            QUERY = f"?{QUERY}"
        cached_data = self.CACHE['get_default_params'][PATH]
        if QUERY in cached_data:
            return cached_data[QUERY]

        report_name_info = get_report_name_info(self.NAME)
        _server = report_name_info.get("server", "")
        if _server[-1].isdigit():
            _server = _server[:-1]
        parsed = self.parse_request(PATH, request.args)
        duration = self.get_fight_duration_total(parsed["SEGMENTS"])
        return_data = parsed | {
            "PATH": PATH,
            "QUERY": QUERY,
            "REPORT_ID": self.NAME,
            "REPORT_NAME": self.FORMATTED_NAME,
            "SEGMENTS_LINKS": self.SEGMENTS_QUERIES,
            "PLAYER_CLASSES": self.CLASSES_NAMES,
            "DURATION": duration,
            "DURATION_STR": duration_to_string(duration),
            "SPEC_ICON_TO_POSITION": SPEC_ICON_TO_POSITION,
            "SERVER": _server,
        }
        cached_data[QUERY] = return_data
        return return_data


    def get_spells(self, rewrite=False):
        try:
            return self.SPELLS
        except AttributeError:
            spells_data_file_name = self.relative_path("SPELLS_DATA.json")
            if rewrite or self.cache_files_missing(spells_data_file_name):
                _spells = logs_spells_list.get_all_spells(self.LOGS)
                file_functions.json_write(spells_data_file_name, _spells)
            else:
                try:
                    _spells = file_functions.json_read_no_exception(spells_data_file_name)
                except Exception:
                    return self.get_spells(rewrite=True)

            for spell_id, new_name in CUSTOM_SPELL_NAMES.items():
                if spell_id in _spells:
                    _spells[spell_id]["name"] = new_name
            self.SPELLS = logs_spells_list.spell_id_to_int(_spells)
            
            return self.SPELLS

    @property
    def SPELLS_WITH_ICONS(self):
        try:
            return self.__SPELLS_WITH_ICONS
        except AttributeError:
            _spells = self.get_spells()
            
            _icons = logs_spells_order.get_spells()
            for spell_id, spell_data in _spells.items():
                spell_data["icon"] = _icons.get(spell_id, UNKNOWN_ICON)

            _spells |= PASSIVE_SPELLS
            self.__SPELLS_WITH_ICONS = _spells
            return _spells

    def get_spell_name(self, spell_id):
        _spells = self.get_spells()
        spell_id = abs(int(spell_id))
        if spell_id in _spells:
            return _spells[spell_id]["name"]
        return "Unknown spell"

    def get_spells_colors(self, spells) -> dict[int, str]:
        if not spells:
            return {}
        all_spells = self.get_spells()
        return {
            spell_id: all_spells[abs(spell_id)]['color']
            for spell_id in spells
            if abs(spell_id) in all_spells
        }

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
    

    @cache_wrap
    def get_slice_damage_heal(self, s, f):
        logs_slice = self.LOGS[s:f]
        players_and_pets = self.get_players_and_pets_guids()
        return logs_dmg_heals.parse_both(logs_slice, players_and_pets)
    
    @cache_wrap
    def get_slice_damage_heal_absorbs(self, s, f):
        data = self.get_slice_damage_heal(s, f)
        for guid, v in self.get_absorbs_by_source(s, f).items():
            data["heal"][guid] += v
            data["heal_total"][guid] += v
        return data

    def get_slice_first_last_hit(self, s: int=None, f: int=None):
        if not s or type(s) != int:
            s = 0
        if not f or type(f) != int:
            f = 0
        return {
            "FIRST_HIT": logs_dmg_heals.readable_logs_line(self.LOGS[s]),
            "LAST_HIT": logs_dmg_heals.readable_logs_line(self.LOGS[f-1]),
        }
    
    def report_add_spec_info(self, specs: dict[str, int], data: dict[str, dict]):
        new_specs: dict[str, tuple(str, str)] = {}
        for unit_name in data:
            if unit_name.endswith('-A'):
                new_specs[unit_name] = ('Mutated Abomination', 'ability_rogue_deviouspoisons')
            elif unit_name == "Total":
                new_specs[unit_name] = ('Total', 'ability_hunter_readiness')
            elif unit_name in self.CLASSES_NAMES:
                new_specs[unit_name] = logs_player_spec.get_spec_info(specs[unit_name])
            else:
                new_specs[unit_name] = (unit_name, UNKNOWN_ICON)
        return new_specs

    def get_report_page_all(self, segments):
        combined_data = {
            "damage": defaultdict(int),
            "heal": defaultdict(int),
            "heal_total": defaultdict(int),
            "taken": defaultdict(int),
        }

        for s, f in segments:
            new_data = self.get_slice_damage_heal_absorbs(s, f)
            for k, _data in combined_data.items():
                add_new_numeric_data(_data, new_data[k])

        specs = self.get_players_specs_in_segments(*segments[0])
        return_data = {
            "DATA": combined_data,
            "SPECS": specs,
        }
        return_data.update(self.get_slice_first_last_hit(segments[0][0], segments[-1][-1]))
        return return_data

    @running_time
    def get_report_page_boss_only(self):
        enc_data = self.get_enc_data()
        segments = [x for y in enc_data.values() for x in y]
        combined_data = {
            "damage": defaultdict(int),
            "heal": defaultdict(int),
            "taken": defaultdict(int),
        }
        for s, f in segments:
            new_data = self.get_slice_damage_heal(s, f)
            for k, _data in combined_data.items():
                add_new_numeric_data(_data, new_data[k])

        specs = self.get_players_specs_in_segments(None, None)

        return_data = {
            "DATA": combined_data,
            "SPECS": specs,
        }
        return_data.update(self.get_slice_first_last_hit(segments[0][0], segments[-1][-1]))
        return return_data

    def convert_to_table_data(self, _data, duration):
        if not _data:
            return {}

        GUIDS = self.get_all_guids()
        _data = logs_dmg_heals.add_pets(_data, GUIDS)
        MAX_VALUE = max(_data.values())

        d = {}
        _total = sum(_data.values())
        d["Total"] = format_report_page_data(_total, duration, MAX_VALUE)
        d["Total"]["percent"] = 0
        
        for name, value in _data.items():
            d[name] = format_report_page_data(value, duration, MAX_VALUE)
            
        return d

    @running_time
    def get_report_page_all_wrap(self, request):
        default_params = self.get_default_params(request)
        segments = default_params["SEGMENTS"]
        boss_name = default_params["BOSS_NAME"]
        mode = request.args.get("mode")

        DURATION = self.get_fight_duration_total(segments)

        if boss_name and boss_name != "all":
            _useful = self.useful_damage_all(segments, boss_name)["USEFUL"]
            _useful = sort_dict_by_value(_useful)
        else:
            _useful = {}    
        
        columns = {
            "useful": _useful,
        }
        if boss_name == "all":
            DD = self.get_report_page_boss_only()
        else:
            DD = self.get_report_page_all(segments)
        columns.update(DD["DATA"])

        TABLE = {}
        PLAYERS = {}
        for k, d in columns.items():
            TABLE[k] = self.convert_to_table_data(d, DURATION)
            PLAYERS.update(TABLE[k])
        
        specs = self.convert_dict_guids_to_names(DD["SPECS"])
        SPECS = self.report_add_spec_info(specs, PLAYERS)

        points = {}
        if mode and _useful and boss_name not in BOSSES_SKIP_POINTS:
            _useful_dps = self.convert_dict_guids_to_names({
                guid: dmg / DURATION
                for guid, dmg in _useful.items()
            })

            server = get_report_name_info(self.NAME)["server"]
            top1 = logs_top_db.SpecTop1(server, boss_name, mode)
            try:
                spec_top1 = {
                    spec: top1.get(spec)
                    for spec in set(specs.values())
                }
                points = {
                    name: f"{udps * 100 / spec_top1[specs[name]]:.1f}"
                    for name, udps in _useful_dps.items()
                    if name in specs
                }
            except (FileNotFoundError, AttributeError):
                pass

        return default_params | DD | {
            "DATA": TABLE,
            "SPECS": SPECS,
            "POINTS": points,
        }


    def get_spell_data_pet_name(self, spell_id: int, pet_name=None):
        spell_id = int(spell_id)
        spell_data = dict(self.SPELLS_WITH_ICONS[spell_id])
        spell_data["id"] = spell_id
        if pet_name:
            spell_data['name'] = f"{spell_data['name']} ({pet_name})"
        return spell_data
    
    @cache_wrap
    def data_given_breakdown(self, s, f, source, heal=False):
        logs_slice = self.LOGS[s:f]
        controlled_units = self.get_units_controlled_by(source)
        return logs_dmg_breakdown.given(logs_slice, controlled_units, heal)

    @cache_wrap
    def data_taken_breakdown(self, s, f, source, heal=False):
        logs_slice = self.LOGS[s:f]
        return logs_dmg_breakdown.taken(logs_slice, source, heal)
    
    def data_breakdown_gen(self, segments, source_guid_id, heal=False, taken=False):
        if taken:
            func = self.data_taken_breakdown
        else:
            func = self.data_given_breakdown

        for s,f in segments:
            yield func(s, f, source_guid_id, heal)

    def get_data_breakdown(self, segments_data) -> logs_dmg_breakdown.BreakdownTypeExtended:
        _other = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        _damage = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        _spells = {}
        _targets = set()

        def get_spell_data_pet_name_wrap(spell_id, pet_name=None):
            try:
                _spell_id = COMBINE_SPELLS.get(spell_id, spell_id)
                _spell_data = self.get_spell_data_pet_name(_spell_id, pet_name)
            except KeyError:
                _spell_data = self.get_spell_data_pet_name(spell_id, pet_name)
            spell_name = f'{_spell_data["id"]}{_spell_data["name"]}'
            if spell_name not in _spells:
                _spells[spell_name] = _spell_data
            return spell_name

        def reduce_data(data):
            for tGUID, sources in data.items():
                target_id = tGUID[:12] if tGUID.startswith("0xF") else tGUID
                _targets.add(target_id)
                for sGUID, spells in sources.items():
                    pet_name = self.get_pet_name(sGUID)
                    for spell_id, types in spells.items():
                        spell_name = get_spell_data_pet_name_wrap(spell_id, pet_name)
                        yield target_id, spell_name, types

        for data in segments_data:
            for target_id, spell_name, types in reduce_data(data["DAMAGE"]):
                for t, v in types.items():
                    _damage[target_id][spell_name][t].extend(v)
                    _damage["Total"][spell_name][t].extend(v)
            for target_id, spell_name, types in reduce_data(data["OTHER"]):
                for t, v in types.items():
                    _other[target_id][spell_name][t] += v
                    _other["Total"][spell_name][t] += v

        return {
            "DAMAGE": _damage,
            "OTHER": _other,
            "SPELLS": _spells,
            "TARGETS": _targets,
        }
    
    def get_numbers_breakdown_wrap(self, segments: list, source: str, filter_guid=None, heal=False, taken=False):
        if not source.startswith("0x"):
            source = self.name_to_guid(source)
            if not source:
                return {
                    "TARGETS": {},
                }
            if source.startswith("0xF"):
                source = source[:12]
        
        _segments_data = self.data_breakdown_gen(segments, source, heal, taken)
        _parsed = self.get_data_breakdown(_segments_data)
        _spells = _parsed["SPELLS"]

        if not filter_guid:
            OTHER = _parsed["OTHER"]["Total"]
            DAMAGE_HITS = _parsed["DAMAGE"]["Total"]
        else:
            filter_guid = filter_guid[:18]
            OTHER = _parsed["OTHER"][filter_guid]
            DAMAGE_HITS = _parsed["DAMAGE"][filter_guid]
        
        actual_sum = {
            spell_name: sum(sum(x) for x in d.values())
            for spell_name, d in DAMAGE_HITS.items()
        }

        if heal:
            if taken:
                _absorbs = self.get_absorbs_by_target_wrap(segments, source, filter_guid)
            else:
                _absorbs = self.get_absorbs_by_source_spells_wrap(segments, source, filter_guid)
            if _absorbs:
                for spell_id, v in _absorbs.items():
                    _spell_data = self.get_spell_data_pet_name(spell_id)
                    SPELL_NAME = _spell_data["name"]
                    if SPELL_NAME not in _spells:
                        _spells[SPELL_NAME] = _spell_data
                    actual_sum[SPELL_NAME] = v

        HITS_DATA = logs_dmg_breakdown.hits_data(DAMAGE_HITS)
        TARGETS = sort_by_name_type(
            (gid, self.guid_to_name(gid))
            for gid in _parsed["TARGETS"]
        )

        SPELLS = dict(sorted(sorted(_spells.items()), key=lambda x: actual_sum.get(x[0], 0), reverse=True))

        _data = self.breakdown_finish_formatting(actual_sum, OTHER)

        return _data | {
            "OTHER": OTHER,
            "SPELLS_DATA": SPELLS,
            "TARGETS": TARGETS,
            "HITS": HITS_DATA,
        }

    def breakdown_finish_formatting(
        self,
        actual_sum: dict[str, int],
        OTHER_SHIT: defaultdict[str, defaultdict[str, int]],
    ):
        ACTUAL_FORMATTED = format_total_data(actual_sum)
        actual_total = actual_sum['Total'] or 1
        ACTUAL_PERCENT =  {
            spell_id: format_percentage(value, actual_total)
            for spell_id, value in actual_sum.items()
        }

        CASTS = {
            spell: _data["CAST"]
            for spell, _data in OTHER_SHIT.items()
            if "CAST" in _data
        }

        reduced = defaultdict(int)
        REDUCED_DETAILED = defaultdict(dict)
        TOTAL_MISSES = defaultdict(int)
        MISS_DETAILED = defaultdict(dict)
        for spell, other_data in OTHER_SHIT.items():
            for k, v in other_data.items():
                if not v:
                    continue
                elif k in REDUCED_KEYS:
                    reduced[spell] += v
                    REDUCED_DETAILED[spell][k] = v
                elif k in MISS_KEYS:
                    TOTAL_MISSES[spell] += v
                    MISS_DETAILED[spell][k] = v

        for spell, data in REDUCED_DETAILED.items():
            for k, v in data.items():
                data[k] = separate_thousands(v)
        
        REDUCED_FORMATTED = format_total_data(reduced)
        REDUCED_PERCENT = {
            spell_id: format_percentage(value, value + actual_sum.get(spell_id, 0))
            for spell_id, value in reduced.items()
        }

        return {
            "ACTUAL": ACTUAL_FORMATTED,
            "ACTUAL_PERCENT": ACTUAL_PERCENT,
            "REDUCED": REDUCED_FORMATTED,
            "REDUCED_PERCENT": REDUCED_PERCENT,
            "REDUCED_DETAILED": REDUCED_DETAILED,
            "MISSES": dict(TOTAL_MISSES),
            "MISS_DETAILED": MISS_DETAILED,
            "CASTS": CASTS,
        }

    @running_time
    def get_comp_data(self, segments, class_filter: str, tGUID=None):
        class_filter = class_filter.lower()
        players = []
        targets = {}
        spells = {}
        for guid, class_name in self.get_classes().items():
            if class_name != class_filter:
                continue
            data = self.get_numbers_breakdown_wrap(segments, guid, filter_guid=tGUID)
            data["NAME"] = self.guid_to_name(guid)
            targets |= data["TARGETS"]
            spells |= data["SPELLS_DATA"]
            players.append(data)

        return json.dumps({
            "PLAYERS": players,
            "SPELLS": spells,
            "TARGETS": sort_by_name_type(targets.items()),
        })

    
    # POTIONS
    @cache_wrap
    def potions_info(self, s, f) -> dict[str, dict[str, int]]:
        logs_slice = self.LOGS[s:f]
        return logs_spell_info.get_potions_count(logs_slice)
    
    def sort_data_guids_by_name(self, data: dict):
        return dict(sorted(data.items(), key=lambda x: self.guid_to_name(x[0])))

    def add_missing_players(self, data, default=0, players=None):
        if players is None:
            players = self.get_players_guids()
        for guid in players:
            if guid not in data:
                data[guid] = default
        return data
    
    def potions_all(self, segments):
        potions = defaultdict(lambda: defaultdict(int))
        players: set[str] = set()

        for s, f in segments:
            _potions = self.potions_info(s, f)
            for spell_id, sources in _potions.items():
                add_new_numeric_data(potions[spell_id], sources)
                
            _specs = self.get_players_specs_in_segments(s, f)
            players.update(_specs)
        
        p_value = logs_spell_info.count_valuable(potions)
        for guid in players:
            if guid not in p_value:
                p_value[guid] = 0
        p_value = self.sort_data_guids_by_name(p_value)

        p_total = logs_spell_info.count_total(potions)
        p_total = self.sort_data_guids_by_name(p_total)

        p_total |= p_value
        p_total = sort_dict_by_value(p_total)
        p_total = self.convert_dict_guids_to_names(p_total)
        
        for spell_id, sources in potions.items():
            potions[spell_id] = self.convert_dict_guids_to_names(sources)

        return {
            "ITEM_INFO": logs_spell_info.ITEM_INFO,
            "ITEMS_TOTAL": p_total,
            "ITEMS": potions,
        }

    @cache_wrap
    def auras_info(self, s, f) -> defaultdict[str, dict[str, tuple[int, float]]]:
        logs_slice = self.LOGS[s:f]
        data = logs_spell_info.get_raid_buff_count(logs_slice)
        return logs_spell_info.get_auras_uptime(logs_slice, data)

    def auras_info_all(self, segments, trim_non_players=True):
        auras_uptime = defaultdict(lambda: defaultdict(list))
        auras_count = defaultdict(lambda: defaultdict(int))

        for s, f in segments:
            _auras = self.auras_info(s, f)
            for guid, aura_data in _auras.items():
                if trim_non_players and not is_player(guid):
                    continue
                for spell_id, (count, uptime) in aura_data.items():
                    auras_count[guid][spell_id] += count
                    auras_uptime[guid][spell_id].append(uptime)

        aura_info_set = set()
        auras_uptime_formatted = defaultdict(lambda: defaultdict(float))
        for guid, aura_data in auras_uptime.items():
            for spell_id, uptimes in aura_data.items():
                aura_info_set.add(spell_id)
                v = sum(uptimes) / len(uptimes) * 100
                auras_uptime_formatted[guid][spell_id] = f"{v:.2f}"
        
        self.add_missing_players(auras_count, {})
        self.add_missing_players(auras_uptime, {})

        auras_count_with_names = self.convert_dict_guids_to_names(auras_count)
        auras_uptime_with_names = self.convert_dict_guids_to_names(auras_uptime_formatted)

        filtered_aura_info = logs_spell_info.get_filtered_info(aura_info_set)

        return {
            "AURA_UPTIME": auras_uptime_with_names,
            "AURA_COUNT": auras_count_with_names,
            "AURA_INFO": filtered_aura_info,
        }


    @running_time
    def get_spell_count(self, s, f, spell_id_str):
        logs_slice = self.LOGS[s:f]
        return logs_spell_info.get_spell_count(logs_slice, spell_id_str)
    
    def spell_count_all(self, segments, spell_id: str):
        def sort_by_total(data: dict):
            return dict(sorted(data.items(), key=lambda x: x[1]["Total"], reverse=True))
        
        spell_id = spell_id.replace("-", "")
        all_spells = self.get_spells()
        if int(spell_id) not in all_spells:
            LOGGER_REPORTS.error(f"{spell_id} not in spells")
            return {
                "SPELLS": {},
            }
        
        spells_data: dict[str, dict[str, dict[str, int]]] = {}
        spells_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        all_targets: list[str] = ["Total", ]
        for s, f in segments:
            _segment_data = self.get_spell_count(s, f, spell_id)
            for flag, sources in _segment_data.items():
                for source_name, targets in sources.items():
                    for target_name, value in targets.items():
                        spells_data[flag][source_name]["Total"] += value
                        spells_data[flag][source_name][target_name] += value
                        if target_name not in all_targets:
                            all_targets.append(target_name)

        for flag in FLAG_ORDER:
            if flag in spells_data:
                spells_data[flag] = sort_by_total(spells_data.pop(flag))

        s_id = abs(int(spell_id))
        SPELL_DATA = self.SPELLS_WITH_ICONS[s_id]

        return {
            "SPELLS": spells_data,
            "TARGETS": all_targets,
            "SPELL_ID": spell_id,
            "SPELL_NAME": SPELL_DATA["name"],
            "SPELL_ICON": SPELL_DATA["icon"],
            "SPELL_COLOR": SPELL_DATA["color"],
        }

    @cache_wrap
    def useful_damage(self, s, f, targets: dict[str, str], boss_name: str):
        logs_slice = self.LOGS[s:f]

        damage = logs_dmg_useful.get_dmg(logs_slice, targets)
        useful = logs_dmg_useful.specific_useful(logs_slice, boss_name)
        return {
            "damage": damage,
            "useful": useful,
        }

    def convert_data_to_names(self, data: dict):
        guids = self.get_all_guids()
        return {
            guids[guid]["name"]: v
            for guid, v in data.items()
            if guid in guids
        }
    
    def add_total_and_names(self, data: dict):
        data_names = self.convert_data_to_names(data)
        data_names["Total"] = sum(data.values())
        return sort_dict_by_value(data_names)
    
    def data_visual_format(self, data):
        data_names = self.add_total_and_names(data)
        return {
            name: separate_thousands(v)
            for name, v in data_names.items()
        }

    @running_time
    def useful_damage_all(self, segments: list, boss_name: str):
        DAMAGE = defaultdict(lambda: defaultdict(int))
        USEFUL = defaultdict(lambda: defaultdict(int))

        boss_guid_id = self.name_to_guid(boss_name)
        targets = logs_dmg_useful.get_all_targets(boss_name, boss_guid_id)
        targets_useful = targets["useful"]
        targets_all = targets["all"]

        for s, f in segments:
            data = self.useful_damage(s, f, targets_all, boss_name)
            for guid_id, _dmg_new in data["damage"].items():
                add_new_numeric_data(DAMAGE[guid_id], _dmg_new)
            
            for guid_id, _dmg_new in data["useful"].items():
                targets_useful[guid_id] = guid_id
                add_new_numeric_data(USEFUL[guid_id], _dmg_new)

        guids = self.get_all_guids()
        damage_with_pets = logs_dmg_useful.combine_pets_all(DAMAGE, guids, trim_non_players=True, ignore_abom=True)
        useful_with_pets = logs_dmg_useful.combine_pets_all(USEFUL, guids, trim_non_players=True, ignore_abom=True)

        _combined = damage_with_pets | useful_with_pets
        damage_total = logs_dmg_useful.get_total_damage(damage_with_pets)
        useful_total = logs_dmg_useful.get_total_damage(_combined, targets_useful)

        custom_units = logs_dmg_useful.guid_to_useful_name(useful_with_pets)
        custom_groups = logs_dmg_useful.add_custom_units(damage_with_pets, boss_name)

        data_all = {
            "Useful": useful_total,
            "Total": damage_total,
        } | custom_units | custom_groups | damage_with_pets

        dmg_to_target = {
            targets_all.get(guid_id, guid_id): self.data_visual_format(_data)
            for guid_id, _data in data_all.items()
            if _data
        }

        players = self.add_total_and_names(useful_total)

        return {
            "TARGETS": dmg_to_target,
            "PLAYERS": players,
            "USEFUL": useful_total,
        }

    def pretty_print_players_data(self, data):
        guids = self.get_all_guids()
        data = sort_dict_by_value(data)
        for guid, value in data.items():
            print(f"{guids[guid]['name']:<12} {separate_thousands(value):>13}")

    @cache_wrap
    def grabs_info(self, s, f):
        logs_slice = self.LOGS[s:f]
        players = self.get_players_guids()
        return logs_valk_grabs.main(logs_slice, players)

    def valk_info_all(self, segments):
        grabs_total = defaultdict(int)
        all_grabs = []
        for s, f in segments:
            grabs = self.grabs_info(s, f)
            if grabs is None:
                continue
            all_grabs.extend(grabs)
            for g in grabs:
                for p in g:
                    grabs_total[p] += 1
        waves = list(range(1, len(all_grabs)+1))
        grabs_total = dict(sorted(grabs_total.items()))
        grabs_total = sort_dict_by_value(grabs_total)
        return {
            "ALL_GRABS": all_grabs,
            "GRABS_TOTAL": grabs_total,
            "WAVES": waves,
        }


    @cache_wrap
    def death_info(self, s, f, guid):
        logs_slice = self.LOGS[s:f]
        deaths = logs_deaths.get_deaths(logs_slice, guid)
        logs_deaths.sfjsiojfasiojfiod(deaths)
        return deaths
    
    def get_deaths(self, segments, guid):
        deaths = {}
        if guid:
            for s, f in segments:
                deaths |= self.death_info(s, f, guid)
        return {
            "DEATHS": deaths,
            "CLASSES": self.get_classes(),
            "PLAYERS": self.get_players_guids(),
            "GUIDS": self.get_all_guids(),
            "SPELLS": self.get_spells(),
        }

    @cache_wrap
    def get_powers(self, s, f):
        logs_slice = self.LOGS[s:f]
        return logs_power.asidjioasjdso(logs_slice)

    def powers_add_data(
        self,
        data: dict[str, dict[str, dict[str, int]]],
        new_data: dict[str, dict[str, dict[str, int]]]
    ):
        for power_name, targets in new_data.items():
            for guid, spells in targets.items():
                name = self.guid_to_name(guid)
                _guid = self.get_master_guid(guid)
                if _guid != guid:
                    master_name = self.guid_to_name(_guid)
                    name = f"{name} ({master_name})"
                
                for spell_id, value in spells.items():
                    data[power_name][name][spell_id] += value
    
    def get_power_data(self, spell_data, spell_id):
        if spell_id in spell_data:
            return spell_data[spell_id]

        spell_info = dict(logs_power.SPELLS.get(spell_id, {}))
        if not spell_info:
            spell_info = {
                "icon": UNKNOWN_ICON,
                "name": self.get_spell_name(spell_id)
            }
            LOGGER_UNUSUAL_SPELLS.info(f"{self.NAME} {spell_id} missing info")
        
        spell_info["value"] = 0
        spell_data[spell_id] = spell_info
        return spell_info

    @running_time
    def get_powers_all(self, segments):
        SPELLS: dict[str, dict] = {}
        TOTAL = defaultdict(lambda: defaultdict(int))
        POWERS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for s, f in segments:
            _data = self.get_powers(s, f)
            self.powers_add_data(POWERS, _data)
        
        for power_name, targets in POWERS.items():
            spell_data = {}
            for target_name, target_spells in targets.items():
                for spell_id, value in target_spells.items():
                    target_spells[spell_id] = separate_thousands(value)

                    TOTAL[power_name][target_name] += value
                    
                    spell_info = self.get_power_data(spell_data, spell_id)
                    spell_info["value"] += value
            
            SPELLS[power_name] = dict(sorted(spell_data.items(), key=lambda x: x[1]["value"], reverse=True))
            for power_data in spell_data.values():
                power_data["value"] = separate_thousands(power_data["value"])
        
        for targets in TOTAL.values():
            for target_name, value in targets.items():
                targets[target_name] = separate_thousands(value)

        labels = [(i, p) for i, p in enumerate(logs_power.POWER_TYPES.values()) if p in POWERS]
        
        return {
            "POWERS": POWERS,
            "TOTAL": TOTAL,
            "SPELLS": SPELLS,
            "LABELS": labels,
        }

    @cache_wrap
    def get_dps(self, s, f, player: str):
        logs_slice = self.LOGS[s:f]
        if player:
            guids = self.get_units_controlled_by(player)
        else:
            guids = self.get_players_and_pets_guids()
        data = logs_dps.get_raw_data(logs_slice, guids)
        logs_dps.convert_keys(data)
        return data

    def get_dps_wrap(self, data: dict):
        if not data:
            return {}

        enc_name = data.get("boss")
        attempt = data.get("attempt")
        if not enc_name or not attempt:
            return {}
        
        enc_data = self.get_enc_data()
        enc_name = BOSSES_FROM_HTML[enc_name]
        s, f = enc_data[enc_name][int(attempt)]
        player = data.get("player_name")
        _data = self.get_dps(s, f, player)
        if not _data:
            return {}
        refresh_window = data.get("sec")
        new_data = logs_dps.convert_to_dps(_data, refresh_window)
        logs_dps.convert_keys_to_str(new_data)
        return new_data

    @cache_wrap
    def get_spell_history(self, s: int, f: int, guid: str) -> dict[str, defaultdict[str, int]]:
        ts = self.get_timestamp()
        s_shifted = ts[self.find_index(s, 180)]
        logs_slice = self.LOGS[s_shifted:f]

        players_and_pets = self.get_players_and_pets_guids()
        data = logs_spells_order.get_history(logs_slice, guid, players_and_pets, s-s_shifted)

        _spells = self.SPELLS_WITH_ICONS
        data["SPELLS"] = {
            x: _spells[int(x)]
            for x in data["DATA"]
        }
        data["RDURATION"] = self.get_slice_duration(s, f)
        data["NAME"] = self.guid_to_name(guid)
        data["CLASS"] = self.get_classes().get(guid, "npc")

        return data
    
    def get_spell_history_wrap(self, segments: dict, player_name: str):
        s, f = segments[0]
        player = self.name_to_guid(player_name)
        return self.get_spell_history(s, f, player)
    
    def get_spell_history_wrap_json(self, segments: dict, player_name: str):
        return json.dumps((self.get_spell_history_wrap(segments, player_name)), default=list)
    
    
    @cache_wrap
    def _get_absorbs(self, s, f):
        if not s or not f:
            return {}, {}

        logs_slice = self.LOGS[s:f]
        specs = self.get_players_specs_in_segments(s, f)
        discos = {guid for guid, spec in specs.items() if spec == 21}
        events = logs_absorbs.parse_absorb_related(logs_slice, discos=discos)
        ABSORBS: dict[str, dict[str, dict[str, int]]] = {}
        DETAILS = {}
        
        for target, lines in events.items():
            _absorbs, _details = logs_absorbs.proccess_absorb(lines, discos, specs.get(target) == 1)
            ABSORBS[target] = _absorbs
            DETAILS[target] = _details

        return ABSORBS, DETAILS
    
    def get_absorbs(self, s, f):
        return self._get_absorbs(s, f)[0]
    
    def get_absorbs_details(self, s, f):
        return self._get_absorbs(s, f)[1]
    
    def get_absorbs_details_wrap(self, segments: list, target: str):
        if not target.startswith("0x0"):
            target = self.name_to_guid(target)

        if not target:
            return []
        
        DETAILS = []
        for s, f in segments:
            _a = self.get_absorbs_details(s, f)
            if target in _a:
                DETAILS.extend(self.get_absorbs_details(s, f)[target])
        return DETAILS

    def get_absorbs_by_source(self, s, f):
        _abs = defaultdict(int)
        _data = self.get_absorbs(s, f)
        for target, sources in _data.items():
            for source, spells in sources.items():
                for spell_id, value in spells.items():
                    _abs[source] += value
        return _abs
    
    def get_absorbs_by_source_spells_wrap(self, segments: list, source_filter: str, target_filter: str=None):
        ABSORBS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for s, f in segments:
            _data = self.get_absorbs(s, f)
            for _target, sources in _data.items():
                for _source, spells in sources.items():
                    for spell_id, value in spells.items():
                        ABSORBS[_source]["Total"][spell_id] += value
                        ABSORBS[_source][_target][spell_id] += value
        
        if not target_filter:
            target_filter = "Total"
        return ABSORBS[source_filter][target_filter]
    
    def get_absorbs_by_target_wrap(self, segments, target_filter, source_filter=None):
        _abs = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for s, f in segments:
            _data = self.get_absorbs(s, f)
            for _target, sources in _data.items():
                for _source, spells in sources.items():
                    # print(_source, spells)
                    for spell_id, value in spells.items():
                        # _abs[source][spell_id] += value
                        _abs[_target]["Total"][spell_id] += value
                        _abs[_target][_source][spell_id] += value
        if not source_filter:
            source_filter = "Total"
        return _abs[target_filter][source_filter]


    def logs_custom_search(self, query: dict[str, str]):
        logs = self.get_logs()
        # for 
        return 'Spell not found'
    

    def lady_spirits(self, s, f):
        logs_slice = self.LOGS[s:f]
        data = logs_lady_spirits.filter_spirits(logs_slice)
        key_by = logs_lady_spirits.KEY_LADY_POPED_BY
        k_dmg = logs_lady_spirits.KEY_LADY_DAMAGE
        k_prev = logs_lady_spirits.KEY_LADY_PREVENTED
        players = self.get_players_guids()
        for x in data:
            guid = x[key_by]
            x[key_by] = players.get(guid, guid)
            x["targets_n"] = len(x[logs_lady_spirits.KEY_LADY_TARGETS])
            x[k_dmg] = separate_thousands(x[k_dmg])
            x[k_prev] = separate_thousands(x[k_prev])
        return data
    
    def lady_spirits_wrap(self, segments):
        pulls = []
        for s, f in segments:
            pulls.append(self.lady_spirits(s, f))
        return pulls
    