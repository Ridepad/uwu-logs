import logging
import logs_main
import constants
import dmg_heals
from constants import SPECS_LIST, CLASS_FROM_HTML

CLASSES = list(CLASS_FROM_HTML)

SPELL_BOOK = {
    "Hysteria": 0,
    "Death Grip": 0,
    "Frost Fever": 0,
    "Ebon Plague": 0,
    "Bone Shield": 0,
    "Horn of Winter": 0,
    "Wandering Plague": 0,
    "Plague Strike": 0,
    "Killing Machine": 0,
    "Icy Touch": 0,
    "Shred": 1,
    "Savage Roar": 1,
    "Swipe (Bear)": 1,
    "Swipe (Cat)": 1,
    "Mangle (Cat)": 1,
    "Rake": 1,
    "Starfire": 1,
    "Wrath": 1,
    "Moonfire": 1,
    "Insect Swarm": 1,
    "Wild Growth": 1,
    "Regrowth": 1,
    "Rejuvenation": 1,
    "Leader of the Pack": 1,
    "Master Shapeshifter": 1,
    "Serpent Sting": 2,
    "Misdirection": 2,
    "Volley": 2,
    "Readiness": 2,
    "Aimed Shot": 2,
    "Chimera Shot": 2,
    "Ignite": 3,
    "Fireball": 3,
    "Arcane Barrage": 3,
    "Missile Barrage": 3,
    "Arcane Blast": 3,
    "Arcane Power": 3,
    "Blizzard": 3,
    "Icy Veins": 3,
    "Arcane Explosion": 3,
    "Winter's Chill": 3,
    "Arctic Winds": 3,
    "Brain Freeze": 3,
    "Beacon of Light": 4,
    "Avenger's Shield": 4,
    "Judgement of Wisdom": 4,
    "Judgement of Light": 4,
    "Hand of Reckoning": 4,
    "Hammer of Justice": 4,
    "Hammer of the Righteous": 4,
    "Sacred Shield": 4,
    "Consecration": 4,
    "Divine Shield": 4,
    "Holy Shock": 4,
    "Illumination": 4,
    "Flash of Light": 4,
    "Greater Blessing of Wisdom": 4,
    "Greater Blessing of Kings": 4,
    "Greater Blessing of Sanctuary": 4,
    "Mind Flay": 5,
    "Shadowform": 5,
    "Power Word: Shield": 5,
    "Weakened Soul": 5,
    "Vampiric Touch": 5,
    "Shadow Word: Pain": 5,
    "Penance": 5,
    "Divine Aegis": 5,
    "Circle of Healing": 5,
    "Renew": 5,
    "Prayer of Fortitude": 5,
    "Prayer of Spirit": 5,
    "Prayer of Shadow Protection": 5,
    "Sinister Strike": 6,
    "Fan of Knives": 6,
    "Blade Flurry": 6,
    "Eviscerate": 6,
    "Killing Spree": 6,
    "Combat Potency": 6,
    "Tricks of the Trade": 6,
    "Backstab": 6,
    "Shadowstep": 6,
    "Stealth": 6,
    "Kidney Shot": 6,
    "Focused Attacks": 6,
    "Envenom": 6,
    "Feint": 6,
    "Vanish": 6,
    "Water Shield": 7,
    "Lightning Shield": 7,
    "Windfury Attack": 7,
    "Stormstrike": 7,
    "Feral Spirit": 7,
    "Thunderstorm": 7,
    "Totem of Wrath": 7,
    "Elemental Mastery": 7,
    "Riptide": 7,
    "Tidal Waves": 7,
    "Earth Shield": 7,
    "Rapid Currents": 7,
    "Cleanse Spirit": 7,
    "Mana Tide Totem": 7,
    "Ancestral Awakening": 7,
    "Unstable Affliction": 8,
    "Soulfire": 8,
    "Metamorphosis": 8,
    "Shadow Bolt": 8,
    "Life Tap": 8,
    "Fel Armor": 8,
    "Soul Link": 8,
    "Corruption": 8,
    "Death Wish": 9,
    "Bloodrage": 9,
    "Heroic Strike": 9,
    "Bloodthirst": 9,
    "Damage Shield": 9,
    "Commanding Shout": 9,
    "Deep Wounds": 9,
    "Defensive Stance": 9,
    "Berserker Stance": 9,
    "Battle Stance": 9,
    "Whirlwind": 9,
}

IGNORED_SPELLS = {
    'PvP Trinket',
    'Melee',
    'Asphyxiation',
    'Backlash',
    'Basic Campfire',
    'Berserking',
    'Blessing of Sanctuary',
    'Chill of the Throne',
    'Conjure Refreshment',
    'Devouring Plague',
    'Divine Hymn',
    'Drink',
    'Empowered Shock Vortex',
    'Fade',
    'Fear Ward',
    'Fish Feast',
    'Flask of the Frost Wyrm',
    'Frostforged Sage',
    'Frozen Throne Teleport',
    'Gas Variable',
    'Hearthstone',
    'Hymn of Hope',
    'Hyperspeed Acceleration',
    'Inner Fire',
    'Instability',
    'Levitate',
    'Mass Dispel',
    'Mind Blast',
    'Mind Sear',
    'Nitro Boosts',
    'Ooze Variable',
    'Oratory of the Damned Teleport',
    'Pact of the Darkfallen',
    'Pain and Suffering',
    'Plague Sickness',
    'Prayer of Fortitude',
    'Prayer of Shadow Protection',
    'Prayer of Spirit',
    'Shadowfiend',
    'Prayer of Mending',
    "Precious's Ribbon",
    'Rampart of Skulls Teleport',
    'Resurrection',
    'Rocket Burst',
    'Rocket Pack',
    'Sated',
    "Sindragosa's Lair Teleport",
    "Siphoned Power",
    "Sulfuron Slammer",
    "Twilight Flames",
    "Upper Spire Teleport",
    "Vile Gas",
    "Well Fed",
    "Wild Magic",
    "Wormhole",
    "Bloodbolt Splash",
    "Blood Mirror",
    "Impale",
    "Interrupt",
    "Lightweave",
    "Recently Infected",
    "Shadow Prison",
    "Vampiric Bite",
    "Ritual of Summoning",
    "Inoculated",
    "Dazed",
    "Deathbringer's Rise Teleport",
    "Dash",
    "Cyclone",
    "Chilled to the Bone",
    "Blighted Spores",
    "Essence of the Blood Queen",
    "Jeeves",
    "MOLL-E",
    "Lay on Hands",
    "Gnomish Battle Chicken",
    "Global Thermal Sapper Charge",
    "Frostforged Champion",
    "Formidable",
    "Forbearance",
    "Flask of Endless Rage",
    "Parachute",
    "Ogre Pinata",
    "Piercing Twilight",
    "Mutated Plague",
    "Flask of Stoneblood",
    "Indestructible",
    # "Remove Curse",
}

SPELLS = {
    "death-knight": {
        "Hysteria": 1,
        "Vampiric Blood": 1,
        "Mark of Blood": 1,
        "Rune Tap": 1,
        "Bloody Vengeance": 1,
        "Blood Armor": 1,

        "Frost Strike": 2,
        "Unbreakable Armor": 2,
        "Hungering Cold": 2,
        "Howling Blast": 2,
        "Acclimation": 2,
        
        "Summon Gargoyle": 3,
        "Scourge Strike": 3,
        "Anti-Magic Zone": 3,
        "Wandering Plague": 3,
        "Ebon Plague": 3,
        "Desolation": 3,
    },
    "druid": {
        "Earth and Moon": 1,
        "Eclipse (Lunar)": 1,
        "Eclipse (Solar)": 1,
        "Force of Nature": 1,
        "Insect Swarm": 1,
        "Languish": 1,
        "Omen of Doom": 1,
        "Starfall": 1,
        "Typhoon": 1,

        "Tiger's Fury": 2,
        "Swipe (Cat)": 2,
        "Shred": 2,
        "Savage Roar": 2,
        "Savage Defense": 2,
        "Rip": 2,
        "Rake": 2,
        "Mangle (Cat)": 2,
        "Maim": 2,
        "King of the Jungle": 2,
        "Fury": 2,
        "Furor": 2,
        "Ferocious Bite": 2,
        "Feral Charge - Cat": 2,
        "Faerie Fire (Feral)": 2,
        "Claw": 2,
        "Berserk": 2,

        "Wild Growth": 3,
        "Revitalize": 3,
        "Tree of Life": 3,
        "Swiftmend": 3,
        "Living Seed": 3,
        "Tree of Life": 3,
    },
    "hunter": {
        "Bestial Wrath": 1,
        "Intimidation": 1,
        "Chimera Shot": 2,
        "Explosive Shot": 3,
    },
    "mage": {
        "Arcane Barrage": 1,
        "Arcane Power": 1,
        "Living Bomb": 2,
        "Combustion": 2,
        "Hot Streak": 2,
        "Cold Snap": 3,
        "Winter's Chill": 3,
        "Summon Water Elemental": 3,
        "Deep Freeze": 3,
    },
    "paladin": {
        "Beacon of Light": 1,
        "Holy Shock": 1,
        "Infusion of Light": 1,
        "Divine Illumination": 1,

        "Ardent Defender": 2,
        "Divine Guardian": 2,
        "Hammer of the Righteous": 2,
        "Avenger's Shield": 2,
        "Redoubt": 2,
        "Holy Shield": 2,
        "Blessing of Sanctuary": 2,
        "Greater Blessing of Sanctuary": 2,
        "Deliverance": 2,
        
        "Seal of Command": 3,
        "The Art of War": 3,
        "Crusader Strike": 3,
        "Divine Storm": 3,
        "Repentance": 3,
    },
    
    "priest": {
        "Renewed Hope": 1,
        "Rapture": 1,
        "Penance": 1,
        "Divine Aegis": 1,
        "Borrowed Time": 1,
        "Inspiration": 1,
        
        "Serendipity": 2,
        "Empowered Renew": 2,
        "Holy Concentration": 2,
        "Circle of Healing": 2,
        "Guardian Spirit": 2,
        # "Blessed Healing": 2,

        "Vampiric Touch": 3,
        "Improved Devouring Plague": 3,
        "Improved Spirit Tap": 3,
        "Mind Flay": 3,
        "Misery": 3,
        "Replenishment": 3,
        "Shadowy Insight": 3,
        "Vampiric Embrace": 3,
        "Dispersion": 3,
        "Shadowform": 3,
    },
    
    "rogue": {
        "Envenom": 1,
        "Mutilate": 1,
        "Cold Blood": 1,
        "Sinister Strike": 2,
        "Adrenaline Rush": 2,
        "Blade Flurry": 2,
        "Killing Spree": 2,
        "Shadow Dance": 3,
        "Shadowstep": 3,
        "Premeditation": 3,
        "Preparation": 3,
    },

    "shaman": {
        "Totem of Wrath": 1,
        "Thunderstorm": 1,
        "Elemental Mastery": 1,
        "Elemental Oath": 1,
        "Elemental Focus": 1,

        "Lava Lash": 2,
        "Feral Spirit": 2,
        "Shamanistic Rage": 2,
        "Stormstrike": 2,
        "Elemental Rage": 2,

        "Cleanse Spirit": 3,
        "Ancestral Awakening": 3,
        "Earth Shield": 3,
        "Tidal Waves": 3,
        "Ancestral Awakening": 3,
        "Riptide": 3,
        "Mana Tide Totem": 3,
        "Nature's Swiftness": 3,
    },
    
    "warlock": {
        "Haunt": 1,
        "Unstable Affliction": 1,
        "Eradication": 1,
        "Molten Core": 2,
        "Metamorphosis": 2,
        "Decimation": 2,
        "Demonic Empowerment": 2,
        "Chaos Bolt": 3,
        "Shadowfury": 3,
        "Conflagrate": 3,
        "Devastation": 3,
    },

    "warrior": {
        "Bladestorm": 1,
        "Mortal Strike": 1,
        "Sweeping Strikes": 1,
        "Endless Rage": 1,
        "Rampage": 2,
        "Bloodthirst": 2,
        "Death Wish": 2,
        "Shockwave": 3,
        "Devastate": 3,
        "Vigilance": 3,
        "Concussion Blow": 3,
    },
}

def classes_gen(logs: list[str], players):
    players_set = set(players)
    for line in logs:
        line_split = line.split(',', 8)
        if line_split[2] not in players_set:
            continue
        try:
            if line_split[7] not in SPELL_BOOK:
                continue
        except IndexError:
            continue

        players_set.remove(line_split[2])
        yield line_split[2], line_split[7]
        if not players_set:
            break
    
    if players_set:
        # print(players_set)
        logging.debug(f'player_class classes_gen {players_set} {logs[0][:100]}')

@constants.running_time
def get_classes(logs: list[str], players: dict[str, str]):
    classes = {
        sGUID: CLASSES[SPELL_BOOK[spellName]]
        for sGUID, spellName in classes_gen(logs, players)
    }
    return dict(sorted(classes.items()))

def specs_gen(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    # players_set = set(players)
    # for guid in players:
    #     # if guid in classes:
    #     print(classes[guid], SPELLS[classes[guid]])
    class_spells = {guid: SPELLS[classes[guid]] for guid in players if guid in classes}
    for line in logs:
        line_split = line.split(',', 8)
        if line_split[2] not in class_spells:
            continue
        try:
            if line_split[7] not in class_spells[line_split[2]]:
                continue
        except IndexError:
            continue
        guid, spell_name = line_split[2], line_split[7]
        yield guid, class_spells[guid][spell_name]
        class_spells.pop(guid, None)
        # players_set.remove(guid)
        if not class_spells:
            break

def specs_gen2(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    players_set = set(players)
    class_spells = {guid: SPELLS[classes[guid]] for guid in players_set}
    for n, line in enumerate(logs):
        _line = line.split(',', 8)
        if _line[2] not in players_set:
            continue
        try:
            if _line[7] not in class_spells[_line[2]]:
                continue
        except IndexError:
            continue
        yield _line[2], class_spells[_line[2]][_line[7]]
        players_set.remove(_line[2])
        print(n, line)
        print(players_set)
        if not players_set:
            break

@constants.running_time
def get_specs_guids(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    specs = {guid: 0 for guid in players}
    for guid, spec_index in specs_gen(logs, players, classes):
        specs[guid] = spec_index
    return specs

def get_spec_info(player_class, spec_index=0):
    classi = CLASSES.index(player_class)
    return SPECS_LIST[classi*4+spec_index]

@constants.running_time
def get_specs(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    specs = get_specs_guids(logs, players, classes)
    
    new_data: dict[str, tuple[str, str]] = {}
    for guid, spec_index in specs.items():
        # classi = CLASSES.index()
        player_class = classes[guid]
        player_name = players[guid]
        # new_data[player_name] = SPEC_LIST[classi*4+spec_index]
        new_data[player_name] = get_spec_info(player_class, spec_index)
    
    return new_data

@constants.running_time
def get_specs_no_names(logs: list[str], players: dict[str, str], classes: dict[str, str]):
    specs = get_specs_guids(logs, players, classes)
    
    new_data: dict[str, tuple[str, str]] = {}
    for guid, spec_index in specs.items():
        player_class = classes[guid]
        classi = CLASSES.index(player_class)
        new_data[guid] = classi*4+spec_index
    
    return new_data


def test_class(name):
    print(name)
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    players = report.get_players_guids()
    q = get_classes(logs, players)
    print(q)
    # sdname = f'./LogsDir/{name}/SPELLS_DATA'
    # constants.save_pickle(sdname, q)

def test_spec(name):
    print(name)
    report = logs_main.THE_LOGS(name)
    enc_data = report.get_enc_data()
    # boss = "Lady Deathwhisper"
    # boss = "Professor Putricide"
    # logs = report.get_logs()
    guids = report.get_all_guids()
    boss = "The Lich King"
    s, f = enc_data[boss][-2]
    logs = report.get_logs(s, f)
    dmg = dmg_heals.parse_only_dmg(logs)
    # dmg = dmg_heals2.add_pets(dmg, guids)
    print(dmg)
    players = {x for x in dmg if x.startswith('0x0')}
    print(players)
    classes = report.get_classes()
    q = get_specs(logs, players, classes)
    print(q)
    players = report.get_players_guids()
    for guid, spec_data in q.items():
        print(f"{players[guid]:<12} {spec_data[0]}")
    # sdname = f'./LogsDir/{name}/SPELLS_DATA'
    # constants.save_pickle(sdname, q)

def __redo(name):
    print(name)
    report = logs_main.THE_LOGS(name)
    logs = report.get_logs()
    players = report.get_players_guids()
    classes = get_classes(logs, players)
    pth = report.relative_path("CLASSES_DATA")
    constants.json_write(pth, classes)

def __redo_wrapped(name):
    try:
        __redo(name)
    except Exception:
        logging.exception(f'player_class __redo {name}')

if __name__ == '__main__':
    names = [
        # '21-12-26--16-44--Imnotadk',
        '21-08-16--18-19--Napnap',
    ]
    for name in names:
        __redo_wrapped(name)
    # constants.redo_data(__redo_wrapped)

