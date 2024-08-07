import json
from collections import defaultdict

import logs_base
import logs_absorbs
import logs_spells_order
import logs_check_difficulty
import logs_deaths
import logs_dmg_breakdown
import logs_dmg_heals
import logs_dmg_useful
import logs_dps
import logs_player_spec
import logs_power
import logs_spell_info
import logs_top_db
import logs_lady_spirits
import logs_valk_grabs
import logs_ucm

from c_spells import UNKNOWN_ICON
from c_bosses import (
    BOSSES_GUIDS,
    BOSSES_FROM_HTML,
)
from h_debug import (
    running_time,

)
from h_other import (
    separate_thousands,
    sort_dict_by_value,
    add_new_numeric_data,
    get_report_name_info,
    convert_to_html_name,
)

SHIFT = {
    'spell': 10,
    'consumables': 10,
    'player_auras': 10,
}
BOSSES_SKIP_POINTS = {
    "Valithria Dreamwalker",
    "Gunship",
    "Heroic Training Dummy",
    "Highlord's Nemesis Trainer",
}
ENTITIES_KEYS = (
    "BOSSES",
    "PLAYERS' PERMANENT PETS",
    "PLAYERS' TEMPORARY PETS",
    "PLAYERS",
    "OTHER",
)

def duration_to_string(t: float):
    milliseconds = t % 1 * 1000
    if milliseconds < 1:
        milliseconds = milliseconds * 1000
    
    t = int(t)
    hours = t // 3600
    minutes = t // 60 % 60
    seconds = t % 60
    return f"{hours}:{minutes:0>2}:{seconds:0>2}.{milliseconds:0>3.0f}"

def is_guid(s: str):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def get_shift(request_path: str):
    url_comp = request_path.split('/')
    try:
        return SHIFT.get(url_comp[3], 0)
    except IndexError:
        return 0

def format_report_page_data(value: int, duration: float, max_value: int):
    return {
        "value": separate_thousands(value),
        "per_second": separate_thousands(calc_per_sec(value, duration)),
        "percent": calc_percent(value, max_value),
    }

def calc_percent(value: int, max_value: int):
    if max_value == 0:
        return 0
    return value * 100 // max_value

def calc_per_sec(value: int, duration: float, precision: int=1):
    v = value / (duration or 1)
    precision = 10**precision
    return int(v * precision) / precision

def get_dict_int(d: dict, key, default=None):
    try:
        v = d[key]
        try:
            return int(v)
        except Exception:
            return default
    except KeyError:
        return default

def str_slice_from_to(s: str, start, end):
    try:
        i_s = s.index(start)
        try:
            s2 = s[i_s+1:]
            i_f = s2.index(end)
            return s[:i_s] + s2[i_f:]
        except ValueError:
            return s[:i_s]
    except ValueError:
        return s

def query_no_custom(query: str):
    query = str_slice_from_to(query, "&target=", "&")
    query = str_slice_from_to(query, "&fc=", "&")
    query = str_slice_from_to(query, "&sc=", "&")
    return query


class THE_LOGS(
    logs_dmg_breakdown.SourceNumbers,
    logs_dmg_useful.UsefulDamage,
    logs_absorbs.Absorbs,
    logs_spells_order.Timeline,
    logs_spell_info.Consumables,
    logs_spell_info.SpellCount,
    logs_spell_info.AuraUptime,
    logs_dps.Dps,
    logs_power.Powers,
    logs_deaths.Deaths,
    logs_lady_spirits.LadySpirits,
    logs_valk_grabs.ValkGrabs,
    logs_ucm.UCM,
):
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
    
    def _attempt_name(self, boss_name, attempt):
        for diff, segm_data in self.SEGMENTS_SEPARATED[boss_name].items():
            for segm in segm_data:
                if segm.get("attempt") == attempt:
                    segment_type = segm.get("segment_type", "")
                    return f"{diff} {segment_type}"
        return f"Try {attempt+1}"

    def parse_request(self, path: str, args: dict) -> dict:
        segment_difficulty = args.get("mode")
        attempt = get_dict_int(args, "attempt")
        boss_name = args.get("boss")
        ts = self.get_timestamp()
        enc_data = self.get_enc_data()
        if boss_name == "all":
            slice_name = "Bosses"
            slice_tries = "All"
            segments = [x for y in enc_data.values() for x in y]
        
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
            boss_name = BOSSES_FROM_HTML[boss_name]
            slice_name = boss_name
            if attempt is not None:
                slice_tries = self._attempt_name(boss_name, attempt)
                s, f = enc_data[boss_name][attempt]
                sc = get_dict_int(args, "sc", 0)
                fc = get_dict_int(args, "fc", 0)
                s_shifted = self.precise_shift(s, sc)
                f_shifted = f
                if fc and fc < self.get_slice_duration(s, f):
                    f_shifted = self.precise_shift(s, fc)
                segments = [[s_shifted, f_shifted], ]
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
        if _server and _server[-1].isdigit():
            _server = _server[:-1]
        parsed = self.parse_request(PATH, request.args)
        duration = self.get_fight_duration_total(parsed["SEGMENTS"])
        return_data = parsed | {
            "PATH": PATH,
            "QUERY": QUERY,
            "QUERY_NO_CUSTOM": query_no_custom(QUERY),
            "REPORT_ID": self.NAME,
            "REPORT_NAME": self.FORMATTED_NAME,
            "SEGMENTS_LINKS": self.SEGMENTS_QUERIES,
            "PLAYER_CLASSES": self.CLASSES_NAMES,
            "DURATION": duration,
            "DURATION_STR": duration_to_string(duration),
            "SERVER": _server,
        }
        cached_data[QUERY] = return_data
        return return_data


    @logs_base.cache_wrap
    def get_slice_damage_heal(self, s, f):
        logs_slice = self.LOGS[s:f]
        players_and_pets = self.get_players_and_pets_guids()
        return logs_dmg_heals.parse_both(logs_slice, players_and_pets)
    
    @logs_base.cache_wrap
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
        new_specs: dict[str, tuple[str, str]] = {}
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
        if not _data:
            return {}
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
            _useful = self.target_damage_all(segments, boss_name)["useful_total"]
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
        sc = get_dict_int(request.args, "sc")
        fc = get_dict_int(request.args, "fc")
        if sc and sc != 0 or fc and fc == 0:
            pass
        elif mode and _useful and boss_name not in BOSSES_SKIP_POINTS:
            _useful_dps = {
                guid: dmg / DURATION
                for guid, dmg in _useful.items()
            }
            _useful_dps = self.convert_dict_guids_to_names(_useful_dps)
            server = get_report_name_info(self.NAME)["server"]
            points = logs_top_db.RaidRank(server, boss_name, mode).get_rank_wrap(_useful_dps, specs)

        return default_params | DD | {
            "DATA": TABLE,
            "SPECS": SPECS,
            "POINTS": points,
        }
    
    @running_time
    def get_numbers_breakdown_wrap(self, segments: list, source: str, filter_guid=None, heal=False, taken=False):
        if is_guid(source):
            source_guid = source
        else:
            source_guid = self.name_to_guid(source)
        
        if not source_guid or not source_guid.startswith("0x"):
            return {
                "TARGETS": {},
            }
        
        a = self.numbers_combined(segments, heal)
        if not taken:
            sources = self.get_units_controlled_by(source_guid)
            _filtered = self._filter(a, sources, filter_guid)
        else:
            _filtered = self._filter(a, filter_guid, source_guid)
            _filtered["PETS"] = {}
        
        if heal:
            if taken:
                _absorbs = self.get_absorbs_by_target_wrap(segments, source_guid, filter_guid)
            else:
                _absorbs = self.get_absorbs_by_source_spells_wrap(segments, source_guid, filter_guid)
            
            _actual = _filtered["ACTUAL"]
            for spell_id, v in _absorbs.items():
                _actual[spell_id] = v

        _formatted = self._format(_filtered)
        
        owner_guid = self.get_master_guid(source_guid)
        if owner_guid != source_guid:
            _formatted["OWNER_NAME"] = self.guid_to_name(owner_guid)
        _formatted["SOURCE_NAME"] = self.guid_to_name(source_guid)
        _formatted["IS_PLAYER"] = source in self.CLASSES_NAMES
        _formatted["SOURCE"] = source
        return _formatted

    @running_time
    def get_comparison_data(self, segments, class_filter: str, tGUID=None):
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
            "TARGETS": targets,
        }, default=list)

    @logs_base.cache_wrap
    def entities(self, s, f):
        _damage = self.numbers_damage(s, f)['ACTUAL']
        guids = set()
        for source_guid, targets_data in _damage.items():
            guids.add(source_guid)
            guids.update(targets_data)
        _data = {
            k: []
            for k in ENTITIES_KEYS
        }
        for guid in sorted(guids):
            name = self.guid_to_name(guid)
            if guid[:3] == "0x0":
                key = "PLAYERS"
            elif guid[:5] == "0xF14":
                owner_name = self.guid_to_name(self.get_master_guid(guid))
                name = f"{name} ({owner_name})"
                key = "PLAYERS' PERMANENT PETS"
            elif guid[6:12] in BOSSES_GUIDS:
                key = "BOSSES"
            else:
                key = "OTHER"
                owner_guid = self.get_master_guid(guid)
                if owner_guid != guid:
                    if owner_guid[:3] == "0x0":
                        key = "PLAYERS' TEMPORARY PETS"
                    owner_name = self.guid_to_name(owner_guid)
                    name = f"{name} ({owner_name})"
            _data[key].append((name, guid))

        return {
            "ENTITIES": _data,
        }

    def logs_custom_search(self, query: dict[str, str]):
        logs = self.get_logs()
        # for 
        return 'Spell not found'
    