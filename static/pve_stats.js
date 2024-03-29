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
const serverSelect = document.getElementById("select-server");
const instanceSelect = document.getElementById("select-instance");
const bossSelect = document.getElementById("select-boss");
const sizeSelect = document.getElementById("select-mode");
const difficultyCheckbox = document.getElementById("difficulty-checkbox");
const submitButton = document.getElementById("submit-button");
const chartTimeline = document.getElementById("chart-timeline");
const statsTableBody = document.getElementById("stats-tbody");
const theTooltip = document.getElementById("the-tooltip");
const theTooltipSpec = document.getElementById("tooltip-spec-info");
const theTooltipBody = document.getElementById("tooltip-body");
const INTERACTABLES = {
  server: serverSelect,
  raid: instanceSelect,
  boss: bossSelect,
  size: sizeSelect,
};

const KEY_DPS = "v";
const KEY_QUANTITY = "n";
const DPS_JUMP = 1000;
const CACHE = {};
const xrequest = new XMLHttpRequest();

let tt_hide_timeout;
let maxvalue = 20000;

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
  remove_children(bossSelect);
  BOSSES[instanceSelect.value].forEach(boss_name => bossSelect.appendChild(new_option(boss_name)));
};

function make_query() {
  const sizeValue = sizeSelect.value;
  const diffValue = difficultyCheckbox.checked ? 'H' : 'N';
  const mode_str = `${sizeValue}${diffValue}`;
  const q = {
    server: serverSelect.value,
    boss: bossSelect.value,
    mode: mode_str,
  };
  return JSON.stringify(q);
}


const to_width_percent = v => `${v}%`;

function new_dps_line(v) {
  const line = document.createElement("div");
  line.className = "chart-column";
  line.style.left = to_width_percent(v*DPS_JUMP/maxvalue*100);
  line.setAttribute("data-label", `${v}k`);
  chartTimeline.appendChild(line);
}
function new_dps_columns() {
  remove_children(chartTimeline);
  for (let i=0; i<maxvalue/DPS_JUMP; i++) {
    new_dps_line(i); 
  }
}

function new_div(classname, pos) {
  const div = document.createElement("div");
  div.className = classname;
  div.style.left = to_width_percent(pos);
  return div;
}

function update_row(row, data) {
  const cell = row.querySelector(".stats-cell-data");
  remove_children(cell);
  if (!data) {
    Array.from(row.attributes)
         .filter(attr => attr.name.slice(0,4) == "data")
         .splice(2)
         .forEach(attr => row.removeAttribute(attr.name));
    return;
  }

  const _divs = {};
  const _values = {};
  for (let k in data) {
    const _value = Math.round(data[k][KEY_DPS]);
    const _amount = data[k][KEY_QUANTITY];
    row.setAttribute(`data-${k}-${KEY_DPS}`, _value);
    row.setAttribute(`data-${k}-${KEY_QUANTITY}`, _amount);
    if (k == "all") continue;

    const _pos = _value/maxvalue*100;
    const _div = new_div(k, _pos);
    cell.appendChild(_div);

    _divs[k] = _div;
    _values[k] = _pos;
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
  maxvalue = Math.ceil((max_v+500)/1000)*1000;
  
  new_dps_columns();
  
  const rows = Array.from(statsTableBody.querySelectorAll("tr"));
  for (const tr of rows) {
    update_row(tr, data[tr.id]);
  }

  rows.sort((a, b) => b.getAttribute("data-sort") - a.getAttribute("data-sort"))
      .forEach(row => statsTableBody.appendChild(row));
}


xrequest.onreadystatechange = () => {
  if (xrequest.readyState != 4) {
    submitButton.textContent = "Loading";
    return;
  }
  if (xrequest.status != 200) return;
  submitButton.textContent = "Submit";
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

  const __diff = difficultyCheckbox.checked ? 'H' : "N";
  const title = `UwU Logs - Top - ${bossSelect.value} - ${sizeSelect.value}${__diff}`;
  document.title = title;

  const parsed = {
    server: serverSelect.value,
    raid: instanceSelect.value,
    boss: bossSelect.value,
    size: sizeSelect.value,
    mode: difficultyCheckbox.checked ? 1 : 0,
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
  theTooltipSpec.innerHTML = "";
  theTooltipSpec.appendChild(tr.querySelector("img").cloneNode());
  theTooltipSpec.append(`${tr.getAttribute("data-spec")} ${tr.getAttribute("data-class")}`);
  theTooltipSpec.className = tr.classList[1];
  
  for (const _row of theTooltipBody.children) {
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
  const trRect = tr.getBoundingClientRect();
  const h = document.documentElement.clientHeight / 7 * 5;
  if (trRect.bottom > h) {
    theTooltip.style.bottom = "0";
    theTooltip.style.removeProperty("top");
  } else {
    theTooltip.style.top = `${trRect.bottom}px`;
    theTooltip.style.removeProperty("bottom");
  }
  theTooltip.style.left = `${elemRect.left}px`;
  theTooltip.style.removeProperty("display");
}
function hide_tooltip() {
  clearTimeout(tt_hide_timeout);
  tt_hide_timeout = setTimeout(() => theTooltip.style.display = "none", 250)
}
function add_tooltip_events() {
  theTooltip.addEventListener("mouseenter", () => clearTimeout(tt_hide_timeout));
  theTooltip.addEventListener("mouseleave", hide_tooltip);
  document.querySelectorAll(".stats-cell-row").forEach(tr => {
    tr.addEventListener("mouseleave", hide_tooltip);
    tr.addEventListener("mouseenter", () => {
      if (!tr.getAttribute(`data-all-${KEY_QUANTITY}`)) return;
      clearTimeout(tt_hide_timeout);
      add_tooltip_info(tr);
      move_tooltip_to(tr);
    });
  });
}


function init() {
  const is_valid_param = (elm, par) => Array.from(elm.children).map(e => e.value).includes(par);
  const find_value_index = (select, option_name) => Array.from(select.children).map(e => e.innerText).indexOf(option_name);

  Object.keys(BOSSES).forEach(name => instanceSelect.appendChild(new_option(name)));

  const currentParams = new URLSearchParams(window.location.search);
  difficultyCheckbox.checked = currentParams.get("mode") != 0;

  for (const key in INTERACTABLES) {
    const par = currentParams.get(key);
    const elm = INTERACTABLES[key];
    if (is_valid_param(elm, par)) {
      elm.value = par;
    } else if (elm == serverSelect) {
      elm.selectedIndex = find_value_index(elm, "Lordaeron");
    } else {
      elm.selectedIndex = 0;
    }

    if (elm == instanceSelect) {
      add_bosses();
    }
  }

  instanceSelect.addEventListener("change", add_bosses);
  submitButton.addEventListener("click", search_changed);
  add_tooltip_events();
  search_changed();

  const button_click = e => {
    const sortby = `data-${e.target.className}-${KEY_DPS}`;
    Array.from(statsTableBody.children)
    .sort((a,b) => b.getAttribute(sortby) - a.getAttribute(sortby))
    .forEach(tr => statsTableBody.appendChild(tr));
  }
  const table_sort = document.getElementById("table-sort");
  for (const button of table_sort.getElementsByTagName('button')) {
    button.addEventListener("click", button_click);
  }
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
