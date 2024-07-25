const LOW_GS_MULT = [1.33, 1, 0.75, 0.42, 1.66];
const SLOT_TYPES = [
  0, 2, 1, 2, 0, null, null, 2, 
  1, 1, 0, 1, 2, 2, 2, 2, 0, 0, 3];
const LEGENDARY = {
  49623: 1433,
  46017:  571,
};
const ILVL_TO_GS = {
  284: [551, 413, 310, 174, 1103],
  277: [531, 398, 298, 168, 1062],
  272: [  0,   0, 290,   0,    0],
  271: [514, 385, 289, 162, 1028],
  270: [511, 383,   0, 161,    0],
  268: [  0,   0, 284,   0,    0],
  264: [494, 370, 278, 156,  988],
  259: [  0,   0, 269,   0,    0],
  258: [477, 357, 268, 150,  954],
  251: [457, 342, 257, 144,  914],
  245: [439, 329, 247, 139,  879],
  239: [422, 316, 237, 133,  845],
  232: [402, 301, 226, 127,  805],
  226: [385, 289, 216, 121,  770],
  219: [365, 274, 205, 115,  730],
  213: [348, 261, 195, 110,  696],
  200: [310, 233, 174,  98,  621],
};

function is_two_hand(type) {
  return type == "Two-Hand" || type == "Two Hand";
}

function get_gs(inv_slot, item_data, item_id) {
  if (!item_data) return 0;

  let inv_type = SLOT_TYPES[inv_slot];
  if (inv_type == null) return 0;

  if (LEGENDARY[item_id]) return LEGENDARY[item_id];

  if (is_two_hand(item_data.slot)) inv_type = 4;

  if (ILVL_TO_GS[item_data.ilvl]) return ILVL_TO_GS[item_data.ilvl][inv_type];

  return ILVL_TO_GS["200"][inv_type] * LOW_GS_MULT[inv_type];
}

const QUALITY_COLOR = [
  "poor",
  "common",
  "uncommon",
  "rare",
  "epic",
  "legendary",
  "artifact",
  "heirloom",
];
const ENCHANTABLE = [
  "Head",
  "Shoulder",
  "Chest",
  "Legs",
  "Hands",
  "Feet",
  "Wrist",
  "Back",
  "Main Hand",
  "Off Hand",
  "One-Hand",
  "Two-Hand",
];
const STATS_ORDER = {
  ap: {
    main: [
      "attack power",
      "critical strike rating",
      "haste rating",
      "hit rating",
      "armor penetration rating",
      "expertise rating",
      "strength",
      "agility",
      "intellect",
    ],
    other: [
      "armor",
      "stamina",
      "resilience rating",
      "defense rating",
      "dodge rating",
      "parry rating",
      "shield block",
      "spell power",
      "spell penetration",
      "spirit",
      "mp5",
    ],
  },
  caster: {
    main: [
      "spell power",
      "critical strike rating",
      "haste rating",
      "hit rating",
      "intellect",
      "spirit",
    ],
    other: [
      "armor",
      "stamina",
      "resilience rating",
      "spell penetration",
      "mp5",
      "strength",
      "agility",
      "defense rating",
      "dodge rating",
      "parry rating",
      "shield block",
      "attack power",
      "armor penetration rating",
      "expertise rating",
    ],
  },
};
const DEFAULT_GEM_DATA = {"socket": [0, 0, 0], 'color_hex': "ffffff"};
const GEM_DATA = {
  "red": {
    "socket": [1, 0, 0],
    "color_hex": "ff0000",
    "unique": ["blood garnet", "bloodstone", "cardinal ruby", "kailee's rose", "living ruby", "scarlet ruby", "test living ruby"],
    "prefix": ["bold", "bright", "crimson", "delicate", "don", "flashing", "fractured", "mighty", "precise", "runed", "stark", "subtle", "teardrop"]
  },
  "yellow": {
    "socket": [0, 1, 0],
    "color_hex": "edc600",
    "unique": ["autumn's glow", "blood of amber", "dawnstone", "facet of eternity", "golden draenite", "kharmaa's grace", "king's amber", "lionseye", "stone of blades", "sublime mystic dawnstone", "sun crystal"],
    "prefix": ["brilliant", "gleaming", "great", "mystic", "quick", "rigid", "smooth", "thick"]
  },
  "blue": {
    "socket": [0, 0, 1],
    "color_hex": "4444ff",
    "unique": ["azure moonstone", "chalcedony", "charmed amani jewel", "empyrean sapphire", "eye of the sea", "falling star", "majestic zircon", "sky sapphire", "star of elune"],
    "prefix": ["lustrous", "solid", "sparkling", "stormy"]
  },
  "orange": {
    "socket": [1, 1, 0],
    "color_hex": "ff8800",
    "unique": ["ametrine", "assassin's fire opal", "beaming fire opal", "enscribed fire opal", "flame spessarite", "glistening fire opal", "huge citrine", "infused fire opal", "iridescent fire opal", "monarch topaz", "mysterious fire opal", "nimble fire opal", "noble topaz", "pyrestone", "shining fire opal", "splendid fire opal"],
    "prefix": ["accurate", "champion's", "deadly", "deft", "durable", "empowered", "etched", "fierce", "glimmering", "glinting", "inscribed", "lucent", "luminous", "potent", "pristine", "reckless", "resolute", "resplendent", "stalwart", "stark", "unstable", "veiled", "wicked"]
  },
  "green": {
    "socket": [0, 1, 1],
    "color_hex": "00aa55",
    "unique": ["dark jade", "deep peridot", "effulgent chrysoprase", "eye of zul", "forest emerald", "polished chrysoprase", "rune covered chrysoprase", "seaspray emerald", "talasite", "test dazzling talasite", "unstable talasite"],
    "prefix": ["barbed", "dazzling", "enduring", "energized", "forceful", "intricate", "jagged", "lambent", "misty", "notched", "opaque", "radiant", "seer's", "shattered", "shining", "steady", "sundered", "tense", "timeless", "turbid", "vivid"]
  },
  "purple": {
    "socket": [1, 0, 1],
    "color_hex": "6600bb",
    "unique": ["blessed tanzanite", "brutal tanzanite", "dreadstone", "fluorescent tanzanite", "imperial tanzanite", "nightseye", "pulsing amethyst", "qa test blank purple gem", "shadowsong amethyst", "soothing amethyst", "twilight opal"],
    "prefix": ["balanced", "defender's", "glowing", "guardian's", "infused", "mysterious", "puissant", "purified", "regal", "royal", "shadow", "shifting", "sovereign", "tenuous"]
  },
  "prismatic": {
    "socket": [1, 1, 1],
    "color_hex": "a335ee",
    "unique": ["chromatic sphere", "enchanted pearl", "enchanted tear", "infinite sphere", "nightmare tear", "prismatic sphere", "soulbound test gem", "void sphere"],
    "prefix": []
  },
  "meta": {
    "socket": [0, 0, 0],
    "color_hex": "6666ff",
    "unique": ["austere earthsiege diamond", "beaming earthsiege diamond", "brutal earthstorm diamond", "earthsiege diamond", "earthstorm diamond", "effulgent skyflare diamond", "imbued unstable diamond", "invigorating earthsiege diamond", "mystical skyfire diamond", "potent unstable diamond", "revitalizing skyflare diamond", "skyfire diamond", "skyflare diamond", "tenacious earthstorm diamond"],
    "prefix": ["bracing", "chaotic", "destructive", "ember", "enigmatic", "eternal", "forlorn", "impassive", "insightful", "persistent", "powerful", "relentless", "swift", "thundering", "tireless", "trenchant"]
  }
}

function find_gem_data_by_name(gem_name) {
  gem_name = gem_name.toLowerCase().replace("perfect ", "");
  const _values = Object.values(GEM_DATA);
  for (const color_data of _values) {
    if (color_data.unique.includes(gem_name)) {
      return color_data;
    }
  }
  const prefix = gem_name.split(' ', 1)[0];
  for (const color_data of _values) {
    if (color_data.prefix.includes(prefix)) {
      return color_data;
    }
  }
  return DEFAULT_GEM_DATA;
}

function split_space_once(string) {
  const space_at = string.indexOf(' ');
  const value = string.substring(0, space_at);
  const stat = string.substring(space_at + 1);
  return [value, stat];
}

function slot_item_changed(slot_element, item_id) {
  const current_item_id = slot_element.getAttribute("data-item-id");
  return current_item_id != item_id;
}

function find_set_name(sets, item_id) {
  item_id = parseInt(item_id);
  for (const set_name in sets) {
    if (sets[set_name].items.includes(item_id)) {
      return set_name;
    }
  }
}

function object_default_int(_default=0) {
  const handler = {
    get: function(target, name) {
      return target[name] ?? _default;
    }
  };
  const o = {};
  return new Proxy(o, handler);
}

function find_equipped_sets(gear_ids, sets) {
  const equipped_sets = object_default_int();
  gear_ids.forEach(item_id => {
    const set_name = find_set_name(sets, item_id);
    if (!set_name) return;
    equipped_sets[set_name] += 1;
  });
  return equipped_sets;
}

export {
  QUALITY_COLOR,
  ENCHANTABLE,
  STATS_ORDER,
  DEFAULT_GEM_DATA,
  GEM_DATA,
  is_two_hand,
  get_gs,
  find_gem_data_by_name,
  split_space_once,
  slot_item_changed,
  find_set_name,
  object_default_int,
  find_equipped_sets,
}
