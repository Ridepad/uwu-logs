import { CACHE } from "./gear_cache.js?v=240831-1";
import {
  QUALITY_COLOR,
  ENCHANTABLE,
  split_space_once,
  find_gem_data_by_name,
  slot_item_changed,
  find_equipped_sets,
  find_set_name,
} from "./gear_constants.js?v=240814-1";

const TOOLTIP = document.getElementById("tooltip-stats");
const GEAR_WRAP = document.getElementById("gear-wrap");
const CHAR_CLASS = document.getElementById("char-class");

function item_enchantable(item_data) {
  return ENCHANTABLE.includes(item_data.slot) || item_data.slot == "Finger" && GEAR_WRAP.getAttribute("data-enchanting");
}

function get_gem_color(gem_data) {
  const gem_data1 = find_gem_data_by_name(gem_data.names[1]);
  return `#${gem_data1.color_hex}`;
}

function dynamic_ench_row(row, ench_id, class_name) {
  const _type = class_name == "enchant" ? "enchant" : "gem";
  if (!ench_id) {
    row.className = "missing";
    row.textContent = `Missing ${_type}`;
    return;
  }

  row.className = "loading";
  row.textContent = `Loading ${_type}...`;
  
  CACHE.fetch_enchant_data(ench_id).then(ench_data => {
    row.className = class_name;
    const ench_string = ench_data.names[0].replaceAll("+", "");
    const [value, stat] = split_space_once(ench_string);
    row_add_value(row, value, stat);
    if (_type == "gem") {
      row.style.color = get_gem_color(ench_data);
    }
  });
}

function make_row_empty(row) {
  row.append(".");
  row.className = "blank-line";
}
function new_row(data) {
  const p = document.createElement("p");
  if (data) {
    p.append(data);
  } else {
    make_row_empty(p);
  }
  return p;
}
function row_add_value(p, value, stat) {
  const span = document.createElement("span");
  span.append(value);
  p.innerHTML = "";
  p.appendChild(span);
  p.append(stat);
  return p;
}
function new_row_num(value, stat) {
  const p = document.createElement("p");
  return row_add_value(p, value, stat);
}

function has_blacksmithing_socket(item_data) {
  return ["Wrist", "Hands"].includes(item_data.slot) && GEAR_WRAP.getAttribute("data-blacksmithing");
}

function has_meta_socket(item_data) {
  return item_data.slot == 'Head' && item_data.meta;
}

function has_additional_socket(item_data) {
  return item_data.slot == 'Waist' ||
  has_meta_socket(item_data) ||
  has_blacksmithing_socket(item_data);
}

function get_socket_amount(item_data) {
  const socket_amount = item_data.sockets.reduce((sum, a) => sum + a, 0);
  if (has_additional_socket(item_data)) {
    return socket_amount + 1;
  }
  return socket_amount;
}

function* tooltip_gems_rows(item_data, gems, socket_bonus) {
  const gems_a = gems.split(',');
  const socket_amount = get_socket_amount(item_data);

  yield new_row();

  for (const i of Array(socket_amount).keys()) {
    const row_gem = document.createElement("p");
    dynamic_ench_row(row_gem, gems_a[i], "gem");
    yield row_gem;
  }
  
  const sb = item_data["socketbonus"];
  if (!sb) {
    yield new_row();
    return;
  }
  
  const [sbonusname, sbonusvalue] = sb["stats"][0];
  const row_socket_bonus = new_row_num(sbonusvalue, sbonusname);
  if (socket_bonus) {
    row_socket_bonus.classList.add("enchant");
  } else {
    row_socket_bonus.classList.add("loading");
  }
  yield row_socket_bonus;
}

function* tooltip_sets(class_sets, item_id) {
  const set_name = find_set_name(class_sets, item_id);
  if (!set_name) return;
  
  const gear_ids = Array.from(document.querySelectorAll(".slot")).map(e => e.getAttribute("data-item-id"));
  const equipped_sets = find_equipped_sets(gear_ids, class_sets);
  const equipped_items_n = equipped_sets[set_name];
    
  const this_item_set = class_sets[set_name];

  yield new_row();
  
  const _set_title = `${set_name} ${equipped_items_n}/${this_item_set.pieces}`;
  const set_row = new_row(_set_title);
  set_row.className = "color-set-name";
  yield set_row;

  for (const [set_n, set_bonus] of this_item_set.stats) {
    const row = new_row_num(`${set_n}:`, set_bonus);
    row.className = equipped_items_n < set_n ? "loading" : "enchant";
    yield row;
  } 
}

function tooltip_row_item_name(item_data) {
  const row_name = new_row(item_data["name"]);
  row_name.classList.add("item-name");
  row_name.classList.add(QUALITY_COLOR[item_data.quality]);
  return row_name;
}

function tooltip_row_ilvl(item_data) {
  const row_ilvl = new_row(item_data["ilvl"]);
  if (item_data['heroic']) row_ilvl.classList.add("heroic");
  return row_ilvl;
}

function tooltip_row_slot_name(item_data) {
  return new_row(item_data["slot"]);
}

function tooltip_row_armor_type(item_data) {
  return new_row(item_data["armor type"]);
}
function* tooltip_row_item_stats(item_data) {
  for (const [stat, value] of item_data.stats) {
    yield new_row_num(value, stat);
  }
}

function tooltip_row_enchant(item_data, ench_id) {
  const row_ench = new_row();
  if (item_enchantable(item_data)) {
    dynamic_ench_row(row_ench, ench_id, "enchant");
  }
  return row_ench;
}
function tooltip_row_additional_effect(item_data) {
  if (item_data.add_text) {
    const row_add_text = new_row(item_data.add_text);
    row_add_text.classList.add("enchant");
    return row_add_text;
  }
}

async function show_tooltip(e) {
  TOOLTIP.innerHTML = "";
  
  const slot_element = e.target;
  const item_id = slot_element.getAttribute("data-item-id");
  const item_data = await CACHE.fetch_item_data(item_id);
  if (!item_data || slot_item_changed(slot_element, item_id)) return;

  const ench_id = slot_element.getAttribute("data-item-ench");
  const gems = slot_element.getAttribute("data-item-gems") ?? "";
  const socket_bonus = slot_element.getAttribute('data-socket-bonus');
  const class_sets = await CACHE.fetch_class_set(CHAR_CLASS.textContent);

  [
    tooltip_row_item_name(item_data),
    tooltip_row_ilvl(item_data),
    tooltip_row_slot_name(item_data),
    tooltip_row_armor_type(item_data),
    ...tooltip_row_item_stats(item_data),
    new_row(),
    tooltip_row_enchant(item_data, ench_id),
    ...tooltip_gems_rows(item_data, gems, socket_bonus),
    tooltip_row_additional_effect(item_data),
    ...tooltip_sets(class_sets, item_id),
  ].forEach(row => {
    if (row) TOOLTIP.appendChild(row);
  });
  
  TOOLTIP.classList.remove("hidden");
}

const GEAR_SLOTS = Array.from(document.querySelectorAll(".slot"));
for (const slot of GEAR_SLOTS) {
  slot.addEventListener("mouseenter", show_tooltip);
  slot.addEventListener("mouseleave", () => TOOLTIP.classList.add("hidden"));
}
