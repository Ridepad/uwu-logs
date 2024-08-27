from collections import defaultdict
import collections

import logs_base
from h_debug import running_time


DEATH_FLAGS = {"UNIT_DIED", "SPELL_INSTAKILL"}
HEAL_FLAGS = {"SPELL_HEAL", "SPELL_PERIODIC_HEAL"}

FLAGS_DMG = {"SWING_DAMAGE", "SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE", "RANGE_DAMAGE", "DAMAGE_SHIELD", "ENVIRONMENTAL_DAMAGE"}
FLAGS_MISS = {"SWING_MISSED", "SPELL_MISSED", "SPELL_PERIODIC_MISSED", "RANGE_MISSED", "DAMAGE_SHIELD_MISSED"}
FLAGS_OFFENSIVE = FLAGS_DMG | FLAGS_MISS
AURA_FLAGS = {"SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_REMOVED", "SPELL_AURA_APPLIED_DOSE", "SPELL_AURA_REMOVED_DOSE"}
FLAGS_CUT = {
    "SWING_DAMAGE": ("DAMAGE", "SWING"),
    "SPELL_DAMAGE": ("DAMAGE", "SPELL"),
    "RANGE_DAMAGE": ("DAMAGE", "RANGE"),
    "SPELL_PERIODIC_DAMAGE": ("DAMAGE", "DOT"),
    "DAMAGE_SHIELD": ("DAMAGE", "SHIELD"),
    "ENVIRONMENTAL_DAMAGE": ("DAMAGE", "ENVIRONMENT"),
    "SPELL_HEAL": ("HEAL", "HEAL"),
    "SPELL_PERIODIC_HEAL": ("HEAL", "HOT"),
    "SPELL_AURA_APPLIED": ("AURA", "APPLIED"),
    "SPELL_AURA_REFRESH": ("AURA", "REFRESH"),
    "SPELL_AURA_REMOVED": ("AURA", "REMOVED"),
    "SPELL_AURA_APPLIED_DOSE": ("AURA", "DOSE"),
    "SPELL_AURA_REMOVED_DOSE": ("AURA", "DOSE"),
    "SPELL_CAST_SUCCESS": ("CAST", "SUCCESS"),
    "SPELL_RESURRECT": ("RESURRECT", ""),
    "UNIT_DIED": ("DIED", ""),
    "SPELL_INSTAKILL": ("DIED", "INSTAKILL"),
    "SWING_MISSED": ("MISS", "SWING"),
    "SPELL_MISSED": ("MISS", "SPELL"),
    "SPELL_PERIODIC_MISSED": ("MISS", "DOT"),
    "RANGE_MISSED": ("MISS", "RANGE"),
    "DAMAGE_SHIELD_MISSED": ("MISS", "SHIELD"),
}

SAVE_SPELLS = {
    "75480", # Petrified Twilight Scale
    "75477",
    "71639", # Corpse Tongue Coin
    "71638", # Sindragosa's Flawless Fang
    "67753", # Juggernaut's Vitality
    "67753", # Satrina's Impeding Scarab
    "67596", # PvP
    "67631", # The Black Heart
    "71586", # Corroded Skeleton Key
    "71569", # Ick's Rotting Thumb
    "64763", # Heart of Iron
    "60180", # Repelling Charge
    "60286", # Defender's Code
    "46021", # Royal Seal of King Llane
    "45313", # Furnace Stone
    "64763", # Heart of Iron
    "67694", # Glyph of Indomitability
    "49080", # Brawler's Souvenir
    "54861", # Nitro Boosts
    # DEATHKNIGHT
    "42650", # Army of the Dead
    "45529", # Blood Tap
    "48707", # Anti-Magic Shell
    "48792", # Icebound Fortitude
    "48982", # Rune Tap
    "49039", # Lichborne
    "49222", # Bone Shield
    "51052", # Anti-Magic Zone
    "51271", # Unbreakable Armor
    "55233", # Vampiric Blood
    "64859", # Blade Barrier
    "70654", # Blood Armor
    # DRUID
    "5229",  # Enrage
    "5487",  # Bear Form
    "9634",  # Dire Bear Form
    "22812", # Barkskin
    "22842", # Frenzied Regeneration
    "48575", # Cower
    "61336", # Survival Instincts
    "62606", # Savage Defense
    # HUNTER
    "781",   # Disengage
    "5384",  # Feign Death
    "19263", # Deterrence
    # MAGE
    "66",    # Invisibility
    "1953",  # Blink
    "45438", # Ice Block
    "55342", # Mirror Image
    "43010", # Fire Ward (Rank 7)
    "43012", # Frost Ward (Rank 7)
    "43020", # Mana shield (Rank 9)
	"43039", # Ice Barrier (Rank 8)
    # PALADIN
    "498",   # Divine Protection
    "642",   # Divine Shield
    "1038",  # Hand of Salvation
    "1044",  # Hand of Freedom
    "6940",  # Hand of Sacrifice
    "10278", # Hand of Protection
    "19752", # Divine Intervention
    "31821", # Aura Mastery
    "31850", # Ardent Defender
    "31884", # Avenging Wrath
    "48788", # Lay on Hands
    "48952", # Holy Shield
    "53601", # Sacred Shield - Aura
    "58597", # Sacred Shield - Shield
    "64205", # Divine Sacrifice
    "66233", # Ardent Defender
    "70940", # Divine Guardian
    # PRIEST
    "586",   # Fade
    "15359", # Inspiration
    "33206", # Pain Suppression
    "47585", # Dispersion
    "47788", # Guardian Spirit
    "48066", # Power Word: Shield
    # ROGUE
    "26669", # Evasion (Rank 2)
    "26889", # Vanish (Rank 3)
    "31224", # Cloak of Shadows
    "48659", # Feint
    # SHAMAN
    "16237", # Ancestral Fortitude
    # WARLOCK
    "47891", # Shadow Ward
    # WARRIOR
    "871",   # Shield Wall
    "2565",  # Shield Block
    "12975"  # Last Stand
    "58374", # Glyph of Blocking
}

ARDENT_DEFENDER = {"66235", }
SELF_RESSURECT = {
    "21169", # Reincarnation
    "47882", # Soulstone
}
# 2/15 21:38:50.554  SPELL_CAST_SUCCESS,0x07000000006CC66E,"Enhica",0x514,0x0000000000000000,nil,0x80000000,21169,"Reincarnation",0x8
# 2/18 14:36:53.002  SPELL_CAST_SUCCESS,0x00000000003DD0B6,"Afalla",0x40514,0x0000000000000000,nil,0x80000000,47882,"Use Soulstone",0x1

def to_int(line: str):
    return int(line.split(' ', 1)[1][:8].replace(':', ''))

def to_int(line: str):
    return int(line[-12:-4].replace(':', ''))

def _get_minutes_seconds(line: str):
    _, m, s = line.split(':', 3)
    return int(m), float(s)

def _toint3(main_line: str):
    m1, s1 = _get_minutes_seconds(main_line)
    def inner(line):
        m2, s2 = _get_minutes_seconds(line)
        if m1 != m2:
            m = m1 - m2 - 1
            s = s1 - s2 + 60
        else:
            m = 0
            s = s1 - s2
        return f"-{m}:{s:0>6.3f}"
    return inner

def _normalize_line(line: list[str]):
    for x in [11, 8, 7, 5, 3]:
        try:
            del line[x]
        except IndexError:
            pass

    while len(line) < 7:
        line.append("")
        
    try:
        line[4] = int(line[4])
    except ValueError:
        pass

    try:
        line[1:2] = FLAGS_CUT[line[1]]
    except KeyError:
        line[1:2] = line[1].split("_")[:2]

    if line[1] == "AURA":
        line[1] = line[-2]

class Death(list[list[str]]):
    pass

class CharDeaths(dict[str, Death]):
    def __init__(self):
        self.alive = True
        self.latest_death = Death()
        self.latest_death_ts = 0

    def new_death(self, ts):
        self.alive = False
        self.latest_death_ts = to_int(ts)
        self.latest_death = Death()
        self[ts] = self.latest_death
        return self.latest_death

    def normilize(self):
        for _id, death in list(self.items()):
            f0 = _toint3(death[0][0])
            death_at = 0
            if death[0][1] in {"SPELL_CAST_SUCCESS", "SPELL_RESURRECT"}:
                death[0][0] = f0(death[1][0]).replace('-', '+')
                f0 = _toint3(death[1][0])
                death_at = 1

            death[death_at][0] = "0:00.000"

            for x in death[death_at+1:]:
                x[0] = f0(x[0])

            for x in death:
                _normalize_line(x)

        return self


@running_time
def get_deaths(logs_slice: list[str]):
    players_deaths = defaultdict(CharDeaths)

    for line in reversed(logs_slice):
        if "0x0" not in line:
            continue
        
        line = line.split(',', 11)
        if line[4][:3] != "0x0":
            continue
        
        player = players_deaths[line[4]]
        flag = line[1]

        if flag == "SPELL_CAST_SUCCESS":
            if line[6] in SELF_RESSURECT:
                player.new_death(line[0]).append(line)
                continue
            
            now = to_int(line[0])
            if player.latest_death_ts - now < 100:
                player.latest_death.append(line)

        elif flag in FLAGS_OFFENSIVE:
            if flag in FLAGS_DMG and line[10] != "0":
                if player.alive:
                    player.new_death(line[0])
            elif player.alive:
                continue
            player.latest_death.append(line)

        elif flag in HEAL_FLAGS:
            if line[6] in ARDENT_DEFENDER:
                if player.alive:
                    player.new_death(line[0])
            
            if player.alive:
                continue
            
            if line[10] != "0":
                player.alive = True
            
            player.latest_death.append(line)
        
        elif flag in AURA_FLAGS:
            if line[6] in SAVE_SPELLS or "DEBUFF" in line:
                now = to_int(line[0])
                if abs(player.latest_death_ts - now) < 100:
                    player.latest_death.append(line)

        elif flag in DEATH_FLAGS:
            if player.alive:
                player.new_death(line[0])
            player.latest_death.append(line)

        elif flag == "SPELL_RESURRECT":
            player.new_death(line[0]).append(line)
    
    for player_deaths in players_deaths.values():
        player_deaths.normilize()

    return players_deaths


class Deaths(logs_base.THE_LOGS):
    # @logs_base.cache_wrap
    def get_deaths_v2(self, s, f):
        logs_slice = self.LOGS[s:f]
        slice_start = logs_slice[0].split(',')[0]

        players_deaths = get_deaths(logs_slice)
        players_deaths_sorted = sorted((
            (ts, player_guid, player_death)
            for player_guid, player_deaths in players_deaths.items()
            for ts, player_death in player_deaths.items()
        ))
        
        players_deaths_formatted = {}
        for death_timestamp, player_guid, player_death in players_deaths_sorted:
            z = self.get_timedelta_seconds(slice_start, death_timestamp)
            name = self.guid_to_name(player_guid)
            _id = f"{z}-{name}"
            players_deaths_formatted[_id] = {
                "player": name,
                "from_start": f"{int(z//60):0>2}:{z%60:0>6.3f}",
                "death": player_death,
            }

        return players_deaths_formatted

    def get_deaths_v2_wrap(self, segments):
        deaths = self.get_deaths_v2(*segments[0])
        return {
            "DEATHS": deaths,
            "CLASSES": self.get_classes(),
            "PLAYERS": self.get_players_guids(),
            "GUIDS": self.get_all_guids(),
            "SPELLS": self.get_spells(),
        }

def _test2():
    report = Deaths("23-02-10--21-00--Safiyah--Lordaeron")
    report.LOGS
    enc_data = report.get_enc_data()
    s, f = enc_data["The Lich King"][-2]
    _all = report.get_deaths_v2(s, f)
    for _id, _dth in _all.items():
        print(_id)

if __name__ == "__main__":
    _test2()
