from c_path import Files, PathExt
from c_spells import (
    COMBINE_SPELLS,
    CUSTOM_SPELL_NAMES,
    SPELLS_SCHOOLS,
    UNKNOWN_ICON,
    UNUSUAL_SPELLS,
)
from h_debug import Loggers, running_time
from logs_core import Logs

LOGGER_UNUSUAL_SPELLS = Loggers.unusual_spells

_EMPTY = ""

KEYS_TO_SAVE = ("name", "school")

class Spell:
    __slots__ = "id", "name", "name_lower", "school", "icon", "color"
    def __init__(
        self,
        id: str,
        name: str,
        school: str,
        icon=UNKNOWN_ICON,
    ) -> None:
        self.id = id
        self.name = name
        self.name_lower = name.lower()
        self.school = school
        self.icon = icon
        self.color = self._color()

    def __str__(self):
        return " | ".join((
            f"{self.id:>5}",
            f"{int(self.school, 16):>3}",
            self.color,
            self.name,
            self.icon,
        ))

    __repr__ = __str__

    def to_dict(self):
        return {
            key: getattr(self, key, _EMPTY)
            for key in ["id", "name", "color", "icon"]
        }
    
    def json_format(self):
        return {
            key: getattr(self, key, _EMPTY)
            for key in KEYS_TO_SAVE
        }

    def _color(self):
        try:
            color_code_int = int(self.school, 16)
        except ValueError:
            color_code_int = 0
        
        try:
            color = SPELLS_SCHOOLS[color_code_int]
        except KeyError:
            color = UNUSUAL_SPELLS[color_code_int]
            LOGGER_UNUSUAL_SPELLS.debug(f"MISSING SPELL COLOR: {self}")
        
        return color

PASSIVE_SPELLS = {
    49497: Spell(
        id="49497",
        name='Spell Deflection',
        school='0x1',
        icon='spell_deathknight_spelldeflection',
    ),
    52286: Spell(
        id="52286",
        name='Will of the Necropolis',
        school='0x1',
        icon='ability_creature_cursed_02',
    ),
}

@Files.spell_icons_db.cache_until_new_self
def spells_icons(spells_json: PathExt) -> dict[str, str]:
    return {
        spell_id: icon_name
        # int(spell_id): icon_name
        for icon_name, _spells in spells_json._json().items()
        for spell_id in _spells
    }

def add_spells_icons(spells: dict[str, Spell]):
    _icons = spells_icons()
    for spell in spells.values():
        spell.icon = _icons.get(spell.id, UNKNOWN_ICON)

def spells_raname_to_custom(spells: dict[str, Spell]):
    for spell_id, new_name in CUSTOM_SPELL_NAMES.items():
        if spell_id in spells:
            spells[spell_id].name = new_name

def spell_id_to_int(data: dict[str, Spell]):
    return {
        int(spell_id): spell_data
        for spell_id, spell_data in data.items()
        if spell_id.isdigit()
    }


class Spells(Logs):
    @property
    def SPELLS(self):
        try:
            return self._spells
        except AttributeError:
            self._spells = self._get_spells()
            return self._spells

    def convert_to_main_spell_id(self, spell_id: str):
        if spell_id not in COMBINE_SPELLS:
            return spell_id
        
        _spell_id = COMBINE_SPELLS[spell_id]
        if int(_spell_id) not in self.SPELLS:
            return spell_id
        
        return _spell_id

    def get_spell_name(self, spell_id):
        spell_id_int = abs(int(spell_id))
        _spell = self.SPELLS.get(spell_id_int) or self.SPELLS[0]
        return _spell.name
    
    @running_time
    def filtered_spell_list(self, _filter: str):
        if not _filter:
            return {}
        
        if _filter.isdigit():
            return {
                spell_id: spell.name
                for spell_id, spell in self.SPELLS.items()
                if _filter in spell.id
            }
        
        _filter = _filter.lower()
        return {
            spell_id: spell.name
            for spell_id, spell in self.SPELLS.items()
            if _filter in spell.name_lower
        }
    
    def _get_spells(self):
        try:
            spells = self._read_spells()
        except Exception:
            spells = self._redo_spells()
        
        add_spells_icons(spells)
        spells_raname_to_custom(spells)
        
        spells = spell_id_to_int(spells)
        spells.update(PASSIVE_SPELLS)
        return spells
    
    def _read_spells(self):
        spells_data_file_name = self.relative_path("SPELLS_DATA.json")
        j: dict[str, dict[str, str]]
        j = spells_data_file_name._json()
        return {
            spell_id: Spell(id=spell_id, **v)
            for spell_id, v in j.items()
        }
    
    @running_time
    def _redo_spells(self):
        spells = self._get_all_spells()
        spell_ids = (
            spell_id
            for spell_id in spells
            if spell_id.isdigit()
        )
        spells = {
            spell_id: spells[spell_id]
            for spell_id in sorted(spell_ids, key=int)
        }
        self._save_spells(spells)
        return spells

    def _get_all_spells(self):
        spells = {
            "0": Spell("0", "Unknown", "0x1"),
            "1": Spell("1", "Melee", "0x1"),
        }
        for line in self.LOGS:
            try:
                _line = line.split(',', 7)
                if _line[6] in spells: 
                    continue
                etc = _line[-1].split(',', 2)
                spells[_line[6]] = Spell(_line[6], etc[0], etc[1])
            except IndexError:
                pass

        return spells
    
    def _save_spells(self, _spells: dict[str, Spell]):
        spells_data_file_name = self.relative_path("SPELLS_DATA.json")
        j = {
            spell_id: spell.json_format()
            for spell_id, spell in _spells.items()
        }
        spells_data_file_name.json_write(j)  


def _test1():
    spells_icons()
    report = Spells("24-04-23--20-57--Meownya--Lordaeron")
    report = Spells("24-05-14--21-17--Meownya--Lordaeron")
    report.LOGS
    report._redo_spells()
    # report.SPELLS
    # for q,w in report.SPELLS.items():
    #     print(w)
    # _r = 1
    # for _ in range(_r):
    #     q2 = report._get_all_spells()

    # report.filtered_spell_list("FIRE")

    # print(q2['48170'])



if __name__ == "__main__":
    _test1()
