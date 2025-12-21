import logs_core
from c_bosses import (
    BOSSES_GUIDS,
    COWARDS,
    MULTIBOSSES,
    convert_to_fight_name,
)
from c_path import FileNames
from h_debug import running_time
from h_datetime import (
    T_DELTA,
    to_dt_year,
)

MAX_LINES_DEFAULT = 1000
MAX_LINES_BY_BOSS = {
    "004630": 10000, # Archimonde
    "0061CE": 10000, # Felmyst
}
MULTIBOSSES_MAIN = {
    guid: list(boss_guids)[0]
    for boss_guids in MULTIBOSSES.values()
    for guid in boss_guids
}
BOSSES_GUIDS_ALL = set(BOSSES_GUIDS) | set(MULTIBOSSES_MAIN)
FLAGS = {
    "UNIT_DIED",
    "SWING_DAMAGE",
    "SPELL_DAMAGE",
    "SPELL_PERIODIC_DAMAGE",
    "RANGE_DAMAGE",
    "DAMAGE_SHIELD",
    "SPELL_HEAL",
    "SPELL_PERIODIC_HEAL",
    "SPELL_AURA_APPLIED",
    "SPELL_AURA_REMOVED",
}
FLAGS_HEAL = {
    "SPELL_HEAL",
    "SPELL_PERIODIC_HEAL",
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
BOSS_MAX_IDLE_TIME_IN_FIGHT_DEFAULT = T_DELTA["30SEC"]
BOSS_MAX_IDLE_TIME_IN_FIGHT = {
    # "008FF5": T_DELTA["30SEC"],
    "009BB7": T_DELTA["2MIN"], # Halion
    "008704": T_DELTA["2MIN"], # Anub'arak
    # "008EF5": T_DELTA["1MIN"],
    "008EF5": T_DELTA["2MIN"], # The Lich King
    "008246": T_DELTA["1MIN"], # Mimiron
    "008208": T_DELTA["1MIN"], # Yogg-Saron
    
    "061A96": T_DELTA["2MIN"], # Illidan Stormrage
    "061A98": T_DELTA["2MIN"], # Shade of Aran
    "061A99": T_DELTA["2MIN"], # Ysondre
    "061AB1": T_DELTA["2MIN"], # Ragnaros
    "061AB3": T_DELTA["2MIN"], # Void Reaver
    "061AB4": T_DELTA["2MIN"], # Azuregos

    "004CA6": T_DELTA["1MIN"], # Kael'thas Sunstrider
    "005B7A": T_DELTA["1MIN"], # Reliquary of Souls

    "0061CE": T_DELTA["1MIN"], # Felmyst
    "006132": T_DELTA["15SEC"], # Brutallus
}
HEAL_BOSSES = {
    "008FB5",
}
SOME_BOSS_SPELLS = {
    "72350", # Fury of Frostmourne
    "70157", # Ice Tomb
}
CAN_BE_SHORT = {
    "007F23": "Highlord's Nemesis Trainer",
    "0079AA": "Heroic Training Dummy",
}


def to_int(timestamp: str):
    i = timestamp.index('.')
    return int(timestamp[i-8:i].replace(':', ''))


class LogLine(tuple[int, str, str, str, str, str, str]):
    pass

class BossSegment(list[LogLine]):
    def __init__(self, boss_id: str):
        self.boss_id = boss_id
        super().__init__()

    def start_end_index(self):
        return [self[0][0], self[-1][0] + 1]

    def get_more_precise_wrap(self):
        # print("===== BossSegment.get_more_precise_wrap")
        # print(self[0])
        # print(self[-1])

        index_start = self.get_more_precise_start()
        index_end = self.get_more_precise_end()

        if index_end:
            for _ in range(index_end):
                self.pop()
        
        if index_start:
            for _ in range(index_start):
                self.pop(0)

        # print(f'... new range [{index_start}:{-index_end}]')
        # print(self[0])
        # print(self[-1])
        
        return self

    def get_more_precise_start(self):
        # print('++++ get_more_precise_start')
        index = 0
        for index, line in enumerate(self):
            # print(line)
            if line[-1][-5:] != ",BUFF":
                break
        
        return index

    def get_more_precise_end(self):
        # print('++++ get_more_precise_end')
        new_fight_end_line_index = 0
        boss_died = False
        damaged_times = -20
        removed_auras = 0
        first_removed_aura_line_index = 0
        max_lines = MAX_LINES_BY_BOSS.get(self.boss_id, MAX_LINES_DEFAULT)
        lines = self[-max_lines:]
        for line_index, line in enumerate(reversed(lines)):
            # print(f">>> {line_index:>5} | {line}")
            
            if line[2] in FLAGS_HEAL and line[4][6:-6] not in HEAL_BOSSES:
                continue
            if line[4][6:-6] not in BOSSES_GUIDS:
                continue
            
            if line[2] in SPELL_AURA:
                if boss_died:
                    continue
                if self.boss_id not in COWARDS:
                    continue
                if line[2] != "SPELL_AURA_REMOVED":
                    continue
                if not removed_auras:
                    first_removed_aura_line_index = line_index
                removed_auras += 1
                if removed_auras < 15:
                    continue
                
                new_fight_end_line_index = first_removed_aura_line_index
                # print(f">>> new_fight_end_line_index {new_fight_end_line_index:>4} | get_more_precise_end removed > 15")
                break
            
            removed_auras = 0
            if line[2] == "UNIT_DIED":
                if boss_died:
                    continue
                if line_index > 30:
                    continue
                new_fight_end_line_index = line_index
                # print(f">>> new_fight_end_line_index {new_fight_end_line_index:>4} | line[2] == UNIT_DIED")
                damaged_times = 0
                boss_died = True
                continue
            
            try:
                _, _, value, overkill, _ = line[-1].split(",", 4)
            except ValueError: # not enough values to unpack
                continue
            
            if overkill == "0":
                # print(f">>>>> damaged {damaged_times:5} | overkill == 0")
                damaged_times += 1
                if damaged_times > 5:
                    break
                continue

            try:
                value_no_overkill = int(value) - int(overkill)
            except ValueError: # invalid literal for int
                continue
            
            damaged_times = 0
            # print(f">>> {line_index:>5} | {value_no_overkill} value_no_overkill")
            if value_no_overkill == 1:
                continue
            
            new_fight_end_line_index = line_index
            # print(f">>> new_fight_end_line_index {new_fight_end_line_index:>4} | value_no_overkill != 1")
            
        return new_fight_end_line_index


class BossLines(list[LogLine]):
    def __init__(self, boss_id: str, year: int):
        self.boss_id = boss_id
        self.year = year
        self.fight_name = convert_to_fight_name(boss_id)
        super().__init__()

    def get_timedelta(self, now: str, before: str):
        return to_dt_year(now, self.year) - to_dt_year(before, self.year)

    def split_to_segments(self):
        segments = [
            segment.get_more_precise_wrap()
            for segment in self._split_to_pulls()
            if len(segment) > 100 or self.boss_id in CAN_BE_SHORT
        ]
        
        if self.boss_id == "008EF5":
            self.refine_lk(segments)

        return [
            segment.start_end_index()
            for segment in segments
        ]
    
    @staticmethod
    def refine_lk(segments: list[BossSegment]):
        for attempt, segment in reversed(list(enumerate(segments))):
            fofs = [
                i
                for (i, line) in enumerate(segment)
                if "72350" in line
            ]
            if not fofs:
                continue

            index_first_fof = fofs[0]
            index_last_fof = fofs[-1]
            # print("\n> fofs:")
            # print(index_first_fof, segment[index_first_fof])
            # print(index_last_fof, segment[index_last_fof])
            segment_before_fof = BossSegment(segment.boss_id)
            segment_before_fof.extend(segment[:index_first_fof+1])
            segments[attempt] = segment_before_fof

            segment_after_fof = BossSegment(segment.boss_id)
            segment_after_fof.extend(segment[index_last_fof:])
            segments.insert(attempt+1, segment_after_fof)
    
    def _new_boss_segment(self):
        return BossSegment(self.boss_id)

    def _split_to_pulls(self):
        MAX_IDLE_TIME = BOSS_MAX_IDLE_TIME_IN_FIGHT.get(self.boss_id, BOSS_MAX_IDLE_TIME_IN_FIGHT_DEFAULT)
        boss_segment = self._new_boss_segment()
        last_timestamp = self[0][1]
        last_time = to_int(last_timestamp)

        for line in self:
            new_timestamp = line[1]
            
            now = to_int(new_timestamp)
            if now - last_time > 20 or last_time > now:
                td = self.get_timedelta(new_timestamp, last_timestamp)
                # print()
                # print(td, td > MAX_IDLE_TIME)
                # print(f"{last_time:06} > {now:06}")
                # print("/// S:", boss_segment[0])
                # print("/// E:", boss_segment[-1])
                # print(">>> N:", line)
                if td > MAX_IDLE_TIME:
                    yield boss_segment
                    boss_segment = self._new_boss_segment()
            
            last_time = now
            last_timestamp = new_timestamp
            boss_segment.append(line)

        yield boss_segment

class BossLinesGroupped(dict[str, BossLines]):
    def __init__(self, year: int):
        self.year = year
        return
    
    def __missing__(self, key):
        v = self[key] = BossLines(boss_id=key, year=self.year)
        return v

    def segments_dict(self):
        return dict(self.split_boss_lines_to_pulls())

    def split_boss_lines_to_pulls(self):
        for boss_id, dumped_lines in self.items():
            # DONT FORGET TO COMMENT THIS OUT
            # if dumped_lines.boss_id != "009BB7": continue # halion
            # if dumped_lines.boss_id != "0093B5": continue # dbs
            # if dumped_lines.boss_id != "005985": continue # Illidan
            # if dumped_lines.boss_id != "004630": continue # Archimonde
            if len(dumped_lines) < 100 and dumped_lines.boss_id not in CAN_BE_SHORT:
                continue
            
            if dumped_lines.fight_name is None:
                continue
            
            # print("\n> split_boss_lines_to_pulls |", dumped_lines.fight_name)
            segments = dumped_lines.split_to_segments()
            if not segments:
                continue

            yield dumped_lines.fight_name, segments


class Fights(logs_core.Logs):
    @property
    def ENCOUNTER_DATA(self):
        try:
            return self.__ENCOUNTER_DATA
        except AttributeError:
            pass
        self.__ENCOUNTER_DATA = self._get_enc_data()
        return self.__ENCOUNTER_DATA
        
    @property
    def encounter_data_path(self):
        return self.relative_path(FileNames.logs_encounter_data)

    def _get_enc_data(self):
        try:
            return self._read_enc_data()
        except Exception:
            return self._redo_enc_data()

    def _read_enc_data(self) -> dict[str, list[list[int]]]:
        return self.encounter_data_path.json()

    def _redo_enc_data(self):
        enc_data = self._make_enc_data()
        self.encounter_data_path.json_write(enc_data)
        return enc_data

    def _make_enc_data(self):
        groupped_boss_lines = self._dump_all_boss_lines()
        return groupped_boss_lines.segments_dict()

    @running_time
    def _dump_all_boss_lines(self):
        NIL = "nil"
        BOSSES = BossLinesGroupped(year=self.year)
        
        for line_index, line in enumerate(self.LOGS):
            if 'xF' not in line:
                continue
            
            timestamp, flag, etc = line.split(',', 2)
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
            BOSSES[guid_id].append((line_index, timestamp, flag, sGUID, tGUID, spell_id, other))

        return BOSSES


#####################################

def print_segment(report: Fights, segment_new, segment_old):
    start = report.LOGS[segment_old[0]]
    try:
        end = report.LOGS[segment_old[1]-1]
    except IndexError:
        end = report.LOGS[-1]
    
    print("OLD", segment_old)
    print(start)
    print(end)

    start = report.LOGS[segment_new[0]]
    try:
        end = report.LOGS[segment_new[1]-1]
    except IndexError:
        end = report.LOGS[-1]
    
    print("NEW", segment_new)
    print(start)
    print(end)

def print_differences(report: Fights, enc_data, enc_data_old):
    print("\n\n")
    print("="*50)
    if enc_data == enc_data_old:
        print(">>>>> enc_data == enc_data_old")
        return
    print(">>>>> enc_data != enc_data_old")
    # print(enc_data)
    # print(enc_data_old)
    for enc_name in enc_data_old:
        segments_old = enc_data_old[enc_name]
        segments = enc_data[enc_name]
        if segments_old == segments:
            continue
        print()
        print(len(report.LOGS))
        print(enc_name)
        print(segments_old)
        print(segments)

        for i, (segment_new, segment_old) in enumerate(zip(segments, segments_old), 1):
            if segment_new == segment_old:
                continue
    
            print()
            print(i)
            print_segment(report, segment_new, segment_old)
        

def test1():
    report_id = "24-08-27--22-00--Blokhastiq--Lordaeron"
    report_id = "24-10-02--21-25--Gattamorta--Icecrown"
    report_id = "24-12-04--19-37--Zralog--Onyxia"
    report_id = "24-12-18--19-23--Zralog--Onyxia"
    report_id = "25-01-30--21-44--Nikrozja--Icecrown"
    report_id = "25-02-24--20-26--Chickenjuice--Whitemane-Frostmourne"
    report_id = "25-02-11--19-23--Homoskup--Icecrown"
    report_id = "25-01-10--21-01--Meownya--Lordaeron"
    report_id = "25-02-26--19-59--Elementherr--Rising-Gods"
    report_id = "24-07-20--20-21--Atilicious--Rising-Gods"
    report_id = "25-03-01--18-46--Fede--Icecrown"
    report_id = "25-03-14--23-41--Mesugaki--Onyxia"
    report_id = "25-03-06--20-34--Harybolseq--Onyxia"
    report_id = "25-03-14--23-41--Mesugaki--Onyxia"
    report_id = "25-03-13--19-45--Keppzor--Onyxia"
    report_id = "25-03-04--19-49--Easygoplay--Onyxia"
    report_id = "25-02-27--20-28--Sewagewater--Onyxia"
    report_id = "25-03-27--20-59--Penetrationx--Onyxia"
    report_id = "25-05-26--20-09--Flamed--Onyxia"
    report_id = "25-05-16--23-05--Notvikk--Icecrown"
    report_id = "25-05-24--15-59--Kadaj--Onyxia"
    report_id = "25-06-01--08-44--Ovenmt--Onyxia"
    report_id = "25-06-05--22-54--Neth--Onyxia"
    report_id = "25-06-08--19-46--Meno--Onyxia"
    report_id = "24-02-29--22-55--Napfelsiine--Rising-Gods"
    report = Fights(report_id)
    report.LOGS
    report._redo_enc_data()
    # enc_data = report._make_enc_data()
    # enc_data_old = report._read_enc_data()
    # print_differences(report, enc_data, enc_data_old)
    # LICH_KING = "The Lich King"
    # print(enc_data[LICH_KING])
    # print(enc_data_old[LICH_KING])

def main():
    test1()

if __name__ == "__main__":
    main()
