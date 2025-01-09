import { wow_sim_template, spec_overrides } from "./proto/template.js";
const TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE";
const WOWSIM_URL = "https://wowsims.github.io/wotlk/";
const max_talents_tree_len = {
  "Death Knight": [28, 29, 31],
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

let glyphs = null;
let global_gems = null;
let sim_data = [];
let spec_path = [];

async function convert_to_link(i, e, name, set, talents) {
  if (!glyphs) {
    await fetch("/static/glyphs.json")
      .then((response) => response.json())
      .then((data) => {
        glyphs = data;
      })
      .catch((err) => console.error("Error loading file:", err));
  }
  if (!global_gems) {
    await fetch("/static/x_gem_to_ench.json")
      .then((response) => response.json())
      .then((data) => {
        global_gems = Object.fromEntries(Object.entries(data).map(([key, value]) => [parseInt(value), parseInt(key)]));
      })
      .catch((err) => console.error("Error loading file:", err));
  }
  sim_data[i] = structuredClone(wow_sim_template);

  sim_data[i].player.name = name;
  sim_data[i].player.class = SIM_CLASS[set.class];
  sim_data[i].player.race = SIM_RACE[set.race];
  sim_data[i].player.profession1 = SIM_PROFESSIONS[!set.profs[0] ? Object.keys(set.profs)[0] : set.profs[0][0]];
  sim_data[i].player.profession2 = SIM_PROFESSIONS[!set.profs[1] ? Object.keys(set.profs)[1] : set.profs[1][0]];

  let sim_gear = transform_gear_data(set.gear_data);
  sim_data[i].player.equipment["items"] = sim_gear;

  const spec = find_spec(set.class, sim_gear, set.specs[i][0]);
  console.log(spec);
  
  const spec_override = spec_overrides[spec.length ? spec + set.class : set.class.toLowerCase()];
  sim_data[i] = merge_deep(sim_data[i], spec_override);

  sim_data[i].player = {
    ...sim_data[i].player,
    ...convert_talents(set.class, talents),
  };

  if(Object.keys(sim_data[i].player.glyphs).length === 0 && spec_override.player.glyphsOverride !== undefined) {
    sim_data[i].player.glyphs = spec_override.player.glyphsOverride[set.specs[i][0]];
  }

  spec_path[i] = spec + (spec.length ? "_" : "") + set.class.toLowerCase();
  
  if (i == 0) {
    e.removeEventListener("click", handle_click_0);
    e.addEventListener("click", handle_click_0);
  } else if (i == 1) {
    e.removeEventListener("click", handle_click_1);
    e.addEventListener("click", handle_click_1);
  }
}
// handler for clicks
function handle_click_0(e) {
  deflate(e, sim_data[0], spec_path[0])
    .then((url) => window.open(url))
    .catch((err) => console.error(err));
}
function handle_click_1(e) {
  deflate(e, sim_data[1], spec_path[1])
    .then((url) => window.open(url))
    .catch((err) => console.error(err));
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
function transform_gear_data(gearData) {
  const transformed = gearData.map((gear) => {
    if (!gear.item) return {}; // Handle empty objects
    const transformed_item = { id: parseInt(gear.item) };
    if (gear.ench) transformed_item.enchant = parseInt(gear.ench);
    if (gear.gems) {
      // Filter out "0" gems and convert to integers
      transformed_item.gems = gear.gems.map((gem) => (gem > 0 ? global_gems[parseInt(gem)] : 0)).filter((gem) => gem !== 0);
    }
    return transformed_item;
  });
  return transformed;
}
//uses google's protocol buffers to encode structured and typed data into link
async function deflate(e, data, spec) {
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
//converts talent string, with or without glyph part, eg:sZV0tAduMusIufdxfMzbM or cxbZ0eibRhzGIkguAox00b:Afi0Mz
function convert_talents(char_class, char_talents) {
  let char_talents_string = char_talents;
  if (!char_talents_string) return;
  const trees = convert_talents_to_levels(char_class, char_talents_string);
  const trees_joined = [];
  for (let i = 0; i < 3; i++) {
    const max_length = max_talents_tree_len[char_class][i];
    const _joined = trees[i].slice(0, max_length).join("");
    trees_joined.push(_joined);
  }
  const trees_enc_sims = trees_joined.join("-");
  const glyphs_sims = convert_glyps(char_class, char_talents_string);
  
  if (Object.keys(glyphs_sims).length === 0) {    
    return {
      talentsString: trees_enc_sims,
    };
  }
  return {
    talentsString: trees_enc_sims,
    glyphs: glyphs_sims,
  };
}
function convert_talents_to_levels(char_class, char_talents_string) {
  const trees = [];
  let current_tree = [];
  let tree_count = 1;
  for (let i = 1; i < char_talents_string.length; i++) {
    const char = char_talents_string[i];
    // console.log(char, i , tree_count, max_talents_tree_len[char_class][trees.length]);
    if (char == ":") {
      for (let j = tree_count * 2; j < max_talents_tree_len[char_class][trees.length]; j++) {
        current_tree.push(0);
      }
      break;
    }
    if (
      char == "Z" ||
      tree_count * 2 > max_talents_tree_len[char_class][trees.length] - 1
    ) {
      tree_count = 0;
      trees.push(current_tree);
      for (let j = tree_count * 2; j < max_talents_tree_len[char_class][trees.length]; j++) {
        current_tree.push(0);
      }
      current_tree = [];
      if (char == "Z") continue;
    }
    const talent_index = TALENTS_ENCODE_STR.indexOf(char);
    const talent1_level = Math.floor(talent_index / 6);
    const talent2_level = talent_index % 6;
    current_tree.push(talent1_level);
    current_tree.push(talent2_level);
    tree_count++;
  }

  if (current_tree.length) {
    trees.push(current_tree);
  }
  while (trees.length < 3) {
    trees.push([]);
  }
  return trees;
}
function convert_glyps(char_class, char_talents_string) {
  const glyph_string = char_talents_string.split(":")[1];
  if (!glyph_string) return {};

  const class_glyphs = glyphs[char_class];
  const char_glyphs = {};
  for (let i = 0; i < glyph_string.length; i++) {
    const char = glyph_string[i];
    const glyph_index = TALENTS_ENCODE_STR.indexOf(char);
    const glyph_type = i < 3 ? "major" : "minor";

    char_glyphs[glyph_type + ((i % 3) + 1)] = parseInt(Object.keys(class_glyphs[glyph_type])[glyph_index]);
  }

  return char_glyphs;
}
// uses set_spec or meta gems to find spec
function find_spec(set_class, sim_gear, set_spec) {
  let spec = "";
  let intersec = [];
  switch (set_class) {
    case "Druid":
      if (set_spec.toLowerCase() === 'balance') {
        spec = "balance";
        break;
      }
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.tank.includes(value));
      if (intersec.length) {
        spec = "feral_tank";
        break;
      }
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.apDps.includes(value));
      if (intersec.length) {
        spec = "feral";
        break;
      }
      if (set_spec.toLowerCase() === 'feral combat') {
        spec = "feral";
        break;
      }
      spec = "balance";
      break;
    case "Shaman":
      if (["enhancement", "elemental"].includes(set_spec.toLowerCase())) {
        spec = set_spec.toLowerCase();  
        break;
      }
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.apDps.includes(value));
      if (intersec.length) {
        spec = "enhancement";
        break;
      }
      spec = "elemental";
      break;
    case "Paladin":
      if (["protection", "retribution"].includes(set_spec.toLowerCase())) {
        spec = set_spec.toLowerCase();  
        break;
      }
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.tank.includes(value));
      if (intersec.length) {
        spec = "protection";
        break;
      }
      spec = "retribution";
      break;
    case "Priest":
      if (set_spec.toLowerCase() === 'shadow') {
        spec = "shadow";
        break;
      }
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.heal.includes(value));
      if (intersec.length) {
        spec = "healing";
        break;
      }
      spec = "shadow";
      break;
    case "Warrior":
      if (set_spec.toLowerCase() === 'protection') {
        spec = "protection";
        break;
      }
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.tank.includes(value));
      if (intersec.length) {
        spec = "protection";
        break;
      }
      spec = "";
      break;
    case "Deathknight":
      intersec = sim_gear[0].gems.filter((value) => SPEC_GEMS.tank.includes(value));
      if (intersec.length) {
        spec = "tank";
        break;
      }
      spec = "";
      break;
    default:
      spec = "";
  }

  return spec;
}
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
