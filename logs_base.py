import json
import os
from collections import defaultdict

import file_functions
import logs_fight_separator
import logs_player_spec
import logs_units_guid
import logs_get_time
import logs_spells_list
from constants import (
    LOGS_CUT_NAME_OLD,
    LOGS_CUT_NAME,
    UNKNOWN_ICON,
)
from c_path import (
    Directories,
    Files,
)
from c_spells import (
    COMBINE_SPELLS,
    CUSTOM_SPELL_NAMES,
)
from h_datetime import (
    MONTHS,
    get_now,
    to_dt_year_precise,
)
from h_debug import (
    Loggers,
    running_time,
    setup_logger,
)
from h_other import get_report_name_info

LOGGER_REPORTS = Loggers.reports

PLAYER = "0x0"

TYPES = (str, bool, type(None))

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

TOTAL_DUMMY_SPEC = {
    "spec": "Total",
    "icon": "ability_hunter_readiness",
    "name": "Total",
    "class": "total",
}

@Files.spell_icons_db.cache_until_new_self
def get_spells_int(spells_json) -> dict[str, str]:
    spells_data = spells_json.json_ignore_error()
    return {
        int(spell_id): icon_name
        for icon_name, _spells in spells_data.items()
        for spell_id in _spells
    }

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
            pass
        
        _dir = Directories.logs / self.NAME
        if not _dir.is_dir():
            _dir.copy_from_backup()
        if not _dir.is_dir():
            raise FileNotFoundError
        self.__path = _dir
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
    
    def get_timedelta_seconds(self, last, now):
        return self.get_timedelta(last, now).total_seconds()

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
    
    def get_slice_spec_info(self, s, f):
        new_specs: dict[str, tuple[str, str]] = {}
        specs = self.get_players_specs_in_segments(s, f)
        for unit_guid, spec_index in specs.items():
            spec, icon = logs_player_spec.get_spec_info(spec_index)
            new_specs[unit_guid] = {
                "spec": spec,
                "icon": icon,
                "name": self.guid_to_name(unit_guid),
                "class": self.CLASSES[unit_guid],
            }
        new_specs["Total"] = TOTAL_DUMMY_SPEC
        return new_specs
        
    @property
    def PLAYERS_NAMES(self):
        try:
            return self.__PLAYERS_NAMES
        except AttributeError:
            players = self.get_players_guids()
            self.__PLAYERS_NAMES = {v:k for k,v in players.items()}
            return self.__PLAYERS_NAMES

    @property
    def unit_id_to_name(self):
        try:
            return self.__unit_id_to_name
        except AttributeError:
            guids = self.get_all_guids()
            __d = {
                guid[6:-6]: info["name"]
                for guid, info in guids.items()
            }
            __d |= self.get_players_guids()
            __d["000000"] = "nil"
            __d["0x0000000000000000"] = "nil"
            self.__unit_id_to_name = __d
            return self.__unit_id_to_name

    def name_to_guid(self, name: str) -> str:
        if name.startswith("0x"):
            return name

        if name in self.PLAYERS_NAMES:
            return self.PLAYERS_NAMES[name]
        
        guids = self.get_all_guids()
        for guid, data in guids.items():
            if data['name'] == name:
                return guid
        
        return None
    
    def guid_to_name(self, guid: str):
        name = self.unit_id_to_name.get(guid)
        if not name:
            name = self.get_all_guids().get(guid, {}).get("name", "Unknown")
        return name
    
    def sort_data_guids_by_name(self, data: dict):
        return dict(sorted(data.items(), key=lambda x: self.guid_to_name(x[0])))

    def convert_dict_guids_to_names(self, data: dict):
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
    
    @property
    def FRIENDLY_IDS(self):
        try:
            return self.__PLAYERS_PETS_IDS
        except AttributeError:
            self.__PLAYERS_PETS_IDS = {
                guid[6:12]
                for guid in self.PLAYERS_PETS
            }
            self.__PLAYERS_PETS_IDS.add("000000")
            return self.__PLAYERS_PETS_IDS

    def get_players_and_pets_guids(self):
        try:
            return self.PLAYERS_AND_PETS
        except AttributeError:
            players = set(self.get_players_guids())
            self.PLAYERS_AND_PETS = players | self.PLAYERS_PETS
            return self.PLAYERS_AND_PETS
    
    def add_missing_players(self, data, default=0, players=None):
        if players is None:
            players = self.get_players_guids()
        for guid in players:
            if guid not in data:
                data[guid] = default
        return data
            
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
    
    def find_sec_from_start(self, s):
        return self.get_timedelta_seconds(self.LOGS[0], self.LOGS[s])
    
    @running_time
    def precise_shift(self, from_index: int, shift_seconds: int):
        if not shift_seconds:
            return from_index
        ts = self.get_timestamp()
        first_line = self.LOGS[from_index]
        shifted_index = shift_seconds + int(self.find_sec_from_start(from_index))
        s = ts[shifted_index-1]
        f = ts[shifted_index+1]
        for i, current_line in enumerate(self.LOGS[s:f]):
            td = self.get_timedelta(first_line, current_line).total_seconds()
            if td > shift_seconds:
                return s+i
        return ts[shifted_index]


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

    def convert_to_main_spell_id(self, spell_id: str):
        if spell_id not in COMBINE_SPELLS:
            return spell_id
        
        _spell_id = COMBINE_SPELLS[spell_id]
        if int(_spell_id) not in self.get_spells():
            return spell_id
        
        return _spell_id

    @property
    def SPELLS_WITH_ICONS(self):
        try:
            return self.__SPELLS_WITH_ICONS
        except AttributeError:
            _spells = self.get_spells()
            
            _icons = get_spells_int()
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
    