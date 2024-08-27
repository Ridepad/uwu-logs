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
    "ENVIRONMENTAL_DAMAGE": ("DAMAGE", "ENV"),
    "SPELL_HEAL": ("HEAL", "HEAL"),
    "SPELL_PERIODIC_HEAL": ("HEAL", "HOT"),
    "SPELL_AURA_APPLIED": ("AURA", "APPLIED"),
    "SPELL_AURA_REFRESH": ("AURA", "REFRESH"),
    "SPELL_AURA_REMOVED": ("AURA", "REMOVED"),
    "SPELL_AURA_APPLIED_DOSE": ("AURA", "DOSE"),
    "SPELL_AURA_REMOVED_DOSE": ("AURA", "DOSE"),
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

def to_int(line: str):
    return int(line.split(' ', 1)[1][:8].replace(':', ''))

def to_int(line: str):
    return int(line[-12:-4].replace(':', ''))

@running_time
def get_deaths(logs_slice: list[str], guid):
    DEATHS: dict[str, list] = {}
    new_death = []
    DEAD = False
    last_death = 0

    for line in reversed(logs_slice):
        if guid not in line:
            continue

        line = line.split(',', 11)
        if line[4] != guid:
            if line[2] != guid or line[1] != "SPELL_CAST_SUCCESS":
                continue
            if line[6] in SELF_RESSURECT:
                DEATHS[line[0]] = new_death = []
                DEAD = True
                last_death = to_int(line[0])
                new_death.append(line)
            else:
                now = to_int(line[0])
                if last_death - now < 100:
                    new_death.append(line)

        elif line[1] in DEATH_FLAGS:
            if not DEAD:
                DEATHS[line[0]] = new_death = []
            DEAD = True
            last_death = to_int(line[0])
            new_death.append(line)

        elif line[1] == "SPELL_RESURRECT":
            DEATHS[line[0]] = new_death = []
            DEAD = True
            last_death = to_int(line[0])
            new_death.append(line)

        elif line[1] in FLAGS_OFFENSIVE:
            if line[1] in FLAGS_DMG and line[10] != "0":
                if not DEAD:
                    DEATHS[line[0]] = new_death = []
                DEAD = True
                last_death = to_int(line[0])
                new_death.append(line)
            
            elif DEAD:
                new_death.append(line)

        elif line[1] in HEAL_FLAGS:
            if line[6] in ARDENT_DEFENDER:
                if not DEAD:
                    DEATHS[line[0]] = new_death = []
                DEAD = True
                last_death = to_int(line[0])
            
            if not DEAD:
                continue
            
            if line[10] != "0":
                DEAD = False
            
            new_death.append(line)
        
        elif line[1] in AURA_FLAGS:
            if line[6] in SAVE_SPELLS or "DEBUFF" in line:
                now = to_int(line[0])
                if last_death - now < 100:
                    new_death.append(line)


    return {t:d for t,d in DEATHS.items() if len(d) > 1}

FLAGS2 = {"SPELL_CAST_SUCCESS", "SPELL_RESURRECT"}
def find_last_hit(death):
    for line in death:
        print(line[1])
        if line[1] not in FLAGS2:
            return death.index(line)



def get_minutes_seconds(line):
    _, m, s = line.split(':', 3)
    return int(m), float(s)

def toint3(main_line):
    m1, s1 = get_minutes_seconds(main_line)
    def inner(line):
        m2, s2 = get_minutes_seconds(line)
        if m1 != m2:
            m = m1 - m2 - 1
            s = s1 - s2 + 60
        else:
            m = 0
            s = s1 - s2
        return f"-{m}:{s:0>6.3f}"
    return inner
    
def normalize_line(line):
    for x in [11, 8, 7, 5, 3]:
        try:
            del line[x]
        except IndexError:
            pass
        
        try:
            line[4] = int(line[4])
        except ValueError:
            pass

        while len(line) < 7:
            line.append("")
    
def sfjsiojfasiojfiod(deaths: dict[str, list[str]]):
    for death in deaths.values():
        f0 = toint3(death[0][0])
        death_at = 0
        if death[0][1] in {"SPELL_CAST_SUCCESS", "SPELL_RESURRECT"}:
            death[0][0] = f0(death[1][0]).replace('-', '+')
            f0 = toint3(death[1][0])
            death_at = 1

        death[death_at][0] = "0:00.000"

        for x in death[death_at+1:]:
            x[0] = f0(x[0])

        for x in death:
            normalize_line(x)


class Deaths(logs_base.THE_LOGS):
    @logs_base.cache_wrap
    def death_info(self, s, f, guid):
        logs_slice = self.LOGS[s:f]
        deaths = get_deaths(logs_slice, guid)
        sfjsiojfasiojfiod(deaths)
        return deaths
    
    def get_deaths(self, segments, guid):
        deaths = {}
        if guid:
            for s, f in segments:
                deaths |= self.death_info(s, f, guid)
        return {
            "DEATHS": deaths,
            "CLASSES": self.get_classes(),
            "PLAYERS": self.get_players_guids(),
            "GUIDS": self.get_all_guids(),
            "SPELLS": self.get_spells(),
        }


def main_test():
    report = Deaths("24-02-09--20-49--Meownya--Lordaeron")
    enc_data = report.get_enc_data()
    guid = report.name_to_guid("Arcanestorm")
    s, f = enc_data["Lady Deathwhisper"][-1]
    logs_slice = report.get_logs(s, f)
    d = get_deaths(logs_slice, guid)
    sfjsiojfasiojfiod(d)
    for t, _d in d.items():
        for x in _d:
            print(x)


if __name__ == "__main__":
    main_test()
