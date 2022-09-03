import json
import os
from collections import defaultdict

import dmg_breakdown
import dmg_heals
import logs_dmg_useful
import logs_auras
import logs_check_difficulty
import logs_fight_separator
import logs_get_time
import logs_player_spec
import logs_spell_info
import logs_spells_list
import logs_units_guid
import logs_valks3
import logs_valk_grabs
from constants import (
    MONTHS, FLAG_ORDER, LOGS_DIR,
    add_new_numeric_data, add_space, get_report_name_info, is_player,
    json_read, json_read_no_exception, json_write, running_time, setup_logger,
    sort_dict_by_value, get_now, to_dt_simple_year, zlib_text_read)

IGNORED_ADDS = ['Treant', 'Shadowfiend', 'Ghouls']
PLAYER = "0x0"
SHIFT = {
    'spell': 10,
    'consumables': 10,
    'player_auras': 10,
}

def get_shift(request_path: str):
    url_comp = request_path.split('/')
    try:
        return SHIFT.get(url_comp[3], 0)
    except IndexError:
        return 0

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
    
@running_time
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


class THE_LOGS:
    GUIDS: dict[str, dict[str, str]]
    PLAYERS: dict[str, str]
    CLASSES: dict[str, str]
    SEGMENTS: dict[str, list[tuple[str]]]

    def __init__(self, logs_name: str) -> None:
        self.loading = False
        self.NAME = logs_name
        self.PATH = os.path.join(LOGS_DIR, logs_name)
        if not os.path.exists(self.PATH):
            os.makedirs(self.PATH, exist_ok=True)
            print('LOG: Created folder:', self.PATH)

        self.year = int(logs_name[:2]) + 2000

        self.last_access = get_now()

        self.bosses_convert: dict[str, str] = {}
        self.DURATIONS: dict[str, float] = {}
        self.TARGETS: dict[str, dict[str, set[str]]] = {}
        self.CACHE: dict[str, dict[str, dict]] = {x: {} for x in dir(self) if "__" not in x}
        self.CONTROLLED_UNITS: dict[str, set[str]] = {}

    def relative_path(self, s: str):
        return os.path.join(self.PATH, s)

    def get_formatted_name(self):
        try:
            return self.FORMATTED_NAME
        except AttributeError:
            report_name_info = get_report_name_info(self.NAME)
            time = report_name_info['time'].replace('-', ':')
            year, month, day = report_name_info['date'].split("-")
            month = MONTHS[int(month)-1][:3]
            date = f"{day} {month} {year}"
            name = report_name_info['name']
            self.FORMATTED_NAME = f"{date}, {time} - {name}"
            return self.FORMATTED_NAME

    def get_logger(self):
        try:
            return self.LOGGER_LOGS
        except AttributeError:
            log_file = self.relative_path('log.log')
            logger = setup_logger(f"{self.NAME}_logger", log_file)
            self.LOGGER_LOGS = logger
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
            logs = zlib_text_read(logs_cut_file_name).splitlines()
            self.LOGS = logs
        
        return logs[s:f]

    def to_dt(self, last, now):
        return to_dt_simple_year(now, self.year) - to_dt_simple_year(last, self.year)
    
    def get_slice_first_last_lines(self, s, f):
        return self.get_logs()[s or 0], self.get_logs()[f or -1]
    
    def get_slice_duration(self, s, f):
        slice_ID = f"{s}_{f}"
        if slice_ID in self.DURATIONS:
            return self.DURATIONS[slice_ID]
        first_line, last_line = self.get_slice_first_last_lines(s, f)
        dur = self.to_dt(first_line, last_line).total_seconds()
        self.DURATIONS[slice_ID] = dur
        return dur

    def get_fight_duration_total(self, segments):
        durations = []
        for s, f in segments:
            durations.append(self.get_slice_duration(s, f))
        return sum(durations)

    def get_fight_duration_total_str(self, segments):
        return convert_duration(self.get_fight_duration_total(segments))
        
    def get_enc_data(self, rewrite=False):
        try:
            return self.ENCOUNTER_DATA
        except AttributeError:
            enc_data_file_name = self.relative_path("ENCOUNTER_DATA.json")
            if rewrite or self.cache_files_missing(enc_data_file_name):
                logs = self.get_logs()
                self.ENCOUNTER_DATA = logs_fight_separator.main(logs)
                json_write(enc_data_file_name, self.ENCOUNTER_DATA, indent=None)
            else:
                enc_data: dict[str, list[tuple[int, int]]]
                enc_data = json_read(enc_data_file_name)
                self.ENCOUNTER_DATA = enc_data
            return self.ENCOUNTER_DATA
    
    def new_guids(self, guids_data_file_name, players_data_file_name, classes_data_file_name):
        logs = self.get_logs()
        enc_data = self.get_enc_data()
        parsed = logs_units_guid.guids_main(logs, enc_data)
        _guids = parsed['everything']
        _players = parsed['players']
        _classes = parsed['classes']
        json_write(guids_data_file_name, _guids)
        json_write(players_data_file_name, _players)
        json_write(classes_data_file_name, _classes)
        return _guids, _players, _classes
    
    def get_guids(self, rewrite=False):
        try:
            return self.GUIDS, self.PLAYERS, self.CLASSES
        except AttributeError:
            files = [
                self.relative_path("GUIDS_DATA.json"),
                self.relative_path("PLAYERS_DATA.json"),
                self.relative_path("CLASSES_DATA.json")
            ]
            
            if rewrite or self.cache_files_missing(files):
                self.GUIDS, self.PLAYERS, self.CLASSES = self.new_guids(*files)
            else:
                self.GUIDS, self.PLAYERS, self.CLASSES = [
                    json_read_no_exception(_file_name)
                    for _file_name in files
                ]
            
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
            
    def get_classes_with_names(self):
        try:
            return self.CLASSES_NAMES
        except AttributeError:
            classes = self.get_classes()
            players = self.get_players_guids()
            self.CLASSES_NAMES = {players[guid]: class_name for guid, class_name in classes.items()}
            return self.CLASSES_NAMES
        
    
    def get_timestamp(self, rewrite=False):
        try:
            return self.TIMESTAMP
        except AttributeError:
            timestamp_data_file_name = self.relative_path("TIMESTAMP_DATA.json")
            if rewrite or self.cache_files_missing(timestamp_data_file_name):
                logs = self.get_logs()
                self.TIMESTAMP = logs_get_time.ujiowfuiwefhuiwe(logs)
                json_write(timestamp_data_file_name, self.TIMESTAMP, indent=None)
            else:
                timestamp_data: list[int]
                timestamp_data = json_read(timestamp_data_file_name)
                self.TIMESTAMP = timestamp_data
            return self.TIMESTAMP
    
    def find_index(self, n, shift=0):
        if n is None:
            return
        ts = self.get_timestamp()
        for i, line_n in enumerate(ts, -shift):
            if n <= line_n:
                return max(i, 0)
    
    def convert_slice_to_time(self, s=None, f=None):
        ts = self.get_timestamp()
        if s is not None:
            s = ts[s]
        if f is not None:
            f = ts[f]
        return s, f


    def attempt_time(self, boss_name, attempt, shift=0):
        enc_data = self.get_enc_data()
        s, f = enc_data[boss_name][attempt]
        s = self.find_index(s, 2+shift)
        f = self.find_index(f, 1)
        return s, f
        
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

    def get_segment_queries(self):
        try:
            return self.SEGMENTS_QUERIES
        except AttributeError:
            segm_links: dict[str, dict] = {}
            boss_html = self.BOSSES_TO_HTML
            separated = self.SEGMENTS_SEPARATED
            for boss_name, diffs in separated.items():
                href1 = f"?boss={boss_html[boss_name]}"
                a = {"href": href1, "class_name": "boss-link", "text": f"All {boss_name} segments"}
                segm_links[boss_name] = {
                    'link': a,
                    'links': {
                        diff_id: self.make_segment_query_diff(segments, boss_name, href1, diff_id)
                        for diff_id, segments in diffs.items()
                    }
                }
                # boss_data = segm_links[boss_name] = {'link': a}
                # boss_data['links'] = {
                #     diff_id: self.make_segment_query_diff(segments, boss_name, href1, diff_id)
                #     for diff_id, segments in diffs.items()
                # }
            self.SEGMENTS_QUERIES = segm_links
            return segm_links
        
    def get_segments_separated(self):
        try:
            return self.SEGMENTS_SEPARATED
        except AttributeError:
            segments = self.get_segments_data()
            self.SEGMENTS_SEPARATED = logs_check_difficulty.separate_modes(segments)
            return self.SEGMENTS_SEPARATED

    def get_segments_data(self):
        try:
            return self.SEGMENTS
        except AttributeError:
            logs = self.get_logs()
            enc_data = self.get_enc_data()
            _data = logs_check_difficulty.get_segments(logs, enc_data)

            self.BOSSES_TO_HTML = _data['boss_html']
            self.BOSSES_FROM_HTML = {v:k for k, v in self.BOSSES_TO_HTML.items()}
            
            self.SEGMENTS = _data['segments']
            return self.SEGMENTS

        
    def get_spells(self, rewrite=False):
        try:
            return self.SPELLS
        except AttributeError:
            spells_data_file_name = self.relative_path("SPELLS_DATA.json")
            if rewrite or self.cache_files_missing(spells_data_file_name):
                logs = self.get_logs()
                self.SPELLS = logs_spells_list.get_all_spells(logs)
                json_write(spells_data_file_name, self.SPELLS)
            else:
                _spells = json_read_no_exception(spells_data_file_name)
                self.SPELLS = logs_spells_list.spell_id_to_int(_spells)
            return self.SPELLS

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
    
    
    def parse_request(self, request):
        args: dict = request.args
        shift = get_shift(request.path)
        enc_data = self.get_enc_data()
        ts = self.get_timestamp()
        segments = self.get_segments_data()
        separated = self.get_segments_separated()

        slice_name = "Custom Slice"
        slice_tries = ""
        boss_name_html = args.get("boss")
        boss_name = self.BOSSES_FROM_HTML.get(boss_name_html, "")
        segment_difficulty = args.get("mode")
        attempt = args.get("attempt", type=int)
        if boss_name:
            slice_name = self.BOSSES_FROM_HTML[boss_name_html]
            if attempt is not None:
                slice_tries = f"Try {attempt+1}"
                segments = [enc_data[boss_name][attempt], ]
            elif segment_difficulty:
                slice_tries = segment_difficulty
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
            "slice_name": slice_name,
            "slice_tries": slice_tries,
            "query": query,
            "boss_name": boss_name,
        }

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


    @running_time
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
        data['specs'] = logs_player_spec.get_specs(logs_slice, players, classes)

        first_line = logs_slice[0].split(',', 8)
        last_line = logs_slice[-1].split(',', 8)
        print(first_line)
        print(last_line)
        data['first_hit'] = f"{first_line[0]} {first_line[1]} {first_line[3]} -> {first_line[5]} with {first_line[7]}"
        if last_line[1] == "UNIT_DIED":
            data['last_hit'] = f"{last_line[0]} {last_line[1]} {last_line[5]}"
        else:
            data['last_hit'] = f"{last_line[0]} {last_line[1]} {last_line[3]} -> {last_line[5]} with {last_line[7]}"

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
                specs[unit_name] = logs_player_spec.get_spec_info(player_class)
                print(f"{unit_name} doenstt have spec!")
            # elif unit_name not in classes_names:
            #     print(f"{unit_name} not in classes_names!")


    def get_report_page_all(self, segments):
        return_dict = {}
        damage = defaultdict(int)
        heal = defaultdict(int)
        specs = {}

        for s, f in segments:
            _data = self.report_page(s, f)
            add_new_numeric_data(damage, _data["damage"])
            add_new_numeric_data(heal, _data["heal"])
            specs |= _data['specs']
            return_dict["FIRST_HIT"] = _data['first_hit']
            return_dict["LAST_HIT"] = _data['last_hit']

        total_duration = self.get_fight_duration_total(segments)

        damage = self.dry_data(damage, total_duration)
        heal = self.dry_data(heal, total_duration)

        self.report_add_missing_specs(specs, damage, heal)

        return return_dict | {
            "DAMAGE": damage,
            "HEAL": heal,
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
        targets: set[str] = set()
        info_data['targets'] = targets
        actual = defaultdict(lambda: defaultdict(list))
        info_data['actual'] = actual

        for s, f in segments:
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

    @running_time
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
        response = []
        for guid, class_name in self.get_classes().items():
            if class_name != class_filter:
                continue
            name = self.guid_to_name(guid)
            data = {
                "name": name,
                "data": self.player_info_all(segments, guid, tGUID)
            }
            # yield f"{json.dumps(data, separators=(',', ':'))}\n"
            response.append(data)
            # yield json.dumps(response)
        return json.dumps(response)

    
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
        potions = defaultdict(lambda: defaultdict(int))

        for s, f in segments:
            _potions = self.potions_info(s, f)
            for spell_id, sources in _potions.items():
                add_new_numeric_data(potions[spell_id], sources)
        

        pots = {x: self.convert_dict_guids_to_name(y) for x,y in potions.items()}
        
        p_total = logs_spell_info.count_total(potions)
        p_total = sort_dict_by_value(p_total)
        p_total = self.add_missing_players(p_total)
        p_total = self.convert_dict_guids_to_name(p_total)

        return {
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

        auras_count_with_names = self.convert_dict_guids_to_name(auras_count)
        auras_uptime_with_names = self.convert_dict_guids_to_name(auras_uptime_formatted)

        filtered_aura_info = logs_spell_info.get_filtered_info(aura_info_set)

        return {
            "AURA_UPTIME": auras_uptime_with_names,
            "AURA_COUNT": auras_count_with_names,
            "AURA_INFO": filtered_aura_info,
        }


    @running_time
    def get_spell_count(self, s, f, spell_id_str) -> dict[str, dict[str, int]]:
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['get_spell_count'].setdefault(spell_id_str, {})
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
                "SPELLS": {},
                "TABS": {},
            }
        
        spells: dict[str, dict[str, dict[str, int]]] = {}

        for s, f in segments:
            _spells = self.get_spell_count(s, f, spell_id)
            for flag, _types in _spells.items():
                _flag = spells.setdefault(flag, {})
                for _type, names in _types.items():
                    _t = _flag.setdefault(_type, {})
                    for name, value in names.items():
                        _t[name] = _t.get(name, 0) + value
        
        spells = {x: spells[x] for x in FLAG_ORDER if x in spells}

        for flag_info in spells.values():
            for sources, sources_info in flag_info.items():
                flag_info[sources] = sort_dict_by_value(sources_info)
        
        tabs = [(flag.lower().replace('_', '-'), flag) for flag in spells]

        _spells = self.get_spells()
        s_id = abs(int(spell_id))
        spell_name = _spells.get(s_id, {}).get('name', '')
        spell_name = f"{spell_id} {spell_name}"

        return {
            "SPELLS": spells,
            "TABS": tabs,
            "SPELL_NAME": spell_name,
            "SPELL_ID": s_id,
        }


    def useful_damage(self, s, f, targets, boss_name):
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['useful_damage']
        if slice_ID in cached_data:
            return cached_data[slice_ID]

        logs_slice = self.get_logs(s, f)

        specific = logs_dmg_useful.specific_useful(logs_slice, boss_name)
        damage = logs_dmg_useful.get_dmg(logs_slice, targets)
        data = {
            "damage": specific | damage,
            "specific": set(specific),
        }
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
        all_data = defaultdict(lambda: defaultdict(int))

        boss_guid_id = self.name_to_guid(boss_name)
        targets = logs_dmg_useful.get_all_targets(boss_name, boss_guid_id)
        targets_useful = targets["useful"]
        targets_all = targets["all"]
        table_heads = ["", "Total Useful"]

        for s, f in segments:
            data = self.useful_damage(s, f, targets_all, boss_name)
            
            for target_name in data["specific"]:
                targets_useful[target_name] = target_name
                # if target_name not in table_heads:
                #     table_heads.append(target_name)
            
            _damage: dict[str, dict[str, int]] = data["damage"]
            for guid_id, _dmg_new in _damage.items():
                add_new_numeric_data(all_data[guid_id], _dmg_new)

        guids = self.get_all_guids()
        all_data = logs_dmg_useful.combine_pets_all(all_data, guids, trim_non_players=True)
    
        targets_useful_dmg = logs_dmg_useful.combine_targets(all_data, targets_useful)
        targets_useful_dmg = self.add_total_and_names(targets_useful_dmg)

        _formatted_dmg = {
            guid_id: self.add_total_and_names(_data)
            for guid_id, _data in all_data.items()
            if _data
        }

        table_heads.extend([targets_all.get(guid_id, guid_id) for guid_id in _formatted_dmg])

        return {
            "HEADS": table_heads,
            "TOTAL": targets_useful_dmg,
            "FORMATTED": _formatted_dmg,
        }


    def get_auras(self, s, f, filter_guid):
        logs_slice = self.get_logs(s, f)
        a = logs_auras.AurasMain(logs_slice)
        data = a.main(filter_guid)
        spell_colors = self.get_spells_colors(data['spells'])
        all_spells = self.get_spells()
        return {
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
            durations.append(self.get_slice_duration(s, f))
    


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
        return logs_player_spec.get_specs_no_names(logs_slice, players, classes)


    def grabs_info(self, s, f):
        slice_ID = f"{s}_{f}"
        cached_data = self.CACHE['grabs_info']
        if slice_ID in cached_data:
            return cached_data[slice_ID]
        
        logs_slice = self.get_logs(s, f)
        players = self.get_players_guids()
        grabs = logs_valk_grabs.main(logs_slice, players)
        cached_data[slice_ID] = grabs
        return grabs

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
