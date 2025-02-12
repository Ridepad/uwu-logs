
# for detection of players' classes
SPELL_BOOK = {
    # Death Knight
    "49222": 0, # Bone Shield
    "49560": 0, # Death Grip
    "51735": 0, # Ebon Plague
    "55095": 0, # Frost Fever
    "57623": 0, # Horn of Winter
    "49016": 0, # Hysteria
    "49909": 0, # Icy Touch
    "51124": 0, # Killing Machine
    "66992": 0, # Plague Strike
    "50526": 0, # Wandering Plague
    # Druid
     "2782": 1, # Remove Curse
    "29166": 1, # Innervate
     "5570": 1, # Insect Swarm
    "24977": 1, # Insect Swarm
    "48468": 1, # Insect Swarm
    "24932": 1, # Leader of the Pack
    "48566": 1, # Mangle (Cat)
    "48422": 1, # Master Shapeshifter
    "48463": 1, # Moonfire
    "48574": 1, # Rake
    "17116": 1, # Nature's Swiftness
     "9858": 1, # Regrowth
    "48443": 1, # Regrowth
     "8910": 1, # Rejuvenation
     "9841": 1, # Rejuvenation
    "26982": 1, # Rejuvenation (Rank 13)
    "48441": 1, # Rejuvenation (Rank 15)
    "70691": 1, # Rejuvenation
    "52610": 1, # Savage Roar
    "48572": 1, # Shred
    "48465": 1, # Starfire
    "48562": 1, # Swipe (Bear)
    "62078": 1, # Swipe (Cat)
    "48438": 1, # Wild Growth
    "48461": 1, # Wrath
    "48466": 1, # Hurricane
    "33831": 1, # Force of Nature
    "48391": 1, # Owlkin Frenzy
    "22812": 1, # Barkskin
    # Hunter
    "14325": 2, # Hunter's Mark
    "53338": 2, # Hunter's Mark
    "14290": 2, # Multi-Shot
    "20904": 2, # Aimed Shot
    "49050": 2, # Aimed Shot
    "53209": 2, # Chimera Shot
    "35079": 2, # Misdirection
    "49001": 2, # Serpent Sting
    "58433": 2, # Volley
    # Mage
    "10181": 3, # Frostbolt
    "10216": 3, # Flamestrike
    "36032": 3, # Arcane Blast
    "42921": 3, # Arcane Explosion
    "12042": 3, # Arcane Power
    "44401": 3, # Missile Barrage
    "42938": 3, # Blizzard
    "42833": 3, # Fireball
    "12472": 3, # Icy Veins
    "12654": 3, # Ignite
    "44401": 3, # Missile Barrage
    "42842": 3, # Frostbolt
    "47610": 3, # Frostfire Bolt
    "42873": 3, # Fire Blast
    # Paladin
    "48827": 4, # Avenger's Shield
    "53654": 4, # Beacon of Light
    "48819": 4, # Consecration
      "642": 4, # Divine Shield
    "66922": 4, # Flash of Light
    "25898": 4, # Greater Blessing of Kings
    "48938": 4, # Greater Blessing of Wisdom
    "10308": 4, # Hammer of Justice
    "53595": 4, # Hammer of the Righteous
    "67485": 4, # Hand of Reckoning
    "48823": 4, # Holy Shock
    "20272": 4, # Illumination
    "58597": 4, # Sacred Shield
    "26017": 4, # Vindication
    "21084": 4, # Seal of Righteousness
    "31884": 4, # Avenging Wrath
    "54172": 4, # Divine Storm
    "59578": 4, # The Art of War
    "35395": 4, # Crusader Strike
    # Priest
     "9474": 5, # Flash Heal
    "14751": 5, # Inner Focus
    "10929": 5, # Renew | Rank 9
    "25315": 5, # Renew | Rank 10
    "25222": 5, # Renew | Rank 12
    "48068": 5, # Renew | Rank 14
    "10965": 5, # Greater Heal
    "48089": 5, # Circle of Healing
    "47753": 5, # Divine Aegis
    "58381": 5, # Mind Flay
    "53000": 5, # Penance
    "10901": 5, # Power Word: Shield
    "25217": 5, # Power Word: Shield
    "25392": 5, # Prayer of Fortitude
    "48170": 5, # Prayer of Shadow Protection
    "32999": 5, # Prayer of Spirit
    "48125": 5, # Shadow Word: Pain
    "15473": 5, # Shadowform
    "64085": 5, # Vampiric Touch
    # Rogue
    "22482": 6, # Blade Flurry
    "35548": 6, # Combat Potency
    "57993": 6, # Envenom
    "11300": 6, # Eviscerate
    "48668": 6, # Eviscerate
    "52874": 6, # Fan of Knives
    "48659": 6, # Feint
    "51637": 6, # Focused Attacks
     "8643": 6, # Kidney Shot
    "57842": 6, # Killing Spree
    "11294": 6, # Sinister Strike
    "48638": 6, # Sinister Strike
     "1784": 6, # Stealth
    "57933": 6, # Tricks of the Trade
    # Shaman
    "52759": 7, # Ancestral Awakening
    "51886": 7, # Cleanse Spirit
    "16246": 7, # Clearcasting
      "379": 7, # Earth Shield
      "547": 7, # Healing Wave | Rank 3
     "8005": 7, # Healing Wave | Rank 7
    "10396": 7, # Healing Wave | Rank 9
    "25357": 7, # Healing Wave | Rank 10
    "25396": 7, # Healing Wave | Rank 12
    "49273": 7, # Healing Wave | Rank 14
     "1064": 7, # Chain Heal | Rank 1
    "10623": 7, # Chain Heal | Rank 3
    "25423": 7, # Chain Heal | Rank 5
    "55459": 7, # Chain Heal | Rank 7
    "10468": 7, # Lesser Healing Wave
    "16166": 7, # Elemental Mastery
    "16188": 7, # Nature's Swiftness
    "51533": 7, # Feral Spirit
    "60043": 7, # Lava Burst
    "49238": 7, # Lightning Bolt
    "49279": 7, # Lightning Shield
    "16190": 7, # Mana Tide Totem
    "70806": 7, # Rapid Currents
    "61301": 7, # Riptide
    "32176": 7, # Stormstrike
    "53390": 7, # Tidal Waves
    "57961": 7, # Water Shield
    "25504": 7, # Windfury Attack
    # Warlock
    "11722": 8, # Curse of the Elements
    "47865": 8, # Curse of the Elements
    "11672": 8, # Corruption
    "25311": 8, # Corruption | Rank 7
    "27216": 8, # Corruption | Rank 8
    "47813": 8, # Corruption | Rank 10
    "47893": 8, # Fel Armor
    "31818": 8, # Life Tap # SPELL_ENERGIZE
    "32553": 8, # Life Tap # SPELL_ENERGIZE Mana Feed
    "63321": 8, # Life Tap # Glyph
    "47241": 8, # Metamorphosis
      "686": 8, # Shadow Bolt | Rank 1
    "11661": 8, # Shadow Bolt | Rank 9
    "25307": 8, # Shadow Bolt | Rank 10
    "27209": 8, # Shadow Bolt | Rank 11
    "47809": 8, # Shadow Bolt | Rank 13
    "25228": 8, # Soul Link
    "47843": 8, # Unstable Affliction
    # Warrior
     "2457": 9, # Battle Stance
     "2458": 9, # Berserker Stance
    "29131": 9, # Bloodrage
    "23894": 9, # Bloodthirst
    "23880": 9, # Bloodthirst
    "47440": 9, # Commanding Shout
    "59653": 9, # Damage Shield
    "12292": 9, # Death Wish
    "12721": 9, # Deep Wounds
       "71": 9, # Defensive Stance
    "11567": 9, # Heroic Strike
    "47450": 9, # Heroic Strike
    "44949": 9, # Whirlwind
}

# for detection of players' specs after
SPELL_BOOK_SPEC = {
    "death-knight": {
        "49016": 1, # Hysteria
        "55233": 1, # Vampiric Blood
        "49005": 1, # Mark of Blood
        "48982": 1, # Rune Tap
        "50449": 1, # Bloody Vengeance
        "70654": 1, # Blood Armor

        "55268": 2, # Frost Strike
        "51271": 2, # Unbreakable Armor
        "51411": 2, # Howling Blast
        "50401": 2, # Razor Frost
        "51714": 2, # Frost Vulnerability
        
        "49206": 3, # Summon Gargoyle
        "55271": 3, # Scourge Strike
        "50526": 3, # Wandering Plague
        "51735": 3, # Ebon Plague
        "66803": 3, # Desolation
    },
    "druid": {
        "60433": 1, # Earth and Moon
        "48468": 1, # Insect Swarm
        "48518": 1, # Eclipse (Lunar)
        "48517": 1, # Eclipse (Solar)
        "33831": 1, # Force of Nature
        "53195": 1, # Starfall
        "53227": 1, # Typhoon
        "24907": 1, # Moonkin Aura

        "50213": 2, # Tiger's Fury
        "62078": 2, # Swipe (Cat)
        "48572": 2, # Shred
        "52610": 2, # Savage Roar
        "62606": 2, # Savage Defense
        "49800": 2, # Rip
        "48574": 2, # Rake
        "33987": 2, # Mangle (Bear)
        "48566": 2, # Mangle (Cat)
        "51178": 2, # King of the Jungle
        "17099": 2, # Furor
        "48577": 2, # Ferocious Bite
        "49376": 2, # Feral Charge - Cat
        "17392": 2, # Faerie Fire (Feral)
        "16857": 2, # Faerie Fire (Feral)
        "47468": 2, # Claw

        "17116": 3, # Nature's Swiftness
        "53251": 3, # Wild Growth
        "48542": 3, # Revitalize
        "34123": 3, # Tree of Life
        "18562": 3, # Swiftmend
        "48504": 3, # Living Seed
    },
    "hunter": {
        "19574": 1, # Bestial Wrath
        "19577": 1, # Intimidation
        "34471": 1, # The Beast Within
        "53257": 1, # Cobra Strikes
        "57475": 1, # Kindred Spirits
        "34456": 1, # Ferocious Inspiration
        "75447": 1, # Ferocious Inspiration

        "20904": 2, # Aimed Shot
        "20906": 2, # Trueshot Aura
        "53220": 2, # Improved Steady Shot
        "53209": 2, # Chimera Shot
        "53353": 2, # Chimera Shot - Serpent
        "23989": 2, # Readiness
        "63468": 2, # Piercing Shots

        "53301": 3, # Explosive Shot (Rank 1)
        "60051": 3, # Explosive Shot (Rank 2)
        "60052": 3, # Explosive Shot (Rank 3)
        "60053": 3, # Explosive Shot (Rank 4)
        "34501": 3, # Expose Weakness
    },
    "mage": {
        "12043": 1, # Presence of Mind
        "44781": 1, # Arcane Barrage
        "12042": 1, # Arcane Power
        "44401": 1, # Missile Barrage

        "12654": 2, # Ignite
        "55360": 2, # Living Bomb
        "48108": 2, # Hot Streak
        "28682": 2, # Combustion
        "11958": 3, # Cold Snap

        "12579": 3, # Winter's Chill
        "31687": 3, # Summon Water Elemental
        "44572": 3, # Deep Freeze
    },
    "paladin": {
        "53652": 1, # Beacon of Light
        "53654": 1, # Beacon of Light
        "25903": 1, # Holy Shock
        "48825": 1, # Holy Shock
        "54149": 1, # Infusion of Light
        "31834": 1, # Light's Grace
        "31842": 1, # Divine Illumination
        "20216": 1, # Divine Favor

        "53595": 2, # Hammer of the Righteous
        "66233": 2, # Ardent Defender
        "32700": 2, # Avenger's Shield (Rank 3)
        "48827": 2, # Avenger's Shield (Rank 5)
        "20132": 2, # Redoubt
        "27179": 2, # Holy Shield (Rank 4)
        "48952": 2, # Holy Shield (Rank 6)
        "70760": 2, # Deliverance
        
        "59578": 3, # The Art of War
        "35395": 3, # Crusader Strike
        "53385": 3, # Divine Storm
        "54203": 3, # Sheath of Light
    },
    "priest": {
        "47755": 1, # Rapture
        "52985": 1, # Penance
        "47753": 1, # Divine Aegis
        "59891": 1, # Borrowed Time
        "10060": 1, # Power Infusion
        # 15359": 1, # Inspiration
        
        "63730": 2, # Serendipity
        "63731": 2, # Serendipity
        "63733": 2, # Serendipity
        "63734": 2, # Serendipity
        "63735": 2, # Serendipity
        "63737": 2, # Serendipity
        "63544": 2, # Empowered Renew
        "63725": 2, # Holy Concentration
        "34864": 2, # Circle of Healing (Rank 3)
        "34866": 2, # Circle of Healing (Rank 5)
        "48089": 2, # Circle of Healing (Rank 7)
        "47788": 2, # Guardian Spirit
        "27827": 2, # Spirit of Redemption
        "34754": 2, # Clearcasting

        "34917": 3, # Vampiric Touch (Rank 3)
        "48160": 3, # Vampiric Touch (Rank 5)
        "63675": 3, # Improved Devouring Plague
        "33198": 3, # Misery
        "33200": 3, # Misery
        "61792": 3, # Shadowy Insight
        "15290": 3, # Vampiric Embrace
        "15473": 3, # Shadowform
        "47585": 3, # Dispersion
    },
    "rogue": {
        "57993": 1, # Envenom
        "48666": 1, # Mutilate

        "11294": 2, # Sinister Strike
        "48638": 2, # Sinister Strike
        "13750": 2, # Adrenaline Rush
        "13877": 2, # Blade Flurry
        "51690": 2, # Killing Spree

        "51713": 3, # Shadow Dance
        "36554": 3, # Shadowstep
        "14183": 3, # Premeditation
        "14185": 3, # Preparation
        "48660": 3, # Hemorrhage
    },
    "shaman": {
        "30706": 1, # Totem of Wrath
        "57722": 1, # Totem of Wrath
        "59159": 1, # Thunderstorm
        "16166": 1, # Elemental Mastery
        "45296": 1, # Lightning Bolt (Proc)
        "49240": 1, # Lightning Bolt (Proc)
        "49269": 1, # Chain Lightning (Proc)

        "60103": 2, # Lava Lash
        "51533": 2, # Feral Spirit
        "30823": 2, # Shamanistic Rage
        "17364": 2, # Stormstrike
        "70829": 2, # Elemental Rage

        "379": 3, # Earth Shield
        "53390": 3, # Tidal Waves
        "52752": 3, # Ancestral Awakening
        # 61301": 3, # Riptide
        "17359": 3, # Mana Tide Totem
        "16190": 3, # Mana Tide Totem
        "51886": 3, # Cleanse Spirit
        "16188": 3, # Nature's Swiftness
        "16237": 3, # Ancestral Fortitude 
    },
    "warlock": {
        "59161": 1, # Haunt (Rank 2)
        "59164": 1, # Haunt (Rank 4)
        "30405": 1, # Unstable Affliction (Rank 3)
        "47843": 1, # Unstable Affliction (Rank 5)
        "64368": 1, # Eradication (Rank 2)
        "64371": 1, # Eradication (Rank 3)
        "30911": 1, # Siphon Life

        "71165": 2, # Molten Core
        "47241": 2, # Metamorphosis
        "63167": 2, # Decimation
        "47193": 2, # Demonic Empowerment

        "59172": 3, # Chaos Bolt
        "47847": 3, # Shadowfury
        "17962": 3, # Conflagrate (Rank 1)
        "30912": 3, # Conflagrate (Rank 6)
        "18871": 3, # Shadowburn
    },
    "warrior": {
        "7384": 1, # Overpower
        "12294": 1, # Mortal Strike
        "47485": 1, # Mortal Strike
        "47486": 1, # Mortal Strike
        "30330": 1, # Mortal Strike
        "25248": 1, # Mortal Strike
        "21551": 1, # Mortal Strike
        "21552": 1, # Mortal Strike
        "21553": 1, # Mortal Strike
        "52437": 1, # Sudden Death
        "60503": 1, # Taste for Blood
        "46924": 1, # Bladestorm

        "25251": 2, # Bloodthirst
        "23881": 2, # Bloodthirst
        "23894": 2, # Bloodthirst
        "30335": 2, # Bloodthirst
        # "12292": 2, # Death Wish
        "30033": 2, # Rampage

        "46968": 3, # Shockwave
        "30016": 3, # Devastate (Rank 2)
        "30022": 3, # Devastate (Rank 3)
        "47498": 3, # Devastate (Rank 5)
    },
}

CLASSES = {
    "Death Knight": {
        "": "class_deathknight",
        "Blood": "spell_deathknight_bloodpresence",
        "Frost": "spell_deathknight_frostpresence",
        "Unholy": "spell_deathknight_unholypresence"
    },
    "Druid": {
        "": "class_druid",
        "Balance": "spell_nature_starfall",
        "Feral Combat": "ability_racial_bearform",
        "Restoration": "spell_nature_healingtouch"
    },
    "Hunter": {
        "": "class_hunter",
        "Beast Mastery": "ability_hunter_beasttaming",
        "Marksmanship": "ability_marksmanship",
        "Survival": "ability_hunter_swiftstrike"
    },
    "Mage": {
        "": "class_mage",
        "Arcane": "spell_holy_magicalsentry",
        "Fire": "spell_fire_firebolt02",
        "Frost": "spell_frost_frostbolt02"
    },
    "Paladin": {
        "": "class_paladin",
        "Holy": "spell_holy_holybolt",
        "Protection": "spell_holy_devotionaura",
        "Retribution": "spell_holy_auraoflight"
    },
    "Priest": {
        "": "class_priest",
        "Discipline": "spell_holy_wordfortitude",
        "Holy": "spell_holy_guardianspirit",
        "Shadow": "spell_shadow_shadowwordpain"
    },
    "Rogue": {
        "": "class_rogue",
        "Assassination": "ability_rogue_eviscerate",
        "Combat": "ability_backstab",
        "Subtlety": "ability_stealth"
    },
    "Shaman": {
        "": "class_shaman",
        "Elemental": "spell_nature_lightning",
        "Enhancement": "spell_nature_lightningshield",
        "Restoration": "spell_nature_magicimmunity"
    },
    "Warlock": {
        "": "class_warlock",
        "Affliction": "spell_shadow_deathcoil",
        "Demonology": "spell_shadow_metamorphosis",
        "Destruction": "spell_shadow_rainoffire"
    },
    "Warrior": {
        "": "class_warrior",
        "Arms": "ability_warrior_savageblow",
        "Fury": "ability_warrior_innerrage",
        "Protection": "ability_warrior_defensivestance"
    }
}

CLASS_TO_HTML = {
    'Death Knight': 'death-knight',
    'Druid': 'druid',
    'Hunter': 'hunter',
    'Mage': 'mage',
    'Paladin': 'paladin',
    'Priest': 'priest',
    'Rogue': 'rogue',
    'Shaman': 'shaman',
    'Warlock': 'warlock',
    'Warrior': 'warrior'
}

CLASS_FROM_HTML = {
    "death-knight": "Death Knight",
    "druid": "Druid",
    "hunter": "Hunter",
    "mage": "Mage",
    "paladin": "Paladin",
    "priest": "Priest",
    "rogue": "Rogue",
    "shaman": "Shaman",
    "warlock": "Warlock",
    "warrior": "Warrior"
}


class _SpecInfo:
    __slots__ = "name", "html_name", "class_name", "class_name_html", "index", "icon"
    def __init__(self, class_name: str, spec_name: str, spec_index: int, spec_icon: str) -> None:
        if spec_name:
            spec_name = f"{spec_name} {class_name}"
        else:
            spec_name = class_name
        self.name = spec_name
        self.html_name = spec_name.lower().replace(" ", "-")
        self.class_name = class_name
        self.class_name_html = class_name.lower().replace(" ", "-")
        self.index = spec_index
        self.icon = spec_icon

def _gen_specs():
    spec_index = 0
    for class_name, specs in CLASSES.items():
        for spec_name, spec_icon in specs.items():
            yield _SpecInfo(class_name, spec_name, spec_index, spec_icon)
            spec_index += 1

SPECS_LIST = list(_gen_specs())

class SpecInfoDict(dict[str, _SpecInfo]):
    def __init__(self):
        for spec_info in SPECS_LIST:
            self[spec_info.name] = spec_info
            self[spec_info.html_name] = spec_info

SPECS_DICT = SpecInfoDict()

CLASSES_LIST = list(CLASSES)
CLASSES_LIST_HTML = list(CLASS_FROM_HTML)
