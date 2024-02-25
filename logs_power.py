from collections import defaultdict

import logs_base
from constants import (
    UNKNOWN_ICON,
    LOGGER_UNUSUAL_SPELLS,
    running_time,
    separate_thousands,
)

POWER_TYPES = {
    '0': 'mana',
    # Mana will range from 0 to the maximum mana a unit has. Player mana pools are calculated based on a base mana pool plus a certain amount given by the Intellect stat. This is the default power type for most non-player units, although there are exceptions. As of World of Warcraft: Legion Legion, mana is used by Druids, Mages, Mistweaver Monks, Paladins, Priests, Shamans and Warlocks.
    '1': 'rage',
    # Rage is used by Warriors and Druids in [Bear Form]. Rage goes from 0 to 100, but may be increased via player talents. Rage degenerates back to 0 out of combat.
    '3': 'energy',
    # Energy is used by Rogues and Druids in [Cat Form]. Energy goes from 0 to 100, but may be increased via player talents.
    '6': 'runic',
    # Runic Power is used by Death Knights. It is gained via certain abilities, and does not degenerate out of combat.
    '2': 'focus',
    # Focus is used by hunter pets. Focus goes from 0 to 100, and has a slow regeneration rate, but certain abilities will generate focus.
    '4': 'happiness',
    # Pet happiness.
    '5': 'runes',
    # Runes are used as a power type for Death Knights. By default, they have 6 runes (1 & 2 are blood, 3 & 4 are frost, 5 & 6 are unholy), but certain talents and abilities may change the type of a rune. Runes can be converted into a Death Rune, which can be used as any other type of rune. While runes are used by Death Knights, it does not appear that the Blizzard UI code uses this spell power type. Rather, runes are managed through the RUNE_POWER_UPDATE event via the GetRuneCooldown() API call.
}

def get_powers(logs: list[str]):
    powers = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for line in logs:
        if "_ENERGIZE" not in line:
            continue
        try:
            _, _, _, _, tguid, _, spell_id, _, _, amount, power_type = line.split(',')
            powers[power_type][tguid][spell_id] += int(amount)
        except ValueError:
            pass
    
    return {
        POWER_TYPES[power_type]: data
        for power_type, data in powers.items()
    }


class Powers(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def get_powers(self, s, f):
        logs_slice = self.LOGS[s:f]
        return get_powers(logs_slice)

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

        spell_info = dict(self.SPELLS_WITH_ICONS.get(int(spell_id), {}))
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

        labels = [(i, p) for i, p in enumerate(POWER_TYPES.values()) if p in POWERS]
        
        return {
            "POWERS": POWERS,
            "TOTAL": TOTAL,
            "SPELLS": SPELLS,
            "LABELS": labels,
        }
