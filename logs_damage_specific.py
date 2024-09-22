from collections import defaultdict
from typing import TypedDict
from h_debug import running_time

FESTER_SPAMMERS = {
    0,  # Death Knight
    1,  # Blood
    2,  # Frost
    3,  # Unholy
    4,  # Druid
    5,  # Balance
    6,  # Feral Combat
    7,  # Restoration
    8,  # Hunter
    9,  # Beast Mastery
    10, # Marksmanship
    11, # Survival
    15, # Frost
    16, # Paladin
    17, # Holy
    # 18, # Protection
    19, # Retribution
    22, # Holy
    31, # Restoration
    36, # Warrior
    37, # Arms
    38, # Fury
    # 39, # Protection
}

class ValksDamage(TypedDict):
    overkill: defaultdict[str, int]
    useful: defaultdict[str, int]

class FesterPlayerDamage:
    __slots__ = "stacks", "increased_by", "useful", "total"
    def __init__(self) -> None:
        self.stacks = 0
        self.increased_by = 1.0
        self.useful = 0
        self.total = 0

    def change_stacks(self, flag: str):
        if flag == "SPELL_AURA_APPLIED_DOSE":
            self.stacks += 1
        elif flag == "SPELL_AURA_APPLIED":
            self.stacks = 1
        elif flag == "SPELL_AURA_REMOVED":
            self.stacks = 0
        else:
            return
        
        self.increased_by = 1 + self.stacks / 10

    def add_damage(self, damage: int, overkill: int):
        self.total += damage
        self.useful += int(damage / self.increased_by) - overkill

@running_time
def _fester_useful(logs_slice: list[str]):
    players: defaultdict[str, FesterPlayerDamage] = defaultdict(FesterPlayerDamage)
    
    for line in logs_slice:
        if ",72553," in line:
            _, flag, _, _, target_guid, _ = line.split(',', 5)
            players[target_guid].change_stacks(flag)
            continue
        
        if "DAMAGE" not in line:
            continue
        
        _line = line.split(',', 11)
        if _line[4][6:12] != "008F12":
            continue
        
        try:
            dmg = int(_line[9])
            overkill = int(_line[10])
            players[_line[2]].add_damage(dmg, overkill)
        except ValueError:
            pass

    return players

@running_time
def fester_useful(logs_slice: list[str], specs: dict[str, int]):
    players_damage = _fester_useful(logs_slice)
    d = {}
    for guid, player in players_damage.items():
        spec = specs.get(guid)
        if spec == 1 and player.useful < 2_000_000:
            d[guid] = player.total
        elif spec in FESTER_SPAMMERS:
            d[guid] = player.useful
        else:
            d[guid] = player.total
    return d


def _is_valk(guid: str):
    return guid[6:-6] == '008F01'
def dmg_gen_valk(logs: list[str]):
    casted_life_siphon = {}
    for line in logs:
        if '8F01' not in line:
            continue
        if "_DAMAGE" not in line:
            continue
        _, _, source_guid, _, target_guid, _, _, _, _, damage, _ = line.split(',', 10)
        if target_guid in casted_life_siphon:
            pass
        elif _is_valk(target_guid):
            yield source_guid, target_guid, int(damage)
        elif _is_valk(source_guid):
            casted_life_siphon[source_guid] = True

@running_time
def get_valks_dmg(logs: list[str], half_hp=2992500 // 2) -> ValksDamage:
    valks_useful = defaultdict(int)
    valks_overkill = defaultdict(int)

    valks_dmg_taken = defaultdict(int)

    for sGUID, tGUID, amount in dmg_gen_valk(logs):
        _dmg_taken = valks_dmg_taken[tGUID]
        if _dmg_taken == -1:
            valks_overkill[sGUID] += amount
            continue

        current_dmg_taken = _dmg_taken + amount
        if current_dmg_taken < half_hp:
            valks_dmg_taken[tGUID] = current_dmg_taken
        else:
            valks_dmg_taken[tGUID] = -1
            overkill = current_dmg_taken - half_hp
            amount -= overkill
            valks_overkill[sGUID] += overkill
        valks_useful[sGUID] += amount

    return {
        'overkill': valks_overkill,
        'useful': valks_useful,
    }

# 8/31 20:12:36.834  SPELL_PERIODIC_HEAL,00808A000A6D,"Freya",0x10a48,00808A000A6D,"Freya",0x10a48,62528,"Touch of Eonar",0x1,42000,14075,0,nil
# 9/ 1 20:26:43.762  SPELL_PERIODIC_HEAL,00808A000CC3,"Freya",0x10a48,00808A000CC3,"Freya",0x10a48,62892,"Touch of Eonar",0x1,218400,143919,0,nil
def freya_useful(logs_slice: list[str]):
    FREYA = "00808A"
    DAMAGE: defaultdict[str, int] = defaultdict(int)
    healing = True
    for line in logs_slice:
        if FREYA not in line:
            continue

        if healing:
            if "SPELL_PERIODIC_HEAL" in line and line.split(',', 11)[10] == '0':
                healing = False
            continue
        
        if "DAMAGE" not in line:
            continue
        try:
            _, _, sGUID, _, tGUID, _, _, _, _, dmg, _ = line.split(',', 10)
            if tGUID[6:-6] == FREYA:
                DAMAGE[sGUID] += int(dmg)
        except ValueError:
            pass
    
    return DAMAGE

def specific_useful(logs_slice, boss_name, specs):
    data: dict[str, defaultdict[str, int]] = {}
    if boss_name == "The Lich King":
        valks_dmg = get_valks_dmg(logs_slice)
        data['008F01'] = valks_dmg['useful']
    elif boss_name == "Freya":
        data['00808A'] = freya_useful(logs_slice)
    elif boss_name == "Festergut":
        data['008F12'] = fester_useful(logs_slice, specs)
        
    return data


def test1():
    import logs_base
    report = logs_base.THE_LOGS("24-05-10--21-04--Jengo--Lordaeron")
    s, f = report.ENCOUNTER_DATA["Festergut"][-1]
    logs_slice = report.LOGS[s:f]
    players_damage = fester_useful(logs_slice)

    d = sorted(players_damage.items(), key=lambda x: x[1], reverse=True)
    for guid, value in d:
        print(f"{report.guid_to_name(guid):12} | {value:>10.0f}")

if __name__ == "__main__":
    test1()
