import {
  get_gs,
  is_two_hand,
  CACHE,
  CONTROLLER,
  QUALITY_COLOR,
  ENCHANTABLE,
  STATS_ORDER,
  GEM_DATA,
  DEFAULT_GEM_DATA,
} from "./gear_constants.js"

const TOOLTIP = document.getElementById("tooltip-stats");
const ELEMENT_SET_NAME = document.getElementById("set-name");
const BUTTON_SET_PREV = document.getElementById("set-prev");
const BUTTON_SET_NEXT = document.getElementById("set-next");
const SPAN_GS = document.getElementById("gear-info-gs");
const CHAR_LEVEL = document.getElementById("char-level");
const CHAR_CLASS = document.getElementById("char-class");
const CHAR_RACE = document.getElementById("char-race");
const TABLE_INFO_BODY = document.getElementById("table-info-body");
const TABLE_STATS_BODY = document.getElementById("table-stats-body");
const GEAR_WRAP = document.getElementById("gear-wrap");

const GEAR_SLOTS = Array.from(document.querySelectorAll(".slot"));

const URL_PREFIX_ICON = "/cache/icon";
const URL_PREFIX_CHARACTER = "/cache/character";
const RELEVANT_PROFS = ["Enchanting", "Blacksmithing"];
const DEFAULT_NAME_VALUE = {
  specs: ["No spec", "0/0/0"],
  profs: ["No prof", "0"],
};
const DEFAULT_SELECTOR = {
  specs: [".name", ".value a"],
  profs: [".name", ".value"],
};

const TIMEOUTS = {};
function throttle(fn, timeout=50) {
  return function(...args) {
    clearTimeout(TIMEOUTS[fn.name]);
    TIMEOUTS[fn.name] = setTimeout(() => fn(...args), timeout);
  }
}

function to_title(string) {
  return string.charAt(0).toUpperCase() + string.substr(1).toLowerCase();
}

function add_value(object, key, value) {
  object[key] = (object[key] ?? 0) + Number(value);
}

function get_char_data_url(server, name) {
  return `${URL_PREFIX_CHARACTER}/${server}/${name}.json`;
}

function make_row_empty(row) {
  row.append(".");
  row.className = "blank-line";
}
function new_p(data) {
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
function new_p_num(value, stat) {
  const p = document.createElement("p");
  return row_add_value(p, value, stat);
}

function add_new_stats(all_stats, new_stats) {
  for (const [stat, value] of new_stats) {
    if (isNaN(value)) continue;
    const stat_lower = stat.toLowerCase();
    add_value(all_stats, stat_lower, value);
  }
}

function add_item_data(slot_element, slot_data, item_data) {
  if (slot_data["ench"]) slot_element.setAttribute("data-item-ench", slot_data["ench"]);
  const gems = (slot_data["gems"] ?? []).filter(v => v != 0);
  if (gems.length) slot_element.setAttribute("data-item-gems", gems);

  slot_element.classList.remove("hidden");

  const img = slot_element.querySelector("img");
  img.src = `${URL_PREFIX_ICON}/${item_data.icon}.jpg`;
  img.setAttribute("data-name", item_data.icon);
  
  const span = slot_element.querySelector("span");
  span.textContent = item_data.ilvl;
  span.className = QUALITY_COLOR[item_data.quality];
}

function reset_slot_element(slot_element) {
  slot_element.classList.add("hidden");
  slot_element.removeAttribute("data-item-gs");
  slot_element.removeAttribute("data-item-ench");
  slot_element.removeAttribute("data-item-gems");
  slot_element.removeAttribute("data-socket-bonus");
}

function socket_bonus_reached(sockets) {
  for (const v of sockets) {
    if (v > 0) return false;
  }
  return true;
}

function has_blacksmithing_socket(item_data) {
  return ["Wrist", "Hands"].includes(item_data.slot) && GEAR_WRAP.getAttribute("data-blacksmithing");
}

function has_meta_socket(item_data) {
  return item_data.slot == 'Head' && item_data.meta
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

function cnv_legacy(object) {
  if (!object) return [];
  if (object.map) return object;
  
  const a = [];
  for (const name in object) {
    a.push([name, object[name]]);
  }
  return a;
}

function format_timestamp(t) {
  const timestamp = Number(t);
  if (isNaN(timestamp)) return t;
  const date = new Date(timestamp * 1000);
  return date.toISOString().slice(0, -8).replace("T", " ");
}

function find_equipped_sets(gear_ids, sets) {
  const equipped_sets = {};
  gear_ids.forEach(item_id => {
    const set_name = find_set_name(sets, item_id);
    if (!set_name) return;
    add_value(equipped_sets, set_name, 1);
  });
  return equipped_sets;
}

function find_set_name(sets, item_id) {
  item_id = parseInt(item_id);
  for (const set_name in sets) {
    if (sets[set_name].items.includes(item_id)) {
      return set_name;
    }
  }
}

function class_name_format(class_name) {
  return class_name.toLowerCase().replace(" ", "");
}

function slot_item_changed(slot_element, item_id) {
  const current_item_id = slot_element.getAttribute("data-item-id");
  return current_item_id != item_id;
}

function set_new_spec_profs_values(e, data, type, talents) {
  const [query_name, query_value] = DEFAULT_SELECTOR[type];
  const element_name = e.querySelector(query_name);
  const element_value = e.querySelector(query_value);
  const [name, value] = data ?? DEFAULT_NAME_VALUE[type];
  element_name.textContent = name;
  element_value.textContent = value;
  if (talents) {
    element_value.href = `https://wotlk.evowow.com/?talent#${talents}`;
  } else {
    element_value.removeAttribute("href");
  }
}

function add_stat_row(stat_name, stat_value) {
  if (!stat_value) return;

  const row = document.createElement("tr");
  
  const cell_value = document.createElement("td");
  cell_value.append(stat_value);
  row.appendChild(cell_value);

  const cell_name = document.createElement("td");
  cell_name.append(stat_name);
  row.appendChild(cell_name);

  TABLE_STATS_BODY.appendChild(row);
}

function add_stat_rows(stats) {
  TABLE_STATS_BODY.innerHTML = "";
  const _ap = stats["attack power"] ?? 0;
  const _sp = stats["spell power"] ?? 0;
  const order = _ap > _sp ? STATS_ORDER.ap : STATS_ORDER.caster;
  ["main", "other"].forEach(t => {
    order[t].forEach(stat_name => {
      add_stat_row(stat_name, stats[stat_name]);
    });
  });
}

function calc_gs() {
  let main_hand
  let total_gs = 0;
  GEAR_SLOTS.forEach((slot_element, slot_i) => {
    if (slot_element.classList.contains("hidden")) return;
    
    const item_id = slot_element.getAttribute("data-item-id");
    CACHE.get_item_data(item_id).then(item_data => {
      if (!item_data || slot_item_changed(slot_element, item_id)) return;
      
      const gs = get_gs(slot_i, item_data, item_id);
      if (!gs) return;
      if (slot_i == 16 && is_two_hand(item_data.slot)) {
        main_hand = gs;
      }
      if (slot_i == 17 && main_hand) {
        total_gs = total_gs - (main_hand - gs) / 2;
      } else {
        total_gs = total_gs + gs;
      }
      SPAN_GS.textContent = total_gs.toFixed(0);
    })
  })
}


class Gear {
  calc_gs = throttle(calc_gs);
  add_stat_rows = throttle(add_stat_rows);

  constructor(server, name) {
    this.SERVER = to_title(server);
    this.NAME = to_title(name);
    const url = get_char_data_url(this.SERVER, this.NAME);
    fetch(url).then(j => j.json().then(data => {
      this.CHAR_DATA = data;
      this.SET_NAMES = Object.keys(data);
      this.SET_AMOUNT = this.SET_NAMES.length;
      this.CURRENT_SET_INDEX = this.SET_NAMES.length;
  
      this.apply_new_set();
  
      BUTTON_SET_PREV.addEventListener("click", this); // this.handleEvent
      BUTTON_SET_NEXT.addEventListener("click", this); // this.handleEvent
    }))
  }
  handleEvent(event) {
    if (event.type == "click") this.apply_new_set(event.target);
  }
  get_current_set_data() {
    const set_date = this.SET_NAMES[this.CURRENT_SET_INDEX];
    let set = this.CHAR_DATA[set_date];
    for (let i = 0; i < 10; i++) {
      if (isNaN(set)) break;
      set = this.CHAR_DATA[set];
    }
    return set;
  }
  apply_new_set(e) {
    const i = e == BUTTON_SET_NEXT ? 1 : -1;
    const next = this.SET_AMOUNT + this.CURRENT_SET_INDEX + i;
    this.CURRENT_SET_INDEX = next % this.SET_AMOUNT;
    const timestamp = this.SET_NAMES[this.CURRENT_SET_INDEX];
    ELEMENT_SET_NAME.textContent = format_timestamp(timestamp);
    this.apply_basic_info();
    this.add_relevant_profs();
    this.add_specs();
    this.add_profs();

    const stats = {};
    this.add_set_stats(stats);
    this.apply_new_items(stats);
  }
  apply_basic_info() {
    const SET = this.get_current_set_data();
    CHAR_LEVEL.textContent = SET["level"];
    CHAR_CLASS.textContent = SET["class"];
    CHAR_RACE.textContent = SET["race"];
  }
  add_relevant_profs() {
    const SET = this.get_current_set_data();
    const _profs = cnv_legacy(SET.profs);
    const profs = _profs.map(e => e[0]);
    RELEVANT_PROFS.forEach(prof_name => {
      const data_name = `data-${prof_name.toLowerCase()}`;
      if (profs.includes(prof_name)) {
        GEAR_WRAP.setAttribute(data_name, true);
      } else {
        GEAR_WRAP.removeAttribute(data_name);
      }
    });
  }
  add_specs() {
    const SET = this.get_current_set_data();
    const data = cnv_legacy(SET["specs"]);
    const talents = SET.talents ?? [];
    Array.from(document.querySelectorAll(".row-spec")).forEach((e, i) => {
      set_new_spec_profs_values(e, data[i], "specs", talents[i]);
    })
  }
  add_profs() {
    const SET = this.get_current_set_data();
    const data = cnv_legacy(SET["profs"]);
    Array.from(document.querySelectorAll(".row-prof")).forEach((e, i) => {
      set_new_spec_profs_values(e, data[i], "profs");
    })
  }
  apply_new_items(stats) {
    const SET = this.get_current_set_data();
    SET.gear_data.forEach((slot_data, slot_i) => {
      const slot_element = GEAR_SLOTS[slot_i];
      reset_slot_element(slot_element);
  
      const item_id = slot_data.item;
      if (!item_id) {
        slot_element.removeAttribute("data-item-id");
        return;
      };

      slot_element.setAttribute("data-item-id", item_id);
      CACHE.get_item_data(item_id).then(item_data => {
        if (!item_data || slot_item_changed(slot_element, item_id)) return;
        
        add_item_data(slot_element, slot_data, item_data);
        add_new_stats(stats, item_data.stats);
        this.add_stat_rows(stats);
        
        this.calc_gs();
        this.add_ench_stats(stats, slot_element);
        this.add_gem_stats(stats, slot_element, item_data);
      })
    })
  }
  add_set_stats(stats) {
    const SET = this.get_current_set_data();
    const class_name = class_name_format(SET["class"]);
    CACHE.get_class_set(class_name).then(sets => {
      const gear_ids = Object.values(SET.gear_data).map(i => i.item);
      const equipped_sets = find_equipped_sets(gear_ids, sets);
      for (const set_name in equipped_sets) {
        const equipped_items = equipped_sets[set_name];
        const set_data = sets[set_name]["stats"];
        for (const [set_n, str] of set_data) {
          const [value, stat] = split_space_once(str);
          if (isNaN(value) || equipped_items < set_n) continue;
          add_value(stats, stat, value);
        }
      }
    });
  }
  add_ench_stats(all_stats, slot_element) {
    const ench_id = slot_element.getAttribute("data-item-ench"); 
    if (!ench_id) return;
    CACHE.get_enchant_data(ench_id).then(ench_data => {
      add_new_stats(all_stats, ench_data.stats);
      this.add_stat_rows(all_stats);
    })
  }
  add_gem_stats(all_stats, slot_element, item_data) {
    const gems = slot_element.getAttribute("data-item-gems"); 
    if (!gems) return;
    
    const sbonus = Array.from(item_data.sockets); // copy to remove reference
    const gem_data_all = gems.split(',').map(gem_id => CACHE.get_enchant_data(gem_id));
    Promise.allSettled(gem_data_all).then(results => {
      results.forEach(result => {
        const gem_data = result.value;
        add_new_stats(all_stats, gem_data.stats);

        const gem_data1 = find_gem_data_by_name(gem_data.names[1]);
        sbonus.forEach((v, i) => sbonus[i] = v - gem_data1.socket[i]);
      })
      if (item_data.socketbonus && socket_bonus_reached(sbonus)) {
        const [sbonusname, sbonusvalue] = item_data.socketbonus.stats[0];
        const stat = sbonusname.toLowerCase();
        add_value(all_stats, stat, sbonusvalue);
        slot_element.setAttribute("data-socket-bonus", true);
      }
      this.add_stat_rows(all_stats);
    });
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

function item_enchantable(item_data) {
  return ENCHANTABLE.includes(item_data.slot) || item_data.slot == "Finger" && GEAR_WRAP.getAttribute("data-enchanter");
}

function get_gem_color(gem_data) {
  const gem_data1 = find_gem_data_by_name(gem_data.names[1]);
  return `#${gem_data1.color_hex}`;
}

function split_space_once(string) {
  const space_at = string.indexOf(' ');
  const value = string.substring(0, space_at);
  const stat = string.substring(space_at + 1);
  return [value, stat];
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
  
  CACHE.get_enchant_data(ench_id).then(ench_data => {
    row.className = class_name;
    const ench_string = ench_data.names[0].replaceAll("+", "");
    const [value, stat] = split_space_once(ench_string);
    row_add_value(row, value, stat);
    if (_type == "gem") {
      row.style.color = get_gem_color(ench_data);
    }
  })
}

function tooltip_gems(slot_element, item_data) {
  const gems = slot_element.getAttribute("data-item-gems") ?? ""; 
  const gems_a = gems.split(',');
  const socket_amount = get_socket_amount(item_data);

  for (const i of Array(socket_amount).keys()) {
    const row_gem = document.createElement("p");
    TOOLTIP.appendChild(row_gem);
    dynamic_ench_row(row_gem, gems_a[i], "gem");
  }
  
  const sb = item_data["socketbonus"];
  if (!sb) {
    TOOLTIP.appendChild(new_p());
    return;
  }
  
  const [sbonusname, sbonusvalue] = sb["stats"][0];
  const row_socket_bonus = new_p_num(sbonusvalue, sbonusname);
  const socket_bonus = slot_element.getAttribute('data-socket-bonus');
  if (socket_bonus) {
    row_socket_bonus.classList.add("enchant");
  } else {
    row_socket_bonus.classList.add("loading");
  }
  TOOLTIP.appendChild(row_socket_bonus);
}

function tooltip_sets(main_item_id) {
  const gear_ids = Array.from(document.querySelectorAll(".slot")).map(e => e.getAttribute("data-item-id"));
  const class_name = class_name_format(CHAR_CLASS.textContent);
  CACHE.get_class_set(class_name).then(sets => {
    const set_name = find_set_name(sets, main_item_id);
    if (!set_name) return;

    const equipped_sets = find_equipped_sets(gear_ids, sets);
    const eq_items = equipped_sets[set_name];
    
    const this_item_set = sets[set_name];

    TOOLTIP.appendChild(new_p());
    const set_row = document.createElement("p");
    set_row.className = "color-set-name";
    set_row.textContent = `${set_name} ${eq_items}/${this_item_set.pieces}`;
    TOOLTIP.appendChild(set_row);

    for (let [set_n, v] of this_item_set.stats) {
      const row = new_p_num(`${set_n}:`, v);
      row.className = eq_items < set_n ? "loading" : "enchant";
      TOOLTIP.appendChild(row);
    } 
  });
}

function tooltip(e) {
  TOOLTIP.innerHTML = "";
  
  const slot_element = e.target;
  const item_id = slot_element.getAttribute("data-item-id");

  CACHE.get_item_data(item_id).then(item_data => {
    if (!item_data || slot_item_changed(slot_element, item_id)) return;

    const row_name = document.createElement("p");
    row_name.classList.add("item-name");
    row_name.classList.add(QUALITY_COLOR[item_data.quality]);
    row_name.textContent = item_data["name"];
    TOOLTIP.appendChild(row_name);
  
    const row_ilvl = new_p(item_data["ilvl"]);
    if (item_data['heroic']) row_ilvl.classList.add("heroic");
    TOOLTIP.appendChild(row_ilvl);
  
    const row_slot = new_p(item_data["slot"]);
    TOOLTIP.appendChild(row_slot);
  
    const row_type = new_p(item_data["armor type"]);
    TOOLTIP.appendChild(row_type);
    
    for (const [stat, value] of item_data.stats) {
      const row_stat = new_p_num(value, stat);
      TOOLTIP.appendChild(row_stat);
    }

    TOOLTIP.appendChild(new_p());
  
    const row_ench = document.createElement("p");
    TOOLTIP.appendChild(row_ench);
    if (item_enchantable(item_data)) {
      const ench_id = slot_element.getAttribute("data-item-ench");
      dynamic_ench_row(row_ench, ench_id, "enchant");
    } else {
      make_row_empty(row_ench);
    }

    TOOLTIP.appendChild(new_p());

    tooltip_gems(slot_element, item_data);
    
    if (item_data.add_text) {
      const row_add_text = new_p(item_data.add_text);
      row_add_text.classList.add("enchant");
      TOOLTIP.appendChild(row_add_text);
    }

    tooltip_sets(item_id);

    TOOLTIP.classList.remove("hidden");
  })
}

function refresh_image(img) {
  const src = img.src;
  const icon_name = img.getAttribute("data-name");
  CACHE.get_icon(icon_name).then(v => {
    if (v.ok) {
      img.src = src;
    }
  });
}

function init() {
  const searchParams = new URLSearchParams(location.search);
  const server = searchParams.get("server") ?? "Lordaeron";
  const character_name = searchParams.get("name") ?? "Safiyah";
  const gear = new Gear(server, character_name);

  for (const slot of GEAR_SLOTS) {
    slot.addEventListener("mouseenter", tooltip);
    slot.addEventListener("mouseleave", () => TOOLTIP.classList.add("hidden"));
  }
  for (const img of document.querySelectorAll(".slot img")) {
    img.addEventListener("error", e => refresh_image(e.target), {once: true});
  }
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
