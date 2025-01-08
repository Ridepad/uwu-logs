import { CACHE } from "./gear_cache.js?v=240831-1";
import {
  get_gs,
  is_two_hand,
  QUALITY_COLOR,
  STATS_ORDER,
  split_space_once,
  find_gem_data_by_name,
  slot_item_changed,
  find_equipped_sets,
  object_default_int,
} from "./gear_constants.js?v=240814-1";


import { convert_to_link } from "./wowsim_export.js";

const ELEMENT_SET_NAME = document.getElementById("set-name");
const BUTTON_SET_PREV = document.getElementById("set-prev");
const BUTTON_SET_NEXT = document.getElementById("set-next");
const SPAN_GS = document.getElementById("gear-info-gs");
const CHAR_LEVEL = document.getElementById("char-level");
const CHAR_CLASS = document.getElementById("char-class");
const CHAR_RACE = document.getElementById("char-race");
const GEAR_WRAP = document.getElementById("gear-wrap");
const LOADING_INFO = document.getElementById("loading-gear");
const NO_GEAR_INFO = document.getElementById("missing-gear");
const NO_CACHE_INFO = document.getElementById("server-no-cache");
const TABLE_STATS_BODY = document.getElementById("table-stats-body");

const GEAR_SLOTS = Array.from(document.querySelectorAll(".slot"));

const URL_PREFIX_TALENTS = "https://aowow.trinitycore.info/?talent#";
const URL_PREFIX_ICON = "/static/icons";
const URL_PREFIX_CHARACTER = "/gear";
const RELEVANT_PROFS = ["Enchanting", "Blacksmithing"];
const DEFAULT_NAME_VALUE = {
  specs: ["No spec", "0/0/0"],
  profs: ["No prof", "0"],
};
const DEFAULT_SELECTOR = {
  specs: [".name", ".value a"],
  profs: [".name", ".value"],
};
const SERVERS_AVAILABLE_GEAR = [
  "Icecrown",
  "Lordaeron",
  "Rising-Gods",
  "WoW-Circle-x1",
  "WoW-Circle-x5",
  "WoW-Circle-x100",
];

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

function get_char_data_url(server, name) {
  return `${URL_PREFIX_CHARACTER}/${server}/${name}`;
}

function add_new_stats(all_stats, new_stats) {
  if (!new_stats) return;
  for (const [stat, value] of new_stats) {
    if (isNaN(value)) continue;
    const stat_lower = stat.toLowerCase();
    all_stats[stat_lower] += +value;
  }
}

function set_new_enchant(slot_element, slot_data) {
  if (slot_data["ench"]) slot_element.setAttribute("data-item-ench", slot_data["ench"]);
}
function set_new_gems(slot_element, slot_data) {
  const gems = (slot_data["gems"] ?? []).filter(v => v != 0);
  if (gems.length) slot_element.setAttribute("data-item-gems", gems);
}
async function set_new_img(slot_element, icon_name) {
  const exists = await CACHE.icon_exists(icon_name);
  if (!exists) icon_name = "undefined";
  const img = slot_element.querySelector("img");
  img.src = `${URL_PREFIX_ICON}/${icon_name}.jpg`;
}
function set_new_ilvl(slot_element, item_data) {
  const span = slot_element.querySelector("span");
  span.textContent = item_data.ilvl;
  span.className = QUALITY_COLOR[item_data.quality];
}

function reset_slot_element(slot_element) {
  slot_element.classList.add("hidden");
  slot_element.removeAttribute("data-item-id");
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



function set_new_spec_profs_values(e, name, value, talents) {
  const element_name = e.querySelector(".name span");
  const element_value = e.querySelector(".value span");
  element_name.textContent = name;
  element_value.textContent = value;
  if (talents) {
    const element_link_1 = e.querySelector(".value a");
    element_link_1.href = `${URL_PREFIX_TALENTS}${talents}`;
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
  const slots_gs = Array(18);
  GEAR_SLOTS.forEach(async (slot_element, slot_i) => {
    if (slot_element.classList.contains("hidden")) return;
    
    const item_id = slot_element.getAttribute("data-item-id");
    const item_data = await CACHE.fetch_item_data(item_id);
    if (!item_data || slot_item_changed(slot_element, item_id)) return;
    
    const gs = get_gs(slot_i, item_data, item_id);
    if (!gs) return;
    slots_gs[slot_i] = gs;

    if (slot_i == 16 && is_two_hand(item_data.slot)) {
      slots_gs.twohand = true;
    }
    let tgs = slots_gs.reduce((total, curr) => total + (curr ?? 0));
    if (slots_gs.twohand && slots_gs[17]) {
      tgs = tgs - (slots_gs[16] + slots_gs[17]) / 2;
    }
    SPAN_GS.textContent = tgs.toFixed(0);
  });
}

export default class Gear {
  calc_gs = throttle(calc_gs);
  add_stat_rows = throttle(add_stat_rows);

  constructor(server, name) {
    this.SERVER = server;
    this.NAME = to_title(name);
    this.URL = get_char_data_url(this.SERVER, this.NAME);
  }
  init() {
    NO_GEAR_INFO.style.display = "none";
    NO_CACHE_INFO.style.display = "none";
    if (!SERVERS_AVAILABLE_GEAR.includes(this.SERVER)) {
      GEAR_WRAP.style.display = "none";
      LOADING_INFO.style.display = "none";
      const msg = `${this.SERVER} doesn't have gear cache yet.`
      console.log(msg);
      NO_CACHE_INFO.textContent = `${this.SERVER} doesn't have gear cache yet.`;
      NO_CACHE_INFO.style.removeProperty("display");
      return;
    }
    
    const loading_timeout = setTimeout(() => {
      GEAR_WRAP.style.display = "none";
      LOADING_INFO.style.removeProperty("display");
    }, 100);

    fetch(this.URL).then(response => {
      clearTimeout(loading_timeout);
      if (response.ok) {
        this.parse_json(response);
        return;
      }
      console.log('not found');
      GEAR_WRAP.style.display = "none";
      LOADING_INFO.style.display = "none";
      NO_GEAR_INFO.style.removeProperty("display");
    });
  }
  parse_json(response) {
    response.json().then(data => {
      console.log(data);
      this.CHAR_DATA = data;
      this.SET_NAMES = Object.keys(data);
      this.SET_AMOUNT = this.SET_NAMES.length;
      this.CURRENT_SET_INDEX = this.SET_NAMES.length;
      
      this.apply_new_set();
      NO_GEAR_INFO.style.display = "none";
      GEAR_WRAP.style.removeProperty("display");

      BUTTON_SET_PREV.addEventListener("click", this); // this.handleEvent
      BUTTON_SET_NEXT.addEventListener("click", this); // this.handleEvent
    }).catch((error) => {
      console.log('error in parsing json',error);
      GEAR_WRAP.style.display = "none";
      NO_GEAR_INFO.style.removeProperty("display");
    }).finally(() => {
      LOADING_INFO.style.display = "none";
    });
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

    const stats = object_default_int();
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
      const talents_string = talents[i] ?? (data[i] ? data[i][2] : undefined);
      const [spec_name, spec_value] = data[i] ?? DEFAULT_NAME_VALUE.specs;
      set_new_spec_profs_values(e, spec_name, spec_value, talents_string);
      convert_to_link(i, e.querySelector(DEFAULT_SELECTOR["specs"][0]), this.NAME, SET, talents_string)
    });
  }
  add_profs() {
    const SET = this.get_current_set_data();
    const data = cnv_legacy(SET["profs"]);
    Array.from(document.querySelectorAll(".row-prof")).forEach((e, i) => {
      const [prof_name, prof_value] = data[i] ?? DEFAULT_NAME_VALUE.profs;
      set_new_spec_profs_values(e, prof_name, prof_value);
    });
  }
  apply_new_items(stats) {
    const SET = this.get_current_set_data();
    SET.gear_data.forEach(async (slot_data, slot_i) => {
      const slot_element = GEAR_SLOTS[slot_i];
      reset_slot_element(slot_element);
  
      const item_id = slot_data.item;
      if (!item_id) return;

      slot_element.setAttribute("data-item-id", item_id);
      const item_data = await CACHE.fetch_item_data(item_id);
      if (!item_data || slot_item_changed(slot_element, item_id)) return;
      
      slot_element.classList.remove("hidden");

      set_new_enchant(slot_element, slot_data);
      set_new_gems(slot_element, slot_data);
      set_new_img(slot_element, item_data.icon);
      set_new_ilvl(slot_element, item_data);

      add_new_stats(stats, item_data.stats);
      this.add_stat_rows(stats);
      
      this.calc_gs();
      this.add_ench_stats(stats, slot_element);
      this.add_gem_stats(stats, slot_element, item_data);
    });
  }
  async add_set_stats(stats) {
    const SET = this.get_current_set_data();
    const class_name = SET["class"];
    const class_sets = await CACHE.fetch_class_set(class_name);
    const gear_ids = Object.values(SET.gear_data).map(i => i.item);
    const equipped_sets = find_equipped_sets(gear_ids, class_sets);
    for (const set_name in equipped_sets) {
      const equipped_items = equipped_sets[set_name];
      const set_data = class_sets[set_name]["stats"];
      for (const [set_n, set_bonus] of set_data) {
        const [value, stat] = split_space_once(set_bonus);
        if (isNaN(value) || equipped_items < set_n) continue;
        stats[stat] += +value;
      }
    }
  }
  async add_ench_stats(all_stats, slot_element) {
    const ench_id = slot_element.getAttribute("data-item-ench"); 
    if (!ench_id) return;
    const ench_data = await CACHE.fetch_enchant_data(ench_id);
    add_new_stats(all_stats, ench_data.stats);
    this.add_stat_rows(all_stats);
  }
  add_gem_stats(all_stats, slot_element, item_data) {
    if (!item_data.sockets) return;
    
    const socketed_gems = slot_element.getAttribute("data-item-gems"); 
    if (!socketed_gems) return;
    
    const sbonus = Array.from(item_data.sockets); // copy to remove reference
    const gem_data_all = socketed_gems.split(',').map(gem_id => CACHE.fetch_enchant_data(gem_id));
    Promise.allSettled(gem_data_all).then(results => {
      results.forEach(result => {
        const gem_info = result.value;
        add_new_stats(all_stats, gem_info.stats);

        const gem_data = find_gem_data_by_name(gem_info.names[1]);
        sbonus.forEach((v, i) => sbonus[i] = v - gem_data.socket[i]);
      });
      if (item_data.socketbonus && socket_bonus_reached(sbonus)) {
        const [sbonusname, sbonusvalue] = item_data.socketbonus.stats[0];
        const stat = sbonusname.toLowerCase();
        all_stats[stat] += sbonusvalue;
        slot_element.setAttribute("data-socket-bonus", true);
      }
      this.add_stat_rows(all_stats);
    });
  }
}
