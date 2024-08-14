const BOSSES = {
  "Icecrown Citadel": [
    "The Lich King",
    "Lord Marrowgar", "Lady Deathwhisper", "Deathbringer Saurfang",
    "Festergut", "Rotface", "Professor Putricide",
    "Blood Prince Council", "Blood-Queen Lana'thel",
    "Sindragosa"
  ],
  "The Ruby Sanctum": ["Halion", "Baltharus the Warborn", "Saviana Ragefire", "General Zarithrian"],
  "Trial of the Crusader": ["Anub'arak", "Northrend Beasts", "Lord Jaraxxus", "Faction Champions", "Twin Val'kyr"],
  "Ulduar": [
    "Flame Leviathan", "Ignis the Furnace Master", "Razorscale", "XT-002 Deconstructor",
    "Assembly of Iron", "Kologarn", "Auriaya", "Hodir", "Thorim", "Freya", "Mimiron",
    "General Vezax", "Yogg-Saron", "Algalon the Observer"
  ],
  "Naxxramas": [
    "Anub'Rekhan", "Grand Widow Faerlina", "Maexxna", "Noth the Plaguebringer", "Heigan the Unclean",
    "Loatheb", "Patchwerk", "Grobbulus", "Gluth", "Thaddius", "Instructor Razuvious", "Gothik the Harvester",
    "The Four Horsemen", "Sapphiron", "Kel'Thuzad"
  ],
  "Vault of Archavon": ["Toravon the Ice Watcher", "Archavon the Stone Watcher", "Emalon the Storm Watcher", "Koralon the Flame Watcher"],
  "Onyxia's Lair": ["Onyxia"],
  "The Eye of Eternity": ["Malygos"],
  "The Obsidian Sanctum": ["Sartharion"],
};
const SELECT_SERVER = document.getElementById("select-server");
const SELECT_INSTANCE = document.getElementById("select-instance");
const SELECT_BOSS = document.getElementById("select-boss");
const SELECT_SIZE = document.getElementById("select-mode");
const CHECKBOX_DIFFICULTY = document.getElementById("difficulty-checkbox");
const BUTTON_SUBMIT = document.getElementById("submit-button");
const CHART_TIMELINE = document.getElementById("chart-timeline");
const TBODY_STATS = document.getElementById("stats-tbody");
const TOOLTIP = document.getElementById("the-tooltip");
const TOOLTIP_HEAD_SPEC_INFO = document.getElementById("tooltip-spec-info");
const TOOTLIP_BODY = document.getElementById("tooltip-body");
const INTERACTABLES = {
  server: SELECT_SERVER,
  raid: SELECT_INSTANCE,
  boss: SELECT_BOSS,
  size: SELECT_SIZE,
};

const KEY_DPS = "dps";
const KEY_QUANTITY = "raids";
const CACHE = {};
const xrequest = new XMLHttpRequest();
const CONFIG = {
  tt_hide_timeout: undefined,
  max_dps_value: 20000,
  dps_jump: 1000,
}

const to_width_percent = v => `${v}%`;
const rows_sort_func = sort_by => (a, b) => b.getAttribute(sort_by) - a.getAttribute(sort_by);

function remove_children(node) {
  while(node.firstChild) node.removeChild(node.firstChild);
}

function new_option(value, index) {
  const _option = document.createElement('option');
  _option.value = index === undefined ? value : index;
  _option.innerHTML = value;
  return _option;
}

function add_bosses() {
  remove_children(SELECT_BOSS);
  BOSSES[SELECT_INSTANCE.value].forEach(boss_name => SELECT_BOSS.appendChild(new_option(boss_name)));
};

function make_query() {
  const sizeValue = SELECT_SIZE.value;
  const diffValue = CHECKBOX_DIFFICULTY.checked ? 'H' : 'N';
  const mode_str = `${sizeValue}${diffValue}`;
  const q = {
    server: SELECT_SERVER.value,
    boss: SELECT_BOSS.value,
    mode: mode_str,
  };
  return JSON.stringify(q);
}


function new_dps_line(v) {
  const line = document.createElement("div");
  line.className = "chart-column";
  line.style.left = to_width_percent(v / CONFIG.max_dps_value * 100);
  line.setAttribute("data-label", `${v / 1000}k`);
  CHART_TIMELINE.appendChild(line);
}
function new_dps_columns() {
  remove_children(CHART_TIMELINE);
  for (let i=0; i < CONFIG.max_dps_value; i = i + CONFIG.dps_jump) {
    new_dps_line(i); 
  }
}

function new_div(classname, pos) {
  const div = document.createElement("div");
  div.className = classname;
  div.style.left = to_width_percent(pos);
  return div;
}

function filter_attributes(attribute) {
  return attribute.name.slice(0, 4) == "data" && attribute.name != "data-spec";
}
function remove_data_attributes(element) {
  const filtered_attributes = Array.from(element.attributes).filter(filter_attributes);
  filtered_attributes.forEach(attr => element.removeAttribute(attr.name));
}

function update_row(row, data) {
  const cell = row.querySelector(".stats-cell-data");
  remove_children(cell);
  remove_data_attributes(row);
  if (!data) return;

  const _divs = {};
  const _values = {};
  for (const percentile_key in data) {
    const dps = Math.round(data[percentile_key][KEY_DPS]);
    const quantity = data[percentile_key][KEY_QUANTITY];
    row.setAttribute(`data-${percentile_key}-${KEY_DPS}`, dps);
    row.setAttribute(`data-${percentile_key}-${KEY_QUANTITY}`, quantity);
    if (percentile_key == "all") continue;

    const _pos = dps / CONFIG.max_dps_value * 100;
    const _div = new_div(percentile_key, _pos);
    cell.appendChild(_div);

    _divs[percentile_key] = _div;
    _values[percentile_key] = _pos;
  }
  const _data = Array.from(Object.keys(data)).sort((a, b) => b.replace("top") - a.replace("top"));
  for (let i=0; i<_data.length-3; i++) {
    _divs[_data[i+1]].style.width = to_width_percent(_values[_data[i]] - _values[_data[i+1]]);
  }

  row.setAttribute("data-sort", data[_data[1]][KEY_DPS]);

  const passthrudiv = new_div("passthrudiv", _values.top10);
  passthrudiv.style.width = to_width_percent(_values.top100 - _values.top10);
  cell.insertBefore(passthrudiv, cell.children[0]);
}
function table_add_new_data(data) {
  const max_v = Math.max(...Object.values(data).map(d => d.top100[KEY_DPS]));
  CONFIG.max_dps_value = Math.ceil((max_v+500)/1000)*1000;
  CONFIG.dps_jump = Math.ceil(CONFIG.max_dps_value / 20000) * 1000;
  
  new_dps_columns();
  
  const rows = Array.from(TBODY_STATS.querySelectorAll("tr"));
  for (const tr of rows) {
    update_row(tr, data[tr.id]);
  }

  rows.sort(rows_sort_func("data-sort")).forEach(row => TBODY_STATS.appendChild(row));
}


xrequest.onreadystatechange = () => {
  if (xrequest.readyState != 4) {
    BUTTON_SUBMIT.textContent = "Loading";
    return;
  }
  if (xrequest.status != 200) return;
  BUTTON_SUBMIT.textContent = "Submit";
  const data = JSON.parse(xrequest.response);
  const query = make_query();
  CACHE[query] = data;
  table_add_new_data(data);
}

function query_server(query) {
  xrequest.open("POST", '');
  xrequest.setRequestHeader("Content-Type", "application/json");
  xrequest.send(query);
}

function fetch_data() {
  const query = make_query();
  const data = CACHE[query];
  data ? table_add_new_data(data) : query_server(query);
}

function search_changed() {
  if (xrequest.readyState != 4 && xrequest.readyState != 0) return;

  const difficulty = CHECKBOX_DIFFICULTY.checked ? 'H' : "N";
  const title = `UwU Logs - Top - ${SELECT_BOSS.value} - ${SELECT_SIZE.value}${difficulty}`;
  document.title = title;

  const parsed = {
    server: SELECT_SERVER.value,
    raid: SELECT_INSTANCE.value,
    boss: SELECT_BOSS.value,
    size: SELECT_SIZE.value,
    mode: CHECKBOX_DIFFICULTY.checked ? 1 : 0,
  };

  const new_params = new URLSearchParams(parsed).toString();
  const url = `?${new_params}`;
  history.pushState(parsed, title, url);

  fetch_data();
}

function add_separator(n) {
  if (n < 1000) return n;
  const thousands = Math.floor(n / 1000);
  const remainder = (n % 1000).toString().padStart(3, "0");
  return `${thousands} ${remainder}`;
}

function add_tooltip_info(tr) {
  const img = TOOLTIP_HEAD_SPEC_INFO.querySelector("img");
  const span = TOOLTIP_HEAD_SPEC_INFO.querySelector("span");
  img.src = tr.querySelector("img").src;
  span.textContent = tr.getAttribute("data-spec");
  TOOLTIP_HEAD_SPEC_INFO.className = tr.classList[1];
  
  for (const _row of TOOTLIP_BODY.children) {
    const _name = _row.className;
    const points = tr.getAttribute(`data-${_name}-${KEY_DPS}`);
    const players = tr.getAttribute(`data-${_name}-${KEY_QUANTITY}`);
    const points_cell = _row.querySelector(".percentile");
    const players_cell = _row.querySelector(".npoints");
    if (_name != "max") players_cell.innerText = add_separator(players);
    if (_name != "all") points_cell.innerText = add_separator(points);
  }
}
function move_tooltip_to(tr) {
  const first_child = tr.querySelector(".stats-cell-data > div");
  if (!first_child) return;

  const elemRect = first_child.getBoundingClientRect();
  const bodyRect = document.body.getBoundingClientRect();
  const bottom_theshold = document.documentElement.clientHeight / 7 * 5;
  const top = elemRect.bottom > bottom_theshold ? bottom_theshold : elemRect.bottom;
  TOOLTIP.style.top = `${top - bodyRect.top}px`;
  TOOLTIP.style.left = `${elemRect.left}px`;
  TOOLTIP.style.removeProperty("display");
}
function hide_tooltip() {
  clearTimeout(CONFIG.tt_hide_timeout);
  CONFIG.tt_hide_timeout = setTimeout(() => TOOLTIP.style.display = "none", 250)
}
function add_row_events(tr) {
  tr.addEventListener("mouseleave", hide_tooltip);
  tr.addEventListener("mouseenter", () => {
    if (!tr.getAttribute(`data-all-${KEY_QUANTITY}`)) return;
    clearTimeout(CONFIG.tt_hide_timeout);
    add_tooltip_info(tr);
    move_tooltip_to(tr);
  });
}
function add_rows_events() {
  document.querySelectorAll(".stats-cell-row").forEach(tr => add_row_events(tr));
}
function add_tooltip_events() {
  TOOLTIP.addEventListener("mouseenter", () => clearTimeout(CONFIG.tt_hide_timeout));
  TOOLTIP.addEventListener("mouseleave", hide_tooltip);
}


function init() {
  const is_valid_param = (elm, par) => Array.from(elm.children).map(e => e.value).includes(par);
  const find_value_index = (select, option_name) => Array.from(select.children).map(e => e.innerText).indexOf(option_name);

  Object.keys(BOSSES).forEach(name => SELECT_INSTANCE.appendChild(new_option(name)));

  const currentParams = new URLSearchParams(window.location.search);
  CHECKBOX_DIFFICULTY.checked = currentParams.get("mode") != 0;

  for (const key in INTERACTABLES) {
    const par = currentParams.get(key);
    const elm = INTERACTABLES[key];
    if (is_valid_param(elm, par)) {
      elm.value = par;
    } else if (elm == SELECT_SERVER) {
      elm.selectedIndex = find_value_index(elm, "Lordaeron");
    } else {
      elm.selectedIndex = 0;
    }

    if (elm == SELECT_INSTANCE) {
      add_bosses();
    }
  }

  SELECT_INSTANCE.addEventListener("change", add_bosses);
  BUTTON_SUBMIT.addEventListener("click", search_changed);
  add_tooltip_events();
  add_rows_events();
  search_changed();

  const button_click = e => {
    const sortby = `data-${e.target.className}-${KEY_DPS}`;
    Array.from(TBODY_STATS.children)
    .sort(rows_sort_func(sortby))
    .forEach(tr => TBODY_STATS.appendChild(tr));
  }
  const table_sort = document.getElementById("table-sort");
  for (const button of table_sort.getElementsByTagName('button')) {
    button.addEventListener("click", button_click);
  }
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
