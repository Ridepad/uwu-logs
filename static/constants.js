const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const CLASSES = ["Death Knight", "Druid", "Hunter", "Mage", "Paladin", "Priest", "Rogue", "Shaman", "Warlock", "Warrior"]
const AURAS_COLUMNS = ["ext", "self", "rekt", "cls"];

const BOSSES = {
  "Points": ["Points"],
  "Speedrun": ["Icecrown Citadel"],
  "Icecrown Citadel": [
    "The Lich King",
    "Lord Marrowgar", "Lady Deathwhisper", "Deathbringer Saurfang",
    "Festergut", "Rotface", "Professor Putricide",
    "Blood Prince Council", "Blood-Queen Lana'thel",
    "Valithria Dreamwalker",
    "Sindragosa"
  ],
  "The Ruby Sanctum": ["Halion", "Baltharus the Warborn", "Saviana Ragefire", "General Zarithrian"],
  "Trial of the Crusader": ["Anub'arak", "Northrend Beasts", "Lord Jaraxxus", "Faction Champions", "Twin Val'kyr"],
  "Vault of Archavon": ["Toravon the Ice Watcher", "Archavon the Stone Watcher", "Emalon the Storm Watcher", "Koralon the Flame Watcher"],
  "Onyxia's Lair": ["Onyxia"],
  "The Eye of Eternity": ["Malygos"],
  "The Obsidian Sanctum": ["Sartharion"],
  "Naxxramas": [
    "Anub'Rekhan", "Grand Widow Faerlina", "Maexxna",
    "Noth the Plaguebringer", "Heigan the Unclean", "Loatheb",
    "Patchwerk", "Grobbulus", "Gluth", "Thaddius",
    "Instructor Razuvious", "Gothik the Harvester", "The Four Horsemen",
    "Sapphiron", "Kel'Thuzad"
  ],
  "Ulduar": [
    "Ignis the Furnace Master", "Razorscale", "XT-002 Deconstructor",
    "Assembly of Iron", "Kologarn", "Auriaya", "Hodir", "Thorim", "Freya", "Mimiron",
    "General Vezax", "Yogg-Saron", "Algalon the Observer"
  ],
  "Magtheridon's Lair": ["Magtheridon"],
  "Karazhan": [
    "Servant Quarters", "Attumen the Huntsman", "Moroes",
    "Opera House", "Maiden of Virtue", "The Curator",
    "Chess Event", "Terestian Illhoof", "Shade of Aran",
    "Netherspite", "Nightbane", "Prince Malchezaar",
  ],
  "Gruul's Lair": [
    "High King Maulgar", "Gruul the Dragonkiller",
  ],
  "Serpentshrine Cavern": [
    "Hydross the Unstable", "The Lurker Below", "Leotheras the Blind",
    "Fathom-Lord Karathress", "Morogrim Tidewalker", "Lady Vashj",
  ],
  "The Eye": [
    "Al'ar", "Void Reaver", "High Astromancer Solarian", "Kael'thas Sunstrider",
  ],
  "Black Temple": [
    "High Warlord Naj'entus", "Supremus", "Shade of Akama", "Teron Gorefiend", "Gurtogg Bloodboil",
    "Reliquary of Souls", "Mother Shahraz", "The Illidari Council", "Illidan Stormrage",
  ],
  "Mount Hyjal": [
    "Rage Winterchill", "Anetheron", "Kaz'rogal", "Azgalor", "Archimonde",
  ],
  "Zul'Aman": [
    "Akil'zon", "Nalorakk", "Jan'alai", "Halazzi", "Hex Lord Malacrass", "Zul'jin",
  ],
  "Sunwell Plateau": [
    "Kalecgos", "Sathrovarr",
    "Brutallus",
    "Felmyst",
    "Alythess", "Sacrolash",
    "M'uru", "Entropius",
    "Kil'jaeden",
  ],
  "Ahn'Qiraj": [
    "The Prophet Skeram", "Battleguard Sartura", "Fankriss the Unyielding",
    "Princess Huhuran", "Twin Emperors", "C'Thun",
    "Bug Trio", "Viscidus", "Ouro",
  ],
  "Molten Core": [
    "Lucifron", "Magmadar", "Gehennas", "Garr", "Shazzrah", "Baron Geddon",
    "Golemagg the Incinerator", "Sulfuron Harbinger", "Majordomo Executus", "Ragnaros",
  ],
  "Blackwing Lair": [
    "Razorgore the Untamed", "Vaelastrasz the Corrupt", "Broodlord Lashlayer",
    "Firemaw", "Ebonroc", "Flamegor", "Chromaggus", "Nefarian",
  ],
};

const SPECS = [
  ["Death Knight", "class_deathknight", "death-knight"],
  ["Blood", "spell_deathknight_bloodpresence", "death-knight"],
  ["Frost", "spell_deathknight_frostpresence", "death-knight"],
  ["Unholy", "spell_deathknight_unholypresence", "death-knight"],
  ["Druid", "class_druid", "druid"],
  ["Balance", "spell_nature_starfall", "druid"],
  ["Feral Combat", "ability_racial_bearform", "druid"],
  ["Restoration", "spell_nature_healingtouch", "druid"],
  ["Hunter", "class_hunter", "hunter"],
  ["Beast Mastery", "ability_hunter_beasttaming", "hunter"],
  ["Marksmanship", "ability_marksmanship", "hunter"],
  ["Survival", "ability_hunter_swiftstrike", "hunter"],
  ["Mage", "class_mage", "mage"],
  ["Arcane", "spell_holy_magicalsentry", "mage"],
  ["Fire", "spell_fire_firebolt02", "mage"],
  ["Frost", "spell_frost_frostbolt02", "mage"],
  ["Paladin", "class_paladin", "paladin"],
  ["Holy", "spell_holy_holybolt", "paladin"],
  ["Protection", "spell_holy_devotionaura", "paladin"],
  ["Retribution", "spell_holy_auraoflight", "paladin"],
  ["Priest", "class_priest", "priest"],
  ["Discipline", "spell_holy_wordfortitude", "priest"],
  ["Holy", "spell_holy_guardianspirit", "priest"],
  ["Shadow", "spell_shadow_shadowwordpain", "priest"],
  ["Rogue", "class_rogue", "rogue"],
  ["Assassination", "ability_rogue_eviscerate", "rogue"],
  ["Combat", "ability_backstab", "rogue"],
  ["Subtlety", "ability_stealth", "rogue"],
  ["Shaman", "class_shaman", "shaman"],
  ["Elemental", "spell_nature_lightning", "shaman"],
  ["Enhancement", "spell_nature_lightningshield", "shaman"],
  ["Restoration", "spell_nature_magicimmunity", "shaman"],
  ["Warlock", "class_warlock", "warlock"],
  ["Affliction", "spell_shadow_deathcoil", "warlock"],
  ["Demonology", "spell_shadow_metamorphosis", "warlock"],
  ["Destruction", "spell_shadow_rainoffire", "warlock"],
  ["Warrior", "class_warrior", "warrior"],
  ["Arms", "ability_warrior_savageblow", "warrior"],
  ["Fury", "ability_warrior_innerrage", "warrior"],
  ["Protection", "ability_warrior_defensivestance", "warrior"]
]


const SPECS_SELECT_OPTIONS = {
  "Death Knight": ["Blood", "Frost", "Unholy"],
  "Druid": ["Balance", "Feral Combat", "Restoration"],
  "Hunter": ["Beast Mastery", "Marksmanship", "Survival"],
  "Mage": ["Arcane", "Fire", "Frost"],
  "Paladin": ["Holy", "Protection", "Retribution"],
  "Priest": ["Discipline", "Holy", "Shadow"],
  "Rogue": ["Assassination", "Combat", "Subtlety"],
  "Shaman": ["Elemental", "Enhancement", "Restoration"],
  "Warlock": ["Affliction", "Demonology", "Destruction"],
  "Warrior": ["Arms", "Fury", "Protection"]
}

export {
  BOSSES,
  CLASSES,
  SPECS,
  SPECS_SELECT_OPTIONS,
  AURAS_COLUMNS,
  MONTHS,
}
