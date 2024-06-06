from collections import defaultdict

from constants import BOSSES_GUIDS, MULTIBOSSES, T_DELTA, convert_to_fight_name, running_time, get_delta

MAX_LINES = 1000
MULTIBOSSES_MAIN = {
    guid: boss_guids[0]
    for boss_guids in MULTIBOSSES.values()
    for guid in boss_guids
}
BOSSES_GUIDS_ALL = set(BOSSES_GUIDS) | set(MULTIBOSSES_MAIN)
FLAGS = {
    "UNIT_DIED",
    "SWING_DAMAGE",
    "SPELL_DAMAGE",
    "RANGE_DAMAGE",
    "DAMAGE_SHIELD",
    "SPELL_HEAL",
    "SPELL_AURA_APPLIED",
    "SPELL_AURA_REMOVED",
}
SPELL_AURA = {
    "SPELL_AURA_APPLIED",
    "SPELL_AURA_REMOVED",
}
IGNORED_SPELL_IDS = {
    "2096", "10909", "45468", # Mind Vision
    "26995", # Soothe Animal
    "56190", "56191", "55346", # Lens
    "60122", # Baby Spice
    "53338", "1130", "14323", "14324", "14325", "19421", "19422", "19423", # Hunter"s Mark
    # "70861", # Sindragosa"s Lair Teleport
    # "72550", # Malleable Goo
    # "72273", # Vile Gas
    "72371", # Blood Power
    # "70952", # Invocation of Blood
    # "72443", # Boiling Blood
    # "72410", # Rune of Blood
    # "72905", "72907", "72906", "72908", # Frostbolt Volley
    # "70842", # Mana Barrier
    # "70109", # Permeating Chill
    # Surge of Darkness
    # Surge of Light
}
BOSS_MAX_SEP = {
    "008FF5": T_DELTA["30SEC"],
    "009BB7": T_DELTA["2MIN"],
    "008704": T_DELTA["2MIN"],
    "008EF5": T_DELTA["2MIN"],
}
HEAL_BOSSES = {
    "008FB5",
}
FINISH_SPELLS = {
    "72350",
}
CAN_BE_SMALL = {
    "Heroic Training Dummy",
    "Highlord's Nemesis Trainer",
}

def to_int(timestamp: str):
    i = timestamp.index('.')
    return int(timestamp[i-8:i].replace(':', ''))

def time_pairs(boss_id, lines):
    MAX_SEP = BOSS_MAX_SEP.get(boss_id, T_DELTA["1MIN"])
    SEGMENTS = []
    CURRENT_LINES = []
    last_timestamp = lines[0][1]
    last_time = to_int(last_timestamp)

    for line in lines:
        new_timestamp = line[1]
        
        now = to_int(new_timestamp)
        if now - last_time > 60 or last_time > now:
            td = get_delta(new_timestamp, last_timestamp)
            if td > MAX_SEP:
                SEGMENTS.append(CURRENT_LINES)
                CURRENT_LINES = []
        
        last_time = now
        last_timestamp = new_timestamp
        CURRENT_LINES.append(line)

    SEGMENTS.append(CURRENT_LINES)
    return SEGMENTS

def get_overkill(etc: str):
    try:
        _, _, dmg, ok, _ = etc.split(",", 4)
        if ok == "0":
            return 0
        return int(dmg) - int(ok)
    except ValueError:
        return 0
    
def get_more_precise_start(lines: list[tuple[int, list[str]]]):
    # print('++++ get_more_precise_start')
    index = 0
    for index, line in enumerate(lines):
        # print(line)
        if line[-1][-5:] != ",BUFF":
            break
    
    return index
    
def get_more_precise_end(lines: list[tuple[int, list[str]]]):
    # print('++++ get_more_precise_end')
    index = 0
    _damaged = 0
    for i, line in enumerate(reversed(lines)):
        if i > MAX_LINES or _damaged > 20:
            # print(">>>>>>> break", i, _damaged)
            break
        if line[2] in SPELL_AURA:
            continue
        if line[2] == "UNIT_DIED" and index < 10:
            # print(line)
            index = i
            continue

        overkill = get_overkill(line[-1])
        if overkill == 0:
            _damaged += 1
        elif overkill > 2:
            # print(line)
            index = i
            break
    
    return -index

def get_more_precise_wrap(lines: list[tuple[int, list[str]]]):
    # print("==== GET MORE PRECISE START", "="*50)
    # print(lines[0])
    # print(lines[-1])
    index_start = get_more_precise_start(lines)
    index_end = get_more_precise_end(lines)
    # print("==== GET MORE PRECISE AFTER", "="*50)
    # print('....... index_start', index_start)
    # print('....... index_end', index_end)
    # print(lines[index_start])
    # print(lines[index_end and index_end - 1 or -1])
    if index_start:
        if index_end:
            return lines[index_start:index_end]
        return lines[index_start:]
    elif index_end:
        return lines[:index_end]
    return lines

def refine_lk(segments: list[list]):
    attempts_to_replace = []
    for attempt, segment in enumerate(segments):
        fofs = [line for line in segment if "72350" in line]
        if not fofs:
            continue
        first = fofs[0]
        last = fofs[-1]
        segment1 = segment[:segment.index(first)+1]
        segment2 = segment[segment.index(last):]
        _split = [segment1, segment2]
        attempts_to_replace.append((attempt, _split))

    for attempt, _split in reversed(attempts_to_replace):
        segments[attempt:attempt+1] = _split


class Fights:
    def __init__(self, logs: list[str]) -> None:
        self.logs = logs
    
    def main(self):
        self.filtered_bosses = self.dump_all_boss_lines()
        return self.filter_bosses()

    @running_time
    def dump_all_boss_lines(self):
        NIL = "nil"
        BOSSES: defaultdict[str, list[tuple[int, str, str, str, str, str, str]]] = defaultdict(list)
        
        for n, line in enumerate(self.logs):
            if 'xF' not in line:
                continue
            
            ts, flag, etc = line.split(',', 2)
            if flag not in FLAGS:
                continue
            
            if flag == "UNIT_DIED":
                sGUID, _, tGUID, _ = etc.split(',', 3)
                _guid = tGUID[6:-6]
                if _guid not in BOSSES_GUIDS_ALL:
                    continue
                spell_id, other = NIL, NIL
            else:
                sGUID, _, tGUID, _, spell_id, other = etc.split(',', 5)
                if spell_id in IGNORED_SPELL_IDS:
                    continue
                
                _guid = tGUID[6:-6]
                if _guid not in BOSSES_GUIDS_ALL:
                    if spell_id not in FINISH_SPELLS:
                        continue
                    _guid = sGUID[6:-6]
            
            _guid = MULTIBOSSES_MAIN.get(_guid, _guid)
            BOSSES[_guid].append((n, ts, flag, sGUID, tGUID, spell_id, other))

        return BOSSES
    
    @running_time
    def filter_bosses(self):
        BOSS_SEGMENTS: dict[str, list[tuple[int, int]]] = {}
        
        for boss_id, dumped_lines in self.filtered_bosses.items():
            # print()
            # print("="*100)
            # print(boss_id, BOSSES_GUIDS[boss_id], len(dumped_lines))
            if len(dumped_lines) < 100:
                continue
            
            fight_name = convert_to_fight_name(boss_id)
            # print(fight_name)
            if fight_name is None:
                continue
            
            new_segments = []
            for segment in time_pairs(boss_id, dumped_lines):
                # print("\n////////////// NEW SEGMENT", len(segment))

                if len(segment) < 100 and fight_name not in CAN_BE_SMALL:
                    continue
                
                segment = get_more_precise_wrap(segment)
                new_segments.append(segment)
                # pretty_print(boss_id, segment)
            
            if not new_segments:
                continue

            if boss_id == "008EF5":
                # print()
                # print("="*100)
                # print(boss_id, BOSSES_GUIDS[boss_id], len(dumped_lines))
                # print("\n:::::::::::::::::::: LICH KING SHIT", len(segment))

                # print(len(segments))
                
                refine_lk(new_segments)
                # print(len(segments))

                # for segment in segments:
                #     print("\n////////////// NEW SEGMENT", len(segment))
                #     pretty_print(boss_id, segment)
            
            BOSS_SEGMENTS[fight_name] = [
                [segment[0][0], segment[-1][0] + 1]
                for segment in new_segments
            ]
        
        return BOSS_SEGMENTS


def pretty_print(boss_id, dumped_lines):
    print("==== PRETTY PRINT", "="*50)
    for i in range(5):
        print(dumped_lines[i])
    if boss_id in {"008FF5", "0086C0", "008FB5", "009443", "009454", "008F46", "00869D"}:
        for i in range(5, 20):
            print(dumped_lines[i])
    print()
    # a = (line for line in reversed(lines) if "SPELL_AURA_REMOVED" not in line)
    a = reversed(dumped_lines)
    for _ in range(66):
        print(next(a))
    if boss_id in {"008EF5"}:
        print()
        a = (line for line in reversed(dumped_lines) if "72350" in line)
        for i in a:
            print(i)
