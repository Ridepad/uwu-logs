from constants import running_time


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
    "6940",  # Hand of Sacrifice
    "31821", # Aura Mastery
    "53601", # Sacred Shield - Aura
    "58597", # Sacred Shield - Shield
    "64205", # Divine Sacrifice
    "70940", # Divine Guardian
    "71586", # Hardened Skin
    "45438", # Ice Block
    "47585", # Dispersion
    "642",   # Divine Shield
    "51052", # Anti-Magic Zone
    "49222", # Bone Shield
    "51271", # Unbreakable Armor
    "5487",  # Bear Form
    "9634",  # Dire Bear Form
    "48575", # Cower
    "33206", # Pain Suppression
    "48066", # Power Word: Shield
    "586",   # Fade
    "26889", # Vanish
    "2565",  # Shield Block
    "47891", # Shadow Ward
    "19263", # Deterrence
    "26669", # Evasion

    "15359", # Inspiration
    "16237", # Ancestral Fortitude
    
    "71638", # Aegis of Dalaran
    "54861", # Nitro Boosts
    "75480", # Scaly Nimbleness

    "48707", # Anti-Magic Shell
    "48792", #IBF
    "55233", #Vampiric Blood
    "64859", #Blade Barrier
    "70654", #Blood Armor
    "45529", # Blood Tap
    "71586", # Hardened Skin

    "498",   #Divine Protection
    "31884", #Avenging Wrath
    "48952", #Holy Shield

    "5229",  #Enrage
    "22812", #Barkskin
    "22842", #Frenzied Regeneration
    "61336", #Survival Instincts

    # "73799", #Soul Reaper
    # "6788", #Weakened Soul
    # "25771", #Forbearance
    # "69762", #Unchained Magic
}

SAVE_SPELLS2 = {
    "Guardian Spirit",
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

# 9/10 00:11:02.037,SPELL_DAMAGE,0x0600000000509B66,"Bloodhgarm",0xF1300087EF0000D1,"Dreadscale",48461,"Wrath",0x8,14042,11837,8,0,0,0,1,nil,nil

@running_time
def get_deaths(logs_slice: list[str], guid):
    DEATHS: dict[str, list] = {}
    new_death = []
    DEAD = False
    last_death = 0

    def new_line(line):
        print(line)
        new_death.append(line)

    for line in reversed(logs_slice):
        if guid not in line:
            continue

        line = line.split(',', 11)
        if line[4] != guid:
            if line[2] != guid or line[1] != "SPELL_CAST_SUCCESS":
                continue
            if line[6] in SELF_RESSURECT:
                print("\n\tSELF_RESSURECT")
                print("\n\tNEW DEATH")
                DEATHS[line[0]] = new_death = []
                DEAD = True
                last_death = to_int(line[0])
                new_line(line)
            else:
                now = to_int(line[0])
                if last_death - now < 100:
                    new_line(line)

        elif line[1] in DEATH_FLAGS:
            print('\n\tDEAD')
            if not DEAD:
                print("\n\tNEW DEATH")
                DEATHS[line[0]] = new_death = []
            DEAD = True
            last_death = to_int(line[0])
            new_line(line)

        elif line[1] == "SPELL_RESURRECT":
            print('\n\tRESURRECT')
            print("\n\tNEW DEATH")
            DEATHS[line[0]] = new_death = []
            DEAD = True
            last_death = to_int(line[0])
            new_line(line)

        elif line[1] in FLAGS_OFFENSIVE:
            if line[1] in FLAGS_DMG and line[10] != "0":
                print("\n\tOVERKILL")
                if not DEAD:
                    print("\n\tNEW DEATH")
                    DEATHS[line[0]] = new_death = []
                DEAD = True
                last_death = to_int(line[0])
                new_line(line)
            
            elif DEAD:
                new_line(line)

        elif line[1] in HEAL_FLAGS:
            if line[6] in ARDENT_DEFENDER:
                print("\n\tARDENT_DEFENDER")
                if not DEAD:
                    print("\n\tNEW DEATH")
                    DEATHS[line[0]] = new_death = []
                DEAD = True
                last_death = to_int(line[0])
            
            if not DEAD:
                continue
            
            if line[10] != "0":
                print()
                print("\n\tHEALED")
                DEAD = False
            
            new_line(line)
        
        elif line[1] in AURA_FLAGS:
            if line[6] in SAVE_SPELLS or "DEBUFF" in line:
                now = to_int(line[0])
                if last_death - now < 100:
                    new_line(line)


    return {t:d for t,d in DEATHS.items() if len(d) > 1}

FLAGS2 = {"SPELL_CAST_SUCCESS", "SPELL_RESURRECT"}
def find_last_hit(death):
    for line in death:
        print(line[1])
        if line[1] not in FLAGS2:
            return death.index(line)



def get_minutes_seconds(line):
    print(line)
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
        
def main_test():
    import logs_main
    report = logs_main.THE_LOGS("22-08-25--20-21--Meownya--Lordaeron")
    enc_data = report.get_enc_data()
    players = report.get_players_guids()
    players = {v:k for k,v in players.items()}
    # print(players)
    # guid = "0x06000000004B3846"
    guid = players["Hulina"]
    s, f = enc_data["The Lich King"][-3]
    logs_slice = report.get_logs(s, f)
    d = get_deaths(logs_slice, guid)
    sfjsiojfasiojfiod(d)
    for t, _d in d.items():
        for x in _d:
            print(x)


if __name__ == "__main__":
    main_test()
