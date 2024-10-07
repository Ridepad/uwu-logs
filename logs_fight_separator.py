from collections import defaultdict

import logs_core
from c_bosses import (
    BOSSES_GUIDS,
    COWARDS,
    MULTIBOSSES,
    convert_to_fight_name,
)
from h_debug import running_time
from h_datetime import (
    T_DELTA,
    get_delta,
)

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
    "1543", "28822", "55798", # Flare
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
    # "008FF5": T_DELTA["30SEC"],
    "008EF5": T_DELTA["1MIN"],
    "009BB7": T_DELTA["2MIN"],
    "008704": T_DELTA["2MIN"],
    "008EF5": T_DELTA["2MIN"],
    "008246": T_DELTA["1MIN"],
    "008208": T_DELTA["1MIN"],
}
HEAL_BOSSES = {
    "008FB5",
}
SOME_BOSS_SPELLS = {
    "72350", # Fury of Frostmourne
    "70157", # Ice Tomb
}
CAN_BE_SMALL = {
    "Heroic Training Dummy",
    "Highlord's Nemesis Trainer",
}


class LogLine(tuple[int, str, str, str, str, str, str]):
    pass

class BossLines(list[LogLine]):
    pass

def to_int(timestamp: str):
    i = timestamp.index('.')
    return int(timestamp[i-8:i].replace(':', ''))

def split_to_pulls(boss_id: str, lines: BossLines):
    # MAX_SEP = BOSS_MAX_SEP.get(boss_id, T_DELTA["1MIN"])
    MAX_SEP = BOSS_MAX_SEP.get(boss_id, T_DELTA["30SEC"])
    CURRENT_LINES = BossLines()
    last_timestamp = lines[0][1]
    last_time = to_int(last_timestamp)

    # print()
    # print("="*150)
    # boss = convert_to_fight_name(boss_id)
    # print(boss)

    for line in lines:
        new_timestamp = line[1]
        
        now = to_int(new_timestamp)
        if now - last_time > 60 or last_time > now:
            td = get_delta(new_timestamp, last_timestamp)
            # print()
            # print(td, td > MAX_SEP)
            # print(f"{last_time:06} > {now:06}")
            # print("/// S:", CURRENT_LINES[0])
            # print("/// E:", CURRENT_LINES[-1])
            # print(">>> N:", line)
            if td > MAX_SEP:
                yield CURRENT_LINES
                CURRENT_LINES = BossLines()
        
        last_time = now
        last_timestamp = new_timestamp
        CURRENT_LINES.append(line)

    yield CURRENT_LINES

def get_overkill(etc: str):
    try:
        _, _, dmg, ok, _ = etc.split(",", 4)
        if ok == "0":
            return 0
        return int(dmg) - int(ok)
    except ValueError:
        return 0
    
def get_more_precise_start(lines: BossLines):
    # print('++++ get_more_precise_start')
    index = 0
    for index, line in enumerate(lines):
        # print(line)
        if line[-1][-5:] != ",BUFF":
            break
    
    return index

def get_more_precise_end(lines: BossLines):
    # print('++++ get_more_precise_end')
    index = 0
    damaged = 0
    removed = 0
    first_removed_index = 0
    for i, line in enumerate(reversed(lines)):
        if i > MAX_LINES:
            # print(f">>> get_more_precise_end i > MAX_LINES\n{line}")
            break
        
        if line[2] in SPELL_AURA:
            if line[2] == "SPELL_AURA_REMOVED" and line[4][6:-6] in COWARDS:
                removed += 1
                if not first_removed_index:
                    first_removed_index = -i
                if removed > 15:
                    # print(f">>> get_more_precise_end removed > 15\n{line}")
                    return first_removed_index
            continue
        
        removed = 0
        first_removed_index = 0
        if line[2] == "UNIT_DIED" and index < 10:
            # print(f">>> get_more_precise_end UNIT_DIED\n{line}")
            index = i
            continue

        overkill = get_overkill(line[-1])
        if overkill == 0:
            damaged += 1
            if damaged > 20:
                # print(">>> get_more_precise_end _damaged > 20")
                break
        elif overkill > 2:
            if line[2] == "SPELL_HEAL" and line[4][6:-6] not in HEAL_BOSSES:
                continue
            # print(f">>> get_more_precise_end overkill > 2\n{line}")
            index = i
            break
    
    return -index

# def get_more_precise_wrap(lines: BossLines, bossname='?'):
def get_more_precise_wrap(lines: BossLines):
    # print("==== GET MORE PRECISE START", "="*50)
    # print(lines[0])
    # print(lines[-1])
    # print()
    # print(bossname)
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

def refine_lk(segments: list[BossLines]):
    # print(segments)
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

@running_time
def split_boss_lines_to_pulls(groupped_boss_lines: dict[str, BossLines]):
    for boss_id, dumped_lines in groupped_boss_lines.items():
        if len(dumped_lines) < 100:
            continue
        
        fight_name = convert_to_fight_name(boss_id)
        if fight_name is None:
            continue
        
        new_segments = [
            # get_more_precise_wrap(segment, fight_name)
            get_more_precise_wrap(segment)
            for segment in split_to_pulls(boss_id, dumped_lines)
            if len(segment) > 100 or fight_name in CAN_BE_SMALL
        ]

        if not new_segments:
            continue

        if boss_id == "008EF5":
            refine_lk(new_segments)

        start_end = [
            [segment[0][0], segment[-1][0] + 1]
            for segment in new_segments
        ]
        yield fight_name, start_end


class Fights(logs_core.Logs):
    @property
    def ENCOUNTER_DATA(self):
        try:
            return self.__ENCOUNTER_DATA
        except AttributeError:
            pass
        self.__ENCOUNTER_DATA = self._get_enc_data()
        return self.__ENCOUNTER_DATA

    def _get_enc_data(self):
        try:
            return self._read_enc_data()
        except Exception:
            return self._redo_enc_data()
    
    def _read_enc_data(self) -> dict[str, list[list[int]]]:
        return self.relative_path("ENCOUNTER_DATA.json").json()

    def _redo_enc_data(self):
        groupped_boss_lines = self._dump_all_boss_lines()
        enc_data = dict(split_boss_lines_to_pulls(groupped_boss_lines))
        enc_data_file_name = self.relative_path("ENCOUNTER_DATA.json")
        enc_data_file_name.json_write(enc_data)
        return enc_data

    @running_time
    def _dump_all_boss_lines(self):
        NIL = "nil"
        BOSSES: defaultdict[str, BossLines] = defaultdict(BossLines)
        
        for n, line in enumerate(self.LOGS):
            if 'xF' not in line:
                continue
            
            ts, flag, etc = line.split(',', 2)
            if flag not in FLAGS:
                continue
            
            if flag == "UNIT_DIED":
                sGUID, _, tGUID, _ = etc.split(',', 3)
                guid_id = tGUID[6:-6]
                if guid_id not in BOSSES_GUIDS_ALL:
                    continue
                spell_id, other = NIL, NIL
            else:
                sGUID, _, tGUID, _, spell_id, other = etc.split(',', 5)
                if spell_id in IGNORED_SPELL_IDS:
                    continue
                
                guid_id = tGUID[6:-6]
                if guid_id not in BOSSES_GUIDS_ALL:
                    if spell_id not in SOME_BOSS_SPELLS:
                        continue
                    guid_id = sGUID[6:-6]
            
            guid_id = MULTIBOSSES_MAIN.get(guid_id, guid_id)
            BOSSES[guid_id].append((n, ts, flag, sGUID, tGUID, spell_id, other))

        return BOSSES


#####################################

from time import perf_counter

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

def t1(logs):
    pc = perf_counter()
    fights = Fights(logs)._dump_all_boss_lines()
    print(f'{(perf_counter() - pc)*1000:>10,.3f}ms | Fights(logs).dump_all_boss_lines')
    return fights

def t3():
    fights = Fights("24-05-14--21-17--Meownya--Lordaeron")._get_enc_data()
    print(fights)

def _test_uld():
    import logs_base
    report = logs_base.THE_LOGS("24-08-27--22-00--Blokhastiq--Lordaeron")
    groupped_boss_lines = report._dump_all_boss_lines()

    BOSS_GUID = "008063"
    lines = groupped_boss_lines[BOSS_GUID]
    for x in lines[:20]:
        print(x)
    print('='*111)
    for x in lines[-30:]:
        print(x)
    
    q = {
        BOSS_GUID: groupped_boss_lines[BOSS_GUID]
    }
    z = split_boss_lines_to_pulls(q)
    for name, ss in z:
        print(name)
        print(ss)

def test1():
    report = Fights("24-10-02--21-25--Gattamorta--Icecrown")
    report.LOGS
    report._redo_enc_data()

def main():
    test1()
    # _test_uld()


if __name__ == "__main__":
    main()
