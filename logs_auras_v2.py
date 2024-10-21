from collections import defaultdict

import logs_base
from h_debug import running_time
from h_other import sort_dict_by_value

DEFAULT_DURATION = 60
ROOM_DURATION = 50
ROOM_AURA_ID = "74297"

SERVERS_NO_ICC_BUFF = {
    "Lordaeron",
}

AURAS_SELF = {
    "53908": 15,    # Potion of Speed
    "53909": 15,    # Potion of Wild Magic
    "28494": 15,    # Insane Strength Potion
    "28507": 15,    # Haste Potion
    "53762": 120,   # Indestructible Potion
    "28714": 60,    # Flame Cap
    "54758": 12,    # Hyperspeed Acceleration
    "26297": 10,    # Berserking
    "20572": 15,    # Blood Fury
    "72416": 10,    # Frostforged Sage
    "72412": 10,    # Frostforged Champion
    "55637": 15,    # Lightweave
    "73422": 10,    # Chaos Bane
    
    "71561": 30,    # Strength of the Taunka
    "71484": 30,    # Strength of the Taunka
    "71558": 30,    # Power of the Taunka
    "71486": 30,    # Power of the Taunka
    "71557": 30,    # Precision of the Iron Dwarves
    "71487": 30,    # Precision of the Iron Dwarves
    "71559": 30,    # Aim of the Iron Dwarves
    "71491": 30,    # Aim of the Iron Dwarves
    "71560": 30,    # Speed of the Vrykul
    "71492": 30,    # Speed of the Vrykul
    "71556": 30,    # Agility of the Vrykul 
    "71485": 30,    # Agility of the Vrykul 

    "75473": 15,    # Charred Twilight Scale
    "75466": 15,
    "71605": 20,    # Phylactery of the Nameless Lich
    "71636": 20,
    "75456": 20,    # Sharpened Twilight Scale
    "75458": 20,
    "71644": 20,    # Dislodged Foreign Object
    "71601": 20,
    "71541": 15,    # Whispering Fanged Skull
    "71401": 15,
    "67772": 15,    # Death's Choice
    "67773": 15,
    "67703": 15,
    "67708": 15,

    "64713": 10,    # Flare of the Heavens
    "71564": 20,    # Nevermelting Ice Crystal
}

AURAS_EXTERNAL = {
    "73822": 60*30, # Hellscream's Warsong
    "73828": 60*30, # Strength of Wrynn
     "2825": 40,    # Bloodlust
    "32182": 40,    # Heroism
    "57933": 10,    # Tricks of the Trade
    "10060": 15,    # Power Infusion
    "49016": 30,    # Hysteria
    "23060": 60*4,  # Battle Squawk
    "54646": 60*30, # Focus Magic
    "29166": 10,    # Innervate
    "19753": 180,   # Divine Intervention
    "72553": 100,   # Gastric Bloat
    "70227": 30,    # Empowered Blood
    "71532": 75,    # Essence of the Blood Queen
    "71533": 60,    # Essence of the Blood Queen
    "67108": 30,    # Nether Power
    "67215": 20,    # Empowered Darkness
    "67218": 20,    # Empowered Light
    "63848": 50,    # Hunger For Blood
    "51800": 60*2,  # Might of Malygos
    "51777": 60*2,  # Arcane Focus
    "51605": 60*2,  # Zeal
    "44335": 30,    # Energy Feedback
}

AURAS_BOSS_MECHANICS = {
    "71289": 12,    # Dominate Mind
    "71237": 15,    # Curse of Torpor
    "69279": 12,    # Gas Spore
    "72550": 20,    # Malleable Goo
    "73020": 6,     # Vile Gas
    "73023": 12,    # Mutated Infection
    "72838": 30,    # Volatile Ooze Adhesive
    "72833": 20,    # Gaseous Bloat
    "72856": 60,    # Unbound Plague
    "72620": 20,    # Choking Gas
    "71265": 6,     # Swarming Shadows
    "73070": 4,     # Incite Terror
    "71340": 30,    # Pact of the Darkfallen
    "69762": 30,    # Unchained Magic
    "67907": 15,    # Mistress' Kiss
    "68125": 8,     # Legion Flame
    "66283": 3,     # Spinning Pain Spike
    "74509": 3,     # Repelling Wave
    "74456": 5,     # Conflagration
    "74384": 4,     # Intimidating Roar
    "74531": 2,     # Tail Lash
    "74118": DEFAULT_DURATION,   # Ooze Variable
    "74119": DEFAULT_DURATION,   # Gas Variable
    "70157": DEFAULT_DURATION,   # Ice Tomb
    "69065": DEFAULT_DURATION,   # Impaled
    "74795": DEFAULT_DURATION,   # Mark of Consumption
    "74567": DEFAULT_DURATION,   # Mark of Combustion
    ROOM_AURA_ID: ROOM_DURATION, # Harvest Souls
}

AURAS_SPEC = {
    "47241": 36,    # Metamorphosis
    "70840": 10,    # Devious Minds
    "63167": 10,    # Decimation
    "64371": 10,    # Eradication

    "48108": 10,    # Hot Streak
    "70753": 5,     # Pushing the Limit
    "70747": 30,    # Quad Core
    
    "12292": 30,    # Death Wish
    "46916": 5,     # Slam!
    "14203": 12,    # Enrage
    "70855": 10,    # Blood Drinker
    "52437": 10,    # Sudden Death

    "51690": 2,     # Killing Spree
    "13877": 15,    # Blade Flurry
    
    "53434": 20,    # Call of the Wild
    "70728": 10,    # Exploit Weakness
    "71007": 10,    # Stinger
    "53220": 12,    # Improved Steady Shot

    "48518": 15,    # Eclipse (Lunar)
    "48517": 15,    # Eclipse (Solar)
    "70721": 6,     # Omen of Doom
    "16886": 3,     # Nature's Grace

    "50334": 15,    # Berserk
    "50213": 6,     # Tiger's Fury
    "16870": 15,    # Clearcasting

    "31884": 20,    # Avenging Wrath

    "14751": DEFAULT_DURATION,    # Inner Focus
    # "61792": 10,    # Shadowy Insight
    
    "53365": 15,    # Unholy Strength
    # "70657": 15,    # Advantage
}


MULTISPELLS = {
    # Essence of the Blood Queen
    "71533": [
        "71533", "71531", "71525", "71473",
    ],
    "71532": [
        "71532", "70867", "70879", "71530",
    ],
    # Malleable Goo
    "72550": [
        "72297", "72549", "72548", "72550",
        "70853", "72873", "72458", "72874",
    ],
    # Vile Gas
    "73020": [
        "69240", "73019", "71218", "73020",
        "72272", "72273",
        # "69244", "73173", "71288", "73174"
    ],
    # Mutated Infection
    "73023": [
        "69674", "73022", "71224", "73023",
    ],
    # Volatile Ooze Adhesive - Green Target
    "72838": [
        "70447", "72837", "72836", "72838",
    ],
    # Gaseous Bloat - Red Target
    "72833": [
        "70672", "72832", "72455", "72833",
    ],
    # Choking Gas
    "72620": [
        "71278", "72619", "72460", "72620",
        "71279", "72621", "72459", "72622",
    ],
    # Unbound Plague
    "72856": [
        "70911", "72855", "72854", "72856",
    ],
    # Legion Flame
    "68125": [
        "66197", "68124", "68123", "68125",
    ],
    # Mistress' Kiss
    "67907": [
        "66334", "67906", "67905", "67907",
    ],
    # Hellscream's Warsong
    "73822": [
        "73816", "73818", "73819", "73820", "73821", "73822",
    ],
    # Strength of Wrynn
    "73828": [
        "73762", "73824", "73825", "73826", "73827", "73828",
    ],
}
MULTISPELLS_D = {y: x for x, spells in MULTISPELLS.items() for y in spells}

ICC_BUFFS = set(MULTISPELLS["73822"]) | set(MULTISPELLS["73828"])

SPELLS = AURAS_SELF | AURAS_EXTERNAL | AURAS_BOSS_MECHANICS | AURAS_SPEC
for spell_id, spell_id_main in MULTISPELLS_D.items():
    SPELLS[spell_id] = SPELLS[spell_id_main]



class Aura:
    __slots__ = "count", "uptime"
    def __init__(self, count: int=0, uptime: float=0.0) -> None:
        self.count = count
        self.uptime = uptime

    def __str__(self):
        return ' | '.join((
            f"{self.count:>3}",
            f"{self.uptime:>6.1f}"
        ))
    
    def __add__(self, other: "Aura"):
        self.count += other.count
        self.uptime += other.uptime
        return self
    
    def __lt__(self, other: "Aura"):
        return self.uptime < other.uptime

class AuraUptimePercentage(Aura):
    pass

class AuraUptimeDuration(Aura):
    pass


class AuraLine:
    __slots__ = "timestamp", "flag"
    def __init__(self, timestamp: str, flag: str) -> None:
        self.timestamp = timestamp
        self.flag = flag


class AuraLines(list[AuraLine]):
    def calc_total_uptime(self, spell_id: str, delta_func):
        MAX_DURATION = SPELLS.get(spell_id, DEFAULT_DURATION)
        applied_timestamp = None
        aura = AuraUptimeDuration()
        for aura_line in self:
            if applied_timestamp is not None:
                _delta = delta_func(applied_timestamp, aura_line.timestamp)
                _delta = min(_delta, MAX_DURATION)
                if _delta > 0:
                    aura.count += 1
                    aura.uptime += _delta
            if aura_line.flag == "SPELL_AURA_REMOVED":
                applied_timestamp = None
            else:
                applied_timestamp = aura_line.timestamp
        return aura


class AuraLinesSources(dict[str, AuraLines]):
    def __missing__(self, key):
        v = self[key] = AuraLines()
        return v


class AuraLinesByTarget(dict[str, AuraLinesSources]):
    def __missing__(self, key):
        v = self[key] = AuraLinesSources()
        return v
    
    @running_time
    def __init__(self, logs_slice: list[str]):
        for line in logs_slice:
            if "SPELL_A" not in line:
                continue
            _line = line.split(',', 7)
            if _line[6] not in SPELLS:
                continue

            # if _line[6] == "16886":
            #     print(line)
            
            spell_id = MULTISPELLS_D.get(_line[6], _line[6])
            self[_line[4]][spell_id].append(AuraLine(*_line[:2]))
        
        self._add_missing_events(logs_slice)

    def _add_missing_events(self, logs_slice: list[str]):
        first_timestamp = logs_slice[0].split(',', 1)[0]
        last_timestamp = logs_slice[-1].split(',', 1)[0]
        AURA_APPLIED = AuraLine(first_timestamp, "SPELL_AURA_APPLIED")
        AURA_REMOVED = AuraLine(last_timestamp, "SPELL_AURA_REMOVED")
        for spells in self.values():
            for aura_timestamps in spells.values():
                if aura_timestamps[0].flag != "SPELL_AURA_APPLIED":
                    aura_timestamps.insert(0, AURA_APPLIED)
                if aura_timestamps[-1].flag != "SPELL_AURA_REMOVED":
                    aura_timestamps.append(AURA_REMOVED)

    def check_icc_buff(self):
        icc = defaultdict(int)
        for target_guid, target_data in self.items():
            for spell_id in target_data:
                if spell_id in ICC_BUFFS:
                    icc[spell_id] += 1

        if icc:
            return list(sort_dict_by_value(icc))[0]

    def room_grabs_timestamps(self):
        timestamps = set()
        for target_guid, target_data in self.items():
            for spell_id, aura_lines in target_data.items():
                if spell_id != ROOM_AURA_ID:
                    continue
                g_timestamps = (aura_line.timestamp for aura_line in aura_lines)
                timestamps.update(g_timestamps)
        return timestamps


class AuraUptimeDurationByTarget(dict[str, dict[str, AuraUptimeDuration]]):
    def __missing__(self, spell_id: str):
        v = self[spell_id] = {}
        return v
    
    # @running_time
    def __init__(self, data: AuraLinesByTarget, delta_func) -> None:
        for target_guid, target_data in data.items():
            for spell_id, aura_timestamps in target_data.items():
                if target_guid[:3] != "0x0":
                    continue
                self[target_guid][spell_id] = aura_timestamps.calc_total_uptime(spell_id, delta_func)


class AuraUptimePercentageByTarget(dict[str, dict[str, AuraUptimePercentage]]):
    def __missing__(self, spell_id: str):
        v = self[spell_id] = {}
        return v
    
    def __init__(self, data: AuraUptimeDurationByTarget, duration: float) -> None:
        for target_guid, target_data in data.items():
            for spell_id, aura in target_data.items():
                uptime_percentage = round(aura.uptime / duration * 100, 1)
                self[target_guid][spell_id] = AuraUptimePercentage(aura.count, uptime_percentage) 




class AurasUptimes(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    @running_time
    def get_auras_uptime_duration(self, s, f):
        logs_slice = self.LOGS[s:f]
        auras_lines = AuraLinesByTarget(logs_slice)
        auras_uptime = AuraUptimeDurationByTarget(auras_lines, self.get_timedelta_seconds)

        custom_auras = {}
        _room_timestamps = auras_lines.room_grabs_timestamps()
        if _room_timestamps:
            custom_auras[ROOM_AURA_ID] = self._aura_lk_room(_room_timestamps, logs_slice[-1])
        
        icc_buff = auras_lines.check_icc_buff()
        if icc_buff:
            duration = self.get_slice_duration(s, f)
            custom_auras[icc_buff] = AuraUptimeDuration(1, duration)

        for auras_on_target in auras_uptime.values():
            auras_on_target.update(custom_auras)

        return auras_uptime
    
    def get_auras_uptime_percentage(self, s, f):
        SLICE_DURATION = self.get_slice_duration(s, f)
        auras_groupped_by_target = self.get_auras_uptime_duration(s, f)
        return AuraUptimePercentageByTarget(auras_groupped_by_target, SLICE_DURATION)

    def get_auras_uptime_wrap(self, boss, attempt=-1):
        s, f = self.get_enc_data()[boss][attempt]
        return self.get_auras_uptime_duration(s, f)

    def get_auras_uptime_percentage_wrap(self, boss, attempt=-1):
        s, f = self.get_enc_data()[boss][attempt]
        return self.get_auras_uptime_percentage(s, f)

    def _aura_lk_room(self, _room_timestamps: set[str], last_line: str):
        room_aura = AuraUptimeDuration(count=1)
        
        room_timestamps = sorted(_room_timestamps)
        for x, y in zip(room_timestamps, room_timestamps[1:]):
            if self.get_timedelta_seconds(x, y) > 60:
                room_aura.count += 1
                room_aura.uptime += ROOM_DURATION
        
        last_grab = room_timestamps[-1]
        gap_after_last_room_grab = self.get_timedelta_seconds(last_grab, last_line)
        room_aura.uptime += min(gap_after_last_room_grab, ROOM_DURATION)
        if gap_after_last_room_grab < 10:
            room_aura.count -= 1
        
        return room_aura
    
    def _pretty_print(self, d, guid_filter=None, spell_id_filter=None):
        print('='*100)
        for target_guid, spells in d.items():
            if guid_filter and target_guid != guid_filter:
                continue
            spells = sort_dict_by_value(spells)
            for spell_id, q in spells.items():
                if spell_id_filter and spell_id != spell_id_filter:
                    continue
                try:
                    spell_name = self.SPELLS[int(spell_id)].name
                except KeyError:
                    spell_name = spell_id
                print(f"{self.guid_to_name(target_guid):12} | {spell_id:>5} | {q} | {spell_name}")
    

    
def test1():
    report = AurasUptimes("24-03-01--21-02--Meownya--Lordaeron")
    report.LOGS
    # q = report.get_auras_uptime_wrap("The Lich King", -2)
    # q = report.get_auras_uptime_wrap("Deathbringer Saurfang", -1)
    # for _ in range(10):
    q = report.get_auras_uptime_wrap("Blood-Queen Lana'thel", -1)
        # q = report.get_auras_uptime_percentage_wrap("Blood-Queen Lana'thel", -1)
    report._pretty_print(q, guid_filter="0x06000000004544FD")
    q = report.get_auras_uptime_wrap("The Lich King", -2)
    report._pretty_print(q, guid_filter="0x06000000004544FD")

def test2():
    report = AurasUptimes("24-06-16--20-36--Saforafire--Icecrown")
    report.LOGS
    q = report.get_auras_uptime_wrap("The Lich King", -2)
    report._pretty_print(q, guid_filter="0x07000000009766B7")

def test3():
    report = AurasUptimes("24-09-04--19-22--Фуфыкс--WoW-Circle")
    report.LOGS
    print(report.PLAYERS_NAMES)
    q = report.get_auras_uptime_wrap("The Lich King", -2)
    report._pretty_print(q, guid_filter="0x000000000193F1FA")
    
    
def test4():
    report = AurasUptimes("24-09-04--19-01--Какойтопарен--WoW-Circle")
    report.LOGS
    # print(report.PLAYERS_NAMES)
    # pc = perf_counter()
    # print("="*100)
    q = report.get_auras_uptime_wrap("The Lich King", -2)
    # report._pretty_print(q, guid_filter="0x000000000191C4A9")

    # q = report.get_auras_uptime_percentage_wrap("The Lich King", -2)
    # report._pretty_print(q, guid_filter="0x000000000191C4A9")
    # print(f'{(perf_counter() - pc)*1000:>10,.3f}ms | Done')
    
    # input()
    
    
    # report.get_uptime_wrap("Rotface", -1)
    # q = report.get_uptime_wrap("Festergut", -1)
    # report.preprint(q, spell_id="75473")
    # report._pretty_print(q, guid_filter="0x06000000004544FD")
    # report.preprint(q, target_guid="0x0700000000830A43")
    # report.preprint(q, "53908")



if __name__ == "__main__":
    test4()
