import Gear from "./char_parser.js?v=241104-1";
import { SPECS } from "./constants.js?v=240830-1";

const INFO_LOADING_POINTS = document.getElementById("loading-points");
const INFO_MISSING_POINTS = document.getElementById("missing-points");
const SECTION_PLAYER_POINTS_WRAP = document.getElementById("player-points-wrap");
const TBODY_POINTS = document.getElementById("points-body");
const TOOLTIP_POINTS = document.getElementById("tooltip-points");
const PLAYER_SEARCH = document.getElementById("player-search");
const PLAYER_NAME = document.getElementById("player-name");
const PLAYER_SERVER = document.getElementById("player-server");
const PLAYER_OVERALL_POINTS = document.getElementById("player-overall-points");
const PLAYER_OVERALL_RANK = document.getElementById("player-overall-rank");
const BUTTON_TOGGLE_MORE_BOSSES = document.getElementById("toggle-more-bosses");
const INPUT_CHAR = document.getElementById("charname-seach");
const SELECT_SERVER = document.getElementById("server-select");
const SPEC_SWAP_WRAP = document.getElementById("spec-wrap");
const DEFAULT_SPEC = [3, 1, 2, 2, 3, 3, 2, 1, 2, 2];
const POINTS = [100, 99, 95, 90, 75, 50, 25, 0];
const SPEC_BUTTONS = [1,2,3].map(i => ({
  index: i,
  input: document.getElementById(`spec-${i}-input`),
  label: document.getElementById(`spec-${i}-label`),
}));

const CURRENT_CHARACTER = {
  name: undefined,
  server: undefined,
  spec: undefined,
  class_i: undefined,
  popped: false,
  main_data() {
    return {
      name: this.name,
      server: this.server,
      spec: this.spec,
    }
  },
  json() {
    return JSON.stringify(this.main_data());
  },
  to_url_params() {
    return new URLSearchParams(Object.entries(this.main_data()));
  },
};
const CACHE_CHARACTERS = {
  current() {
    return this[CURRENT_CHARACTER.json()];
  },
};

let loading_timeout;
const CHAR_REQUEST = new XMLHttpRequest();
CHAR_REQUEST.onreadystatechange = () => {
  if (CHAR_REQUEST.readyState != 4) return;
  clearTimeout(loading_timeout);
  if (CHAR_REQUEST.status != 200) {
    SECTION_PLAYER_POINTS_WRAP.style.display = "none";
    INFO_LOADING_POINTS.style.display = "none";
    SPEC_SWAP_WRAP.style.visibility = "hidden";
    INFO_MISSING_POINTS.style.removeProperty("display");
    CURRENT_CHARACTER.class_i = undefined;
    return;
  }

  const j = JSON.parse(CHAR_REQUEST.response);
  
  if (!CURRENT_CHARACTER.spec) {
    CURRENT_CHARACTER.spec = DEFAULT_SPEC[j.class_i];
  }

  CACHE_CHARACTERS[CURRENT_CHARACTER.json()] = j;

  table_add_new_data(j);
}

function armory_link_warmane(server) {
  return name => `https://armory.warmane.com/character/${name}/${server}`;
}
function armory_link_rising_gods(name) {
  return `https://db.rising-gods.de/?profile=eu.rising-gods.${name}`;
}
const SERVER_ARMORY_FUNCTIONS = {
  "Lordaeron": armory_link_warmane("Lordaeron"),
  "Icecrown": armory_link_warmane("Icecrown"),
  "Onyxia": armory_link_warmane("Onyxia"),
  "Rising-Gods": armory_link_rising_gods,
};

function add_point(v) {
  return (v / 100).toFixed(2);
}

function split_thousands(v) {
  const a = v.toString().split('');
  const insert_at = a.includes(".") ? 5 : 3;
  if (a.length <= insert_at) return v;
  a.splice(a.length-insert_at, 0, ' ');
  return a.join('');
}

function format_dps(v) {
  v = v.toFixed(1);
  return split_thousands(v);
}

const TOOLTIP_ELEMENTS = {
  ".row-players .td-player": boss_data => split_thousands(boss_data["rank_players"]),
  ".row-players .td-max":    boss_data => split_thousands(boss_data["spec_total_players"]),
  ".row-players .td-points": boss_data => add_point(boss_data["points_rank_players"]),
  ".row-raids .td-player":   boss_data => split_thousands(boss_data["rank_raids"]),
  ".row-raids .td-max":      boss_data => split_thousands(boss_data["spec_total_raids"]),
  ".row-raids .td-points":   boss_data => add_point(boss_data["points_rank_raids"]),
  ".row-dps .td-player":     boss_data => format_dps(boss_data["dps_max"]),
  ".row-dps .td-max":        boss_data => format_dps(boss_data["spec_r1_dps"]),
  ".row-dps .td-points":     boss_data => add_point(boss_data["points_dps"]),
};

function is_landscape() {
  return window.matchMedia("(orientation: landscape)").matches;
}

function cell(v, class_name) {
  const td = document.createElement("td");
  td.className = class_name;
  td.append(v);
  return td;
}

function format_duration(dur) {
  const minutes = Math.floor(dur / 60);
  const seconds = Math.floor(dur % 60);
  const m_str = minutes.toString().padStart(2, '0');
  const s_str = seconds.toString().padStart(2, '0');
  return `${m_str}:${s_str}`;
}

function points_rank_class(v) {
  for (const i of POINTS) if (v - i >= 0) return `top${i}`;
}

function cell_points(v) {
  const _class = points_rank_class(v/100);
  v = add_point(v);
  const td = cell(v, "cell-points");
  td.classList.add(_class);
  return td;
}

function tooltip_set_values(row) {
  const data = CACHE_CHARACTERS.current();
  const boss_name = row.getAttribute("data-boss-name");
  const boss_data = data.bosses[boss_name];

  for (const selector in TOOLTIP_ELEMENTS) {
    const element = TOOLTIP_POINTS.querySelector(selector);
    const f = TOOLTIP_ELEMENTS[selector];
    element.textContent = f(boss_data);
  }
}
function row_on_enter(event) {
  const row = event.target;
  tooltip_set_values(row);
  const trRect = row.getBoundingClientRect();
  TOOLTIP_POINTS.style.top = `${trRect.bottom}px`;
  TOOLTIP_POINTS.style.left = is_landscape() ? `${trRect.left}px` : 0;
  TOOLTIP_POINTS.style.removeProperty("display");
}

function cell_date(report_ID) {
  const report_date = report_ID.slice(0, 15);
  const [year, month, day, ] = report_date.split('-');
  const date_text = `${day}-${month}-${year}`;

  const a = document.createElement('a');
  a.href = `/reports/${report_ID}`;
  a.target = "_blank";
  a.append(date_text);

  const cell = document.createElement('td');
  cell.appendChild(a);
  cell.className = "cell-date";

  return cell;
}

function add_dummy_cells(tr) {
  tr.appendChild(cell("", "cell-rank"));
  tr.appendChild(cell_points(0));
  tr.appendChild(cell("", "cell-dps"));
  tr.appendChild(cell("", "cell-dur"));
  tr.appendChild(cell("", "cell-raids"));
  tr.appendChild(cell("", "cell-date"));
}

function row(boss_name, data) {
  const tr = document.createElement("tr");
  tr.appendChild(cell(boss_name, "player-cell"));
  if (!data["rank_players"]) {
    add_dummy_cells(tr);
    return tr;
  };

  tr.appendChild(cell(split_thousands(data["rank_players"]), "cell-rank"));
  tr.appendChild(cell_points(data["points"]));
  tr.appendChild(cell(format_dps(data["dps_max"]), "cell-dps"));
  tr.appendChild(cell(format_duration(data["fastest_kill_duration"]), "cell-dur"));
  tr.appendChild(cell(split_thousands(data["raids"]), "cell-raids"));
  tr.appendChild(cell_date(data["report_id"]));

  tr.setAttribute("data-boss-name", boss_name);
  tr.addEventListener("mouseenter", row_on_enter);
  tr.addEventListener("mouseleave", () => TOOLTIP_POINTS.style.display = "none");
  
  return tr;
}

function set_new_player_name() {
  const name = CURRENT_CHARACTER.name;
  const server = CURRENT_CHARACTER.server;
  PLAYER_SERVER.textContent = server;
  PLAYER_NAME.textContent = name;
  const armory_function = SERVER_ARMORY_FUNCTIONS[server];
  if (armory_function) {
    PLAYER_NAME.href = armory_function(name);
    PLAYER_NAME.target = "_blank";
  } else {
    PLAYER_NAME.removeAttribute("href");
    PLAYER_NAME.removeAttribute("target");
  }
}

function push_new_state() {
  SPEC_BUTTONS[CURRENT_CHARACTER.spec - 1].input.checked = true;
  
  if (CURRENT_CHARACTER.popped) return;
  
  window.localStorage.setItem("character_spec", CURRENT_CHARACTER.spec);
  CURRENT_CHARACTER.popped = false;

  const url = `?${CURRENT_CHARACTER.to_url_params()}`;
  history.pushState(null, "", url);
}
function refresh_spec_icons() {
  const class_i = CURRENT_CHARACTER.class_i * 4;
  PLAYER_NAME.className = SPECS[class_i][2];
  for (const spec_button of SPEC_BUTTONS) {
    const img_element = spec_button.label.querySelector("img");
    const icon_name = SPECS[class_i + spec_button.index][1];
    img_element.src = `/static/icons/${icon_name}.jpg`;
  }
}
function table_add_new_data(data) {
  push_new_state();

  TBODY_POINTS.innerHTML = "";
  const boss_data = data.bosses;
  for (const boss_name in boss_data) {
    const tr = row(boss_name, boss_data[boss_name]);
    TBODY_POINTS.appendChild(tr);
  }
  
  const overall_points = add_point(data.overall_points);
  PLAYER_OVERALL_POINTS.textContent = overall_points;
  PLAYER_OVERALL_POINTS.className = points_rank_class(overall_points);
  PLAYER_OVERALL_RANK.textContent = `(${data.overall_rank ?? 0})`;
  
  INFO_MISSING_POINTS.style.display = "none";
  INFO_LOADING_POINTS.style.display = "none";
  SPEC_SWAP_WRAP.style.removeProperty("visibility");
  SECTION_PLAYER_POINTS_WRAP.style.removeProperty("display");
  
  if (data.class_i == CURRENT_CHARACTER.class_i) return;
  
  CURRENT_CHARACTER.class_i = data.class_i;
  refresh_spec_icons();
}

function query_server() {
  CHAR_REQUEST.open("POST", "/character");
  CHAR_REQUEST.setRequestHeader("Content-Type", "application/json");
  CHAR_REQUEST.send(CURRENT_CHARACTER.json());
  loading_timeout = setTimeout(() => {
    // prevents content flickering
    SECTION_PLAYER_POINTS_WRAP.style.display = "none";
    INFO_MISSING_POINTS.style.display = "none";
    INFO_LOADING_POINTS.style.removeProperty("display");
  }, 100);
}
function fetch_data() {
  const data = CACHE_CHARACTERS.current();
  data ? table_add_new_data(data) : query_server();
}

function new_spec(spec) {
  CURRENT_CHARACTER.spec = spec;
  CURRENT_CHARACTER.popped = false;
  fetch_data();
}
function toggle_more_bosses(e) {
  let show = window.localStorage.getItem("show-more-bosses") == "true";
  if (e) {
    show = !show;
    window.localStorage.setItem("show-more-bosses", show);
  }
  if (show) {
    TBODY_POINTS.classList.remove("hide-other-bosses");
  } else {
    TBODY_POINTS.classList.add("hide-other-bosses");
  }
  BUTTON_TOGGLE_MORE_BOSSES.textContent = show ? "Hide other bosses" : "Show other bosses";
}

function find_value_index(select, option_name) {
  for (let i = 0; i < select.childElementCount; i++) {
    if (select[i].textContent == option_name) return i;
  }
}
function set_current_server() {
  SELECT_SERVER.selectedIndex = find_value_index(SELECT_SERVER, CURRENT_CHARACTER.server);
}
function new_character() {
  set_new_player_name();
  set_current_server();

  const gear = new Gear(CURRENT_CHARACTER.server, CURRENT_CHARACTER.name);
  gear.init();
  
  fetch_data();
}

function to_title(string) {
  return string.charAt(0).toUpperCase() + string.substr(1).toLowerCase();
}
function new_character_search() {
  const _character_name = INPUT_CHAR.value.length > 1 ? INPUT_CHAR.value : PLAYER_NAME.textContent;
  const character_name = to_title(_character_name);
  const character_server = SELECT_SERVER.value;

  CURRENT_CHARACTER.name = character_name;
  CURRENT_CHARACTER.server = character_server;
  CURRENT_CHARACTER.spec = undefined;

  window.localStorage.setItem("character_name", character_name);
  window.localStorage.setItem("character_server", character_server);

  new_character();
}

function init_character() {
  const search = new URLSearchParams(window.location.search);
  let character_name = search.get("name");
  let character_server = search.get("server");
  let character_spec = search.get("spec");
  
  if (!character_name || !character_server) {
    character_name = window.localStorage.getItem("character_name");
    character_server = window.localStorage.getItem("character_server");
    character_spec = window.localStorage.getItem("character_spec");
  }
  
  if (!character_name || !character_server) {
    character_name = "Safiyah";
    character_server = "Lordaeron";
    character_spec = 3;
  }

  CURRENT_CHARACTER.name = character_name;
  CURRENT_CHARACTER.server = character_server;
  CURRENT_CHARACTER.spec = character_spec;

  new_character();
}

function popstate() {
  const search = new URLSearchParams(window.location.search);
  if (!search.get("name")) return;
  
  ["name", "server", "spec"].forEach(k => {
    const value = search.get(k);
    CURRENT_CHARACTER[k] = value;
  });

  CURRENT_CHARACTER.popped = true;

  new_character();
}

function invalid_character_name() {
  return !INPUT_CHAR.value.length || PLAYER_NAME.textContent == INPUT_CHAR.value;
}

function init() {
  init_character();
  toggle_more_bosses();
  
  window.addEventListener("popstate", popstate);
  BUTTON_TOGGLE_MORE_BOSSES.addEventListener("click", toggle_more_bosses);
  for (const spec_button of SPEC_BUTTONS) {
    spec_button.input.addEventListener("click", () => new_spec(spec_button.index));
  }
  INPUT_CHAR.addEventListener("keydown", event => {
    const key = [event.key, event.code];
    if (key.includes("Space")) {
      event.preventDefault();
    } else if (key.includes("Enter")) {
      if (invalid_character_name()) return;
      new_character_search();
    }
  });
  INPUT_CHAR.addEventListener("input", event => {
    if (event.inputType !== "insertFromPaste") return;
    event.preventDefault();
    INPUT_CHAR.value = event.data.replaceAll(" ", "").slice(0, 12);
  });
  PLAYER_SEARCH.addEventListener("change", () => {
    if (PLAYER_SEARCH.checked) {
      INPUT_CHAR.value = "";
      return;
    }
    if (invalid_character_name()) return;
    new_character_search();
  });
  SELECT_SERVER.addEventListener("change", () => new_character_search());
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
