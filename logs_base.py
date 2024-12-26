from c_player_classes import SPECS_LIST

import json

import logs_fight_separator
import logs_get_time
import logs_player_spec
import logs_spells_list
import logs_units_guid
from h_debug import Loggers, running_time


PLAYER = "0x0"
TYPES = (str, bool, type(None))
LOGGER_REPORTS = Loggers.reports
TOTAL_DUMMY_SPEC = {
    "spec": "Total",
    "icon": "ability_hunter_readiness",
    "name": "Total",
    "class": "total",
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


class THE_LOGS(
    logs_fight_separator.Fights,
    logs_spells_list.Spells,
    logs_get_time.Timestamps,
):
    @property
    def ALL_GUIDS(self) -> dict[str, dict[str, str]]:
        try:
            return self._guids_all
        except AttributeError:
            pass

        self._guids_data()
        return self._guids_all

    @property
    def PLAYERS_GUIDS(self) -> dict[str, str]:
        try:
            return self._guids_players
        except AttributeError:
            pass

        self._guids_data()
        return self._guids_players

    @property
    def PLAYER_CLASSES(self) -> dict[str, str]:
        try:
            return self._guids_classes
        except AttributeError:
            pass

        self._guids_data()
        return self._guids_classes
        
    @property
    def PLAYERS_NAMES(self):
        try:
            return self._players_names
        except AttributeError:
            players = self.get_players_guids()
            self._players_names = {v:k for k,v in players.items()}
            return self._players_names
    
    @property
    def PLAYERS_PETS(self):
        try:
            return self._players_pets
        except AttributeError:
            self._players_pets = {
                guid
                for guid, p in self.ALL_GUIDS.items()
                if p.get("master_guid", "").startswith(PLAYER)
            }
            return self._players_pets
    
    @property
    def FRIENDLY_IDS(self):
        try:
            return self._friendly_ids
        except AttributeError:
            d = {
                guid[6:12]
                for guid in self.PLAYERS_PETS
            }
            d.add("000000")
            self._friendly_ids = d
            return d
            
    @property
    def CLASSES_NAMES(self) -> dict[str, str]:
        try:
            return self._classes_names
        except AttributeError:
            self._classes_names = self.convert_dict_guids_to_names(self.PLAYER_CLASSES)
            return self._classes_names

    @property
    def UNIT_ID_TO_NAME(self):
        try:
            return self._unit_id_to_name
        except AttributeError:
            d = {
                guid[6:-6]: info["name"]
                for guid, info in self.ALL_GUIDS.items()
            }
            d |= self.get_players_guids()
            d["000000"] = "nil"
            d["0x0000000000000000"] = "nil"
            self._unit_id_to_name = d
            return self._unit_id_to_name
        
    @property
    def CONTROLLED_UNITS(self):
        try:
            return self._controlled_units
        except AttributeError:
            self._controlled_units = {}
            return self._controlled_units

    def _guids_data(self):
        try:
            self._read_guids()
        except FileNotFoundError:
            self._redo_guids()

    def _read_guids(self):
        self._guids_all = self.relative_path("GUIDS_DATA.json").json()
        self._guids_players = self.relative_path("PLAYERS_DATA.json").json()
        self._guids_classes = self.relative_path("CLASSES_DATA.json").json()
    
    @running_time
    def _redo_guids(self):
        parsed = logs_units_guid.guids_main(self.LOGS, self.ENCOUNTER_DATA)

        if parsed['missing_owner']:
            LOGGER_REPORTS.error(f"{self.NAME} | Missing owners: {parsed['missing_owner']}")
        
        self._guids_all = parsed['everything']
        self._guids_players = parsed['players']
        self._guids_classes = parsed['classes']

        to_write = (
            ("GUIDS_DATA.json", self._guids_all),
            ("PLAYERS_DATA.json", self._guids_players),
            ("CLASSES_DATA.json", self._guids_classes),
        )

        for file_name, data in to_write:
            self.relative_path(file_name).json_write(data, indent=2)

    def get_players_guids(self, whitelist_guids=None, whitelist_names=None):
        players = self.PLAYERS_GUIDS
        if whitelist_guids is not None:
            return {k:v for k,v in players.items() if k in whitelist_guids}
        elif whitelist_names is not None:
            return {k:v for k,v in players.items() if v in whitelist_names}
        else:
            return players

    @cache_wrap
    def get_players_specs_in_segments(self, s, f) -> dict[str, int]:
        '''specs = {guid: spec_index}'''
        logs_slice = self.LOGS[s:f]
        return logs_player_spec.get_specs(logs_slice, self.PLAYERS_GUIDS, self.PLAYER_CLASSES)
    
    def get_slice_spec_info(self, s, f):
        new_specs: dict[str, tuple[str, str]] = {}
        specs = self.get_players_specs_in_segments(s, f)
        for unit_guid, spec_index in specs.items():
            spec_data = SPECS_LIST[spec_index]
            new_specs[unit_guid] = {
                "spec": spec_data.name,
                "icon": spec_data.icon,
                "name": self.guid_to_name(unit_guid),
                "class": self.PLAYER_CLASSES[unit_guid],
            }
        new_specs["Total"] = TOTAL_DUMMY_SPEC
        return new_specs

    def name_to_guid(self, name: str) -> str:
        if name.startswith("0x"):
            return name

        if name in self.PLAYERS_NAMES:
            return self.PLAYERS_NAMES[name]
        
        for guid, data in self.ALL_GUIDS.items():
            if data['name'] == name:
                return guid
        
        return None
    
    def guid_to_name(self, guid: str):
        name = self.UNIT_ID_TO_NAME.get(guid)
        if not name:
            name = self.ALL_GUIDS.get(guid, {}).get("name", "Unknown")
        return name
    
    def sort_data_guids_by_name(self, data: dict):
        return dict(sorted(data.items(), key=lambda x: self.guid_to_name(x[0])))

    def convert_dict_guids_to_names(self, data: dict):
        return {
            self.guid_to_name(guid): value
            for guid, value in data.items()
        }
    
    def get_master_guid(self, guid: str):
        master_guid = self.ALL_GUIDS[guid].get('master_guid')
        if not master_guid:
            return guid
        return self.ALL_GUIDS.get(master_guid, {}).get('master_guid', master_guid)
    
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
        
        controlled_units = {
            guid
            for guid, p in self.ALL_GUIDS.items()
            if p.get("master_guid") == master_guid or master_guid in guid
        }
        controlled_units.add(master_guid)
        self.CONTROLLED_UNITS[master_guid] = controlled_units
        return controlled_units

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

    def get_classes_with_names_json(self):
        try:
            return self._classes_with_names_json
        except AttributeError:
            self._classes_with_names_json = json.dumps(self.CLASSES_NAMES)
            return self._classes_with_names_json
    
    def find_index(self, line_index: int, shift: int=0, slice_end=False):
        if line_index is None:
            if slice_end:
                return self.TIMESTAMPS[-1]
            return 0
        if not shift:
            shift = 0
        return bisect_left(self.TIMESTAMPS, line_index) + shift
    
    def find_shifted_log_line(self, line_index: int, shift: int):
        if not line_index or not shift:
            return line_index
        index = self.find_index(line_index, shift)
        new_index = index + shift
        return self.TIMESTAMPS[new_index]
    
    def find_sec_from_start(self, s):
        return self.get_timedelta_seconds(self.LOGS[0], self.LOGS[s])
    
    def precise_shift(self, from_index: int, shift_seconds: int):
        if not shift_seconds:
            return from_index
        first_line = self.LOGS[from_index]
        shifted_index = shift_seconds + int(self.find_sec_from_start(from_index))
        s = self.TIMESTAMPS[shifted_index-1]
        f = self.TIMESTAMPS[shifted_index+1]
        for i, current_line in enumerate(self.LOGS[s:f]):
            td = self.get_timedelta(first_line, current_line).total_seconds()
            if td > shift_seconds:
                return s+i
        return self.TIMESTAMPS[shifted_index]


    def get_all_guids(self):
        return self.ALL_GUIDS

    def get_classes(self):
        return self.PLAYER_CLASSES

    def get_enc_data(self):
        return self.ENCOUNTER_DATA
    
    def get_timestamp(self):
        return self.TIMESTAMPS
    
    def get_spells(self):
        return self.SPELLS
