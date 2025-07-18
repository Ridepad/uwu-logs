import json
from collections import defaultdict
from dataclasses import dataclass

import logs_base
import logs_absorbs
import logs_spells_order
import logs_check_difficulty
import logs_deaths
import logs_dmg_breakdown
import logs_dmg_heals
import logs_dmg_useful
import logs_dps
import logs_power
import logs_spell_info
import logs_lady_spirits
import logs_toc_valks
import logs_valk_grabs
import logs_ucm
import logs_auras_v2

from c_spells import UNKNOWN_ICON
from c_bosses import (
    BOSSES_GUIDS,
    BOSSES_FROM_HTML,
)
from c_player_classes import SPECS_LIST
from h_debug import running_time
from h_other import (
    add_new_numeric_data,
    convert_to_html_name,
    get_report_name_info,
    separate_thousands,
    sort_dict_by_value,
)

SHIFT = {
    'spell': 10,
    'consumables': 10,
    'player_auras': 10,
}
ENTITIES_KEYS = (
    "BOSSES",
    "PLAYERS' PERMANENT PETS",
    "PLAYERS' TEMPORARY PETS",
    "PLAYERS",
    "OTHER",
)

def is_guid(s: str):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

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


def to_int(v: str, default: int=None):
    try:
        return int(v)
    except Exception:
        return default

@dataclass
class QuerySegment:
    boss: str = ""
    mode: str = ""
    attempt: str = ""
    s: str = None
    f: str = None
    sc: str = None
    fc: str = None
    target: str = None

    @property
    def start(self):
        return to_int(self.s)
    @property
    def end(self):
        return to_int(self.f)
    @property
    def custom_start(self):
        return to_int(self.sc)
    @property
    def custom_end(self):
        return to_int(self.fc)
    @property
    def encounter_name(self):
        return BOSSES_FROM_HTML.get(self.boss, self.boss)


class THE_LOGS(
    logs_check_difficulty.LogsSegments,
    logs_dmg_breakdown.SourceNumbers,
    logs_dmg_useful.UsefulDamage,
    logs_absorbs.Absorbs,
    logs_spells_order.Timeline,
    logs_spell_info.Consumables,
    logs_spell_info.SpellCount,
    logs_spell_info.AuraUptime,
    logs_auras_v2.AurasUptimes,
    logs_dps.Dps,
    logs_power.Powers,
    logs_deaths.Deaths,
    logs_lady_spirits.LadySpirits,
    logs_valk_grabs.ValkGrabs,
    logs_ucm.UCM,
    logs_toc_valks.ValksTOC,
):
    def get_segments_data_json(self, encounter_name_html: str):
        if encounter_name_html not in BOSSES_FROM_HTML:
            return "[]"
        encounter_name = BOSSES_FROM_HTML[encounter_name_html]
        if encounter_name not in self.SEGMENTS:
            return "[]"
        _data = [
            segment.segment_str
            for segment in self.SEGMENTS[encounter_name]
        ]
        return json.dumps(_data)
    
    def _attempt_name(self, boss_name: str, attempt: int):
        segment = self.SEGMENTS[boss_name][attempt]
        return segment.segment_type

    def parse_request_all_bosses(self):
        slice_name = "Bosses"
        slice_tries = "All"
        segments = [x for y in self.ENCOUNTER_DATA.values() for x in y]
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": slice_name,
            "SLICE_TRIES": slice_tries,
        }
    
    def parse_request_custom_slice(self, query: QuerySegment):
        slice_name = "Custom Slice"
        slice_tries = ""
        if query.start and query.end:
            segments = [[self.TIMESTAMPS[query.start], self.TIMESTAMPS[query.end]]]
        else:
            segments =  [[None, None]]
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": slice_name,
            "SLICE_TRIES": slice_tries,
        }
    
    def parse_request_by_attempt(self, query: QuerySegment):
        boss_name = BOSSES_FROM_HTML[query.boss]
        attempt_int = int(query.attempt)

        try:
            segment = self.SEGMENTS[boss_name][attempt_int]
        except IndexError:
            segment = self.SEGMENTS[boss_name][-1]
        except KeyError:
            return self.parse_request_custom_slice(query)
        
        s_shifted = self.precise_shift(segment.start, query.custom_start)
        f_shifted = segment.end
        if query.custom_end and query.custom_end < segment.duration:
            f_shifted = self.precise_shift(segment.start, query.custom_end)
        segments = [[s_shifted, f_shifted], ]
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": boss_name,
            "SLICE_TRIES": segment.segment_diff_type,
        }
    
    def parse_request_by_difficulty(self, query: QuerySegment):
        boss_name = BOSSES_FROM_HTML[query.boss]
        segments = self.ENCOUNTER_DATA[boss_name]
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": boss_name,
            "SLICE_TRIES": "All",
        }
    
    def parse_request_last_kill_for_difficulty(self, query: QuerySegment):
        boss_name = BOSSES_FROM_HTML[query.boss]
        segment = self.get_latest_kill(boss_name, query.mode)
        if segment is None:
            return self.parse_request_custom_slice(query)
        segments = [[segment.start, segment.end]]
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": boss_name,
            "SLICE_TRIES": segment.segment_diff_type,
        }
    
    def parse_request_all_boss_segments(self, query: QuerySegment):
        boss_name = BOSSES_FROM_HTML[query.boss]
        segments = [
            [segment.start, segment.end]
            for segment in self.SEGMENTS[boss_name]
            if segment.difficulty == query.mode
        ]
        return {
            "SEGMENTS": segments,
            "SLICE_NAME": boss_name,
            "SLICE_TRIES": f"{query.mode} All",
        }

    def parse_request(self, query: QuerySegment) -> dict:
        if query.boss == "all":
            return self.parse_request_all_bosses()
        
        if query.boss not in BOSSES_FROM_HTML:
            return self.parse_request_custom_slice(query)
        
        if query.attempt.isdigit():
            return self.parse_request_by_attempt(query)
        
        if not query.mode:
            return self.parse_request_by_difficulty(query)
        
        if query.attempt == "kill":
            return self.parse_request_last_kill_for_difficulty(query)
        
        return self.parse_request_all_boss_segments(query)

    # def get_default_params(self, path: str, query: str, args: dict) -> dict:
    def get_default_params(self, request) -> dict:
        # print('>>>>> get_default_params')
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
        query_data = QuerySegment(**request.args)
        parsed = self.parse_request(query_data)
        duration = self.get_fight_duration_total(parsed["SEGMENTS"])
        return_data = parsed | {
            "PATH": PATH,
            "QUERY": QUERY,
            "QUERY_NO_CUSTOM": query_no_custom(QUERY),
            "REPORT_ID": self.NAME,
            "REPORT_NAME": self.FORMATTED_NAME,
            "SEGMENTS_LINKS": self.SEGMENTS_QUERIES,
            "SEGMENTS_KILLS": self.SEGMENTS_KILLS,
            "PLAYER_CLASSES": self.CLASSES_NAMES,
            "DURATION": duration,
            "DURATION_STR": self.duration_to_string(duration),
            "SERVER": _server,
        }
        cached_data[QUERY] = return_data
        return return_data
    
    def request_get_kill_segment(self, request):
        query_data = QuerySegment(**request.args)
        boss_name = BOSSES_FROM_HTML[query_data.boss]
        return self.get_latest_kill(boss_name, query_data.mode)


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
                spec_index = specs[unit_name]
                spec = SPECS_LIST[spec_index]
                new_specs[unit_name] = (spec.name, spec.icon)
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

        _data = logs_dmg_heals.add_pets(_data, self.ALL_GUIDS)
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
    def get_report_page_all_wrap(self, segments: list[tuple[int, int]], boss_name: str):
        boss_name = BOSSES_FROM_HTML.get(boss_name, boss_name)

        if not boss_name or  boss_name == "all":
            _useful = {}
        else:
            _useful = self.target_damage_all(segments, boss_name)["useful_total"]
            _useful = sort_dict_by_value(_useful)
        
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
        DURATION = self.get_fight_duration_total(segments)
        for k, d in columns.items():
            TABLE[k] = self.convert_to_table_data(d, DURATION)
            PLAYERS.update(TABLE[k])
        
        specs = self.convert_dict_guids_to_names(DD["SPECS"])
        SPECS = self.report_add_spec_info(specs, PLAYERS)

        return {
            "DATA": TABLE,
            "SPECS": SPECS,
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
    