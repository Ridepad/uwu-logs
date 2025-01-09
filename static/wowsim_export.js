import { wow_sim_template, spec_overrides } from "./proto/template.js";
const TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE";
const WOWSIM_URL = "https://wowsims.github.io/wotlk/";
const GLYPHS_JSON_FILE = "/static/glyphs.json";
const GEM_TO_ENCH_JSON_FILE = "/static/gem_to_ench.json";
const MAX_TALENTS_TREE_LEN = {
  Deathknight: [28, 29, 31],
  Druid: [28, 30, 27],
  Hunter: [26, 27, 28],
  Mage: [30, 28, 28],
  Paladin: [26, 26, 26],
  Priest: [28, 27, 27],
  Rogue: [27, 28, 28],
  Shaman: [25, 29, 26],
  Warlock: [28, 27, 26],
  Warrior: [31, 27, 27],
};
const SIM_PROFESSIONS = {
  ProfessionUnknown: 0,
  Alchemy: 1,
  Blacksmithing: 2,
  Enchanting: 3,
  Engineering: 4,
  Herbalism: 5,
  Inscription: 6,
  Jewelcrafting: 7,
  Leatherworking: 8,
  Mining: 9,
  Skinning: 10,
  Tailoring: 11,
};
const SIM_CLASS = {
  Unknown: 0,
  Druid: 1,
  Hunter: 2,
  Mage: 3,
  Paladin: 4,
  Priest: 5,
  Rogue: 6,
  Shaman: 7,
  Warlock: 8,
  Warrior: 9,
  Deathknight: 10,
};
const SIM_FACTION = {
  Unknown: 0,
  Alliance: 1,
  Horde: 2,
};
const SIM_RACE = {
  Unknown: 0,
  BloodElf: 1,
  Draenei: 2,
  Dwarf: 3,
  Gnome: 4,
  Human: 5,
  NightElf: 6,
  Orc: 7,
  Tauren: 8,
  Troll: 9,
  Undead: 10,
};
const SIM_SPEC = {
  BalanceDruid: 0,
  FeralDruid: 12,
  FeralTankDruid: 14,
  ElementalShaman: 1,
  EnhancementShaman: 9,
  Hunter: 8,
  Mage: 2,
  ProtectionPaladin: 13,
  RetributionPaladin: 3,
  Rogue: 7,
  HealingPriest: 17,
  ShadowPriest: 4,
  Warlock: 5,
  Warrior: 6,
  ProtectionWarrior: 11,
  Deathknight: 15,
  TankDeathknight: 16,
};
const SPEC_GEMS = {
  tank: [41380, 44088, 41397, 41396],
  apDps: [41398, 41400, 41385, 44087, 41381, 44076, 41339, 41385],
  manaDps: [41395, 41389, 41285, 34220, 41375, 41378],
  heal: [41333, 41401, 41376],
};


function is_spec(socketed_gems, spec_gems) {
  return socketed_gems.filter((value) => spec_gems.includes(value)).length > 0;
}

function is_tank(gems) {
  return is_spec(gems, SPEC_GEMS.tank);
}

function is_heal(gems) {
  return is_spec(gems, SPEC_GEMS.heal);
}

function is_apDps(gems) {
  return is_spec(gems, SPEC_GEMS.apDps);
}

const CLASS_SPECS = {
  find_spec(set_class, sim_gear, set_spec) {
    set_spec = set_spec.toLowerCase();
    const f = this[set_class];
    if (!f) return "";
    const spec = f(set_spec, sim_gear[0].gems);
    return spec ?? "";
  },
  default: () => "",
  Druid: (spec_name, gems) => {
    if (spec_name === "balance") return "balance";
    if (is_tank(gems)) return "feral_tank";
    if (is_apDps(gems)) return "feral";
    if (spec_name === "feral combat") return "feral";
    return "balance";
  },
  Shaman: (spec_name, gems) => {
    if (spec_name === "enhancement") return "enhancement";
    if (spec_name === "elemental") return "elemental";
    if (is_apDps(gems)) return "enhancement";
    return "elemental";
  },
  Paladin: (spec_name, gems) => {
    if (spec_name === "protection") return "protection";
    if (spec_name === "retribution") return "retribution";
    if (is_tank(gems)) return "protection";
    return "retribution";
  },
  Priest: (spec_name, gems) => {
    if (spec_name === "shadow") return "shadow";
    if (is_heal(gems)) return "healing";
    return "shadow";
  },
  Warrior: (spec_name, gems) => {
    if (spec_name === "protection") return "protection";
    if (is_tank(gems)) return "protection";
  },
  Deathknight: (spec_name, gems) => {
    if (is_tank(gems)) return "tank";
  },
}

function async_map(array, callback) {
  const mapped = array.map(async element => await callback(element));
  return Promise.all(mapped);
}

const glyphs_fetch = fetch(GLYPHS_JSON_FILE)
  .then((response) => response.json())
  .catch((err) => {
    console.error(`Error loading file ${GLYPHS_JSON_FILE}:`, err);
    return {};
  });
async function get_class_glyphs(char_class) {
  const data = await glyphs_fetch;
  return data[char_class];
}

const gems_fetch = fetch(GEM_TO_ENCH_JSON_FILE)
  .then((response) => response.json())
  .then((data) => {
    return Object.fromEntries(Object.entries(data).map(([key, value]) => [parseInt(value), parseInt(key)]));
  })
  .catch((err) => {
    console.error(`Error loading file ${GEM_TO_ENCH_JSON_FILE}:`, err);
    return {};
  });
async function get_gem_ench_id(gem_id) {
  if (gem_id <= 0) return 0;
  const gem_data = await gems_fetch;
  return gem_data[parseInt(gem_id)];
}
function map_gems(gems) {
  gems = gems.filter(gem_id => gem_id > 0);
  return async_map(gems, get_gem_ench_id);
}

function to_title(string) {
  return string.charAt(0).toUpperCase() + string.substr(1).toLowerCase();
}
async function convert_to_link(set, player_name, spec_name, talents_string) {
  const player_class = to_title(set.class).replace(" ", "");
  const player_class_lower = player_class.toLowerCase();
  
  const data = structuredClone(wow_sim_template);
  data.player.name = player_name;
  data.player.class = SIM_CLASS[player_class];
  data.player.race = SIM_RACE[set.race];
  data.player.talentsString = convert_talents(player_class, talents_string);

  const professions = Array.isArray(set.profs) ? set.profs : Object.entries(set.profs);
  data.player.profession1 = professions[0] ? SIM_PROFESSIONS[professions[0][0]] : 0;
  data.player.profession2 = professions[1] ? SIM_PROFESSIONS[professions[1][0]] : 0;
  
  const sim_gear = await transform_gear_data(set.gear_data);
  data.player.equipment.items = sim_gear;

  const spec = CLASS_SPECS.find_spec(player_class, sim_gear, spec_name);
  
  const spec_override_key = spec.length ? spec + player_class : player_class_lower;
  const spec_override = spec_overrides[spec_override_key];
  merge_deep(data, spec_override);

  const glyphs = await convert_glyphs(player_class, talents_string);
  if (Object.keys(glyphs).length > 0) {
    data.player.glyphs = glyphs;
  } else if (spec_override.player.glyphsOverride !== undefined) {
    data.player.glyphs = spec_override.player.glyphsOverride[spec_name];
  }

  const separator = spec.length ? "_" : "";
  const spec_path = spec + separator + player_class_lower;
  return deflate(data, spec_path);
}

//merges target object with sources into one object
function merge_deep(target, ...sources) {
  if (!sources.length) return target;
  const source = sources.shift();

  if (is_object(target) && is_object(source)) {
    for (const key in source) {
      if (is_object(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        merge_deep(target[key], source[key]);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }

  return merge_deep(target, ...sources);
}
function is_object(item) {
  return item && typeof item === "object" && !Array.isArray(item);
}
//transforms gem enchant ids to gem items
async function transform_item_slot(slot) {
  if (!slot.item) return {};
  
  const transformed_item = { id: parseInt(slot.item) };
  if (slot.ench) transformed_item.enchant = parseInt(slot.ench);
  // Filter out "0" gems and convert to integers
  if (slot.gems) transformed_item.gems = await map_gems(slot.gems);
  return transformed_item;
}
function transform_gear_data(items) {
  return async_map(items, transform_item_slot);
}
//uses google's protocol buffers to encode structured and typed data into link
async function deflate(data, spec) {
  return new Promise((resolve, reject) => {
    protobuf.load("./static/proto/wowsim_pb.json", function (err, root) {
      if (err) {
        reject(err);
        return;
      }

      //Obtain a message type
      const IndividualSimSettings = root.lookupType("proto.IndividualSimSettings");

      // Verify the payload if necessary (i.e. when possibly incomplete or invalid)
      const errorMessage = IndividualSimSettings.verify(data);
      if (errorMessage) {
        reject(new Error("Invalid data: " + errorMessage));
        return;
      }

      // Step 3: Encode the data
      const message = IndividualSimSettings.create(data); // Create a message
      const binaryData = IndividualSimSettings.encode(message).finish(); // Encode to binary

      let deflate = pako.deflate(binaryData);
      const encoded = window.btoa(String.fromCharCode(...deflate));
      const linkUrl = new URL(WOWSIM_URL + spec + "/?i=gtm#");
      linkUrl.hash = encoded;

      resolve(linkUrl);
    });
  });
}

// test talent strings
// 0tMbuiIRcdIVuRuZbxczb            58/0/13
// hih0qsdItGfzAo0xxI               55/16/0
// IZcG0hkAbihsg0AoE0MVo:Tbn0Vz     0/53/18
//converts talent string, with or without glyph part, eg:sZV0tAduMusIufdxfMzbM or cxbZ0eibRhzGIkguAox00b:Afi0Mz
function convert_talents(char_class, char_talents_string) {
  if (!char_talents_string) return;
  const trees = convert_talents_to_levels(char_class, char_talents_string);
  const trees_joined = [];
  for (let i = 0; i < 3; i++) {
    const tree_talents_amount = MAX_TALENTS_TREE_LEN[char_class][i];
    const tree_joined_string = trees[i].slice(0, tree_talents_amount).join("");
    const padded_to_tree_size = tree_joined_string.padEnd(tree_talents_amount, "0");
    trees_joined.push(padded_to_tree_size);
  }
  return trees_joined.join("-");
}
function convert_talents_to_levels(char_class, char_talents_string) {
  const tree_max_nodes = MAX_TALENTS_TREE_LEN[char_class];
  const trees = [[], [], []];
  let current_tree = 0;

  for (let i = 1; i < char_talents_string.length; i++) {
    const char = char_talents_string[i];
    
    if (char == ":") break;
    if (trees[current_tree].length >= tree_max_nodes[current_tree]) {
      current_tree++
    }
    if (char == "Z") {
      current_tree++
      continue;
    }

    const talent_index = TALENTS_ENCODE_STR.indexOf(char);
    const talent1_level = Math.floor(talent_index / 6);
    const talent2_level = talent_index % 6;
    trees[current_tree].push(talent1_level);
    trees[current_tree].push(talent2_level);
  }
  return trees;
}

function split_glyphs_string(glyph_string) {
  glyph_string = glyph_string.slice(0, 6);
  if (glyph_string.includes("Z")) {
    return glyph_string.split("Z");
  }
  return [glyph_string.slice(0, 3), glyph_string.slice(3, 6)];
}
function split_glyphs(glyph_string) {
  const [major, minor] = split_glyphs_string(glyph_string);
  return {
    major: major,
    minor: minor,
  };
}
async function convert_glyphs(char_class, char_talents_string) {
  if (!char_talents_string) return {};
  
  const glyph_string = char_talents_string.split(":")[1];
  if (!glyph_string) return {};

  const class_glyphs = await get_class_glyphs(char_class);
  if (!class_glyphs) return {};
  
  const char_glyphs = {};
  const glyphs_split_by_type = split_glyphs(glyph_string);
  for (const glyph_type in glyphs_split_by_type) {
    const glyph_spell_ids = Object.keys(class_glyphs[glyph_type]);
    const glyph_string_split = glyphs_split_by_type[glyph_type];
    for (let i = 0; i < glyph_string_split.length; i++) {
      const glyph_char = glyph_string_split[i];
      const glyph_index = TALENTS_ENCODE_STR.indexOf(glyph_char);
      const glyph_key = `${glyph_type}${i+1}`;
      char_glyphs[glyph_key] = parseInt(glyph_spell_ids[glyph_index]);
    }
  }

  return char_glyphs;
}
// test glyph string with missing glyphs
// convert_glyphs("Rogue", "0xcZb:TpZVmz")
// convert_glyphs("Rogue", "0xcZb:TZVmz")
// convert_glyphs("Rogue", "0xcZb:ZVmz")

// can be used to test export strings
function inflate(base64EncodedData) {
  protobuf.load("./static/proto/wowsim_pb.json", function (err, root) {
    const base64 = window.atob(base64EncodedData);
    const codes = [];

    for (let i = 0; i < base64.length; i++) {
      codes.push(base64.charCodeAt(i));
    }

    const inflate = pako.inflate(new Uint8Array(codes));

    // Step 3: Get the relevant message type (Player)
    const IndividualSimSettings = root.lookupType("proto.IndividualSimSettings");

    // Step 4: Decode the binary data
    const decodedMessage1 = IndividualSimSettings.decode(inflate);

    // Step 5: Convert to a plain JavaScript object
    const plainObject = IndividualSimSettings.toObject(decodedMessage1);
    console.log("Decoded CHAR:", plainObject);
  });
}
export { convert_to_link };
