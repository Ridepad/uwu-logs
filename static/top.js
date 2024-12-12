import {
  BOSSES,
  CLASSES,
  SPECS,
  SPECS_SELECT_OPTIONS,
  MONTHS,
} from "./constants.js?v=240909-1";

console.time("aura_icons fetch");
const AURAS_ICONS = await fetch("/static/aura_icons.json").then(response => response.json());
console.timeEnd("aura_icons fetch");

const SELECT_SERVER = document.getElementById('select-server');
const SELECT_RAID = document.getElementById('select-instance');
const SELECT_BOSS = document.getElementById('select-boss');
const SELECT_SIZE = document.getElementById('select-size');
const SELECT_CLASS = document.getElementById('select-class');
const SELECT_SPEC = document.getElementById('select-spec');
const CHECKBOX_DIFFICULTY = document.getElementById('checkbox-difficulty');
const CHECKBOX_COMBINE = document.getElementById('checkbox-combine');

const TABLE_TOP = document.getElementById("table-top");
const TABLE_POINTS = document.getElementById("table-points");
const TABLE_SPEEDRUN = document.getElementById("table-speedrun");
const PROGRESS_BAR = document.getElementById('upload-progress-bar');
const PROGRESS_BAR_PERCENTAGE = document.getElementById('upload-progress-bar-percentage');
const TABLE_CONTAINER = document.getElementById('table-container');
const LOADING_INFO = document.getElementById('loading-info');
const LOADING_INFO_PANEL = document.getElementById('loading-info-panel');
const TOGGLE_TOTAL_DAMAGE = document.getElementById('toggle-total-damage');
const TOGGLE_USEFUL_DAMAGE = document.getElementById('toggle-useful-damage');
const TOGGLE_LIMIT = document.getElementById('toggle-limit');
const TOGGLE_EXTERNALS = document.getElementById('toggle-externals');
const THE_TOOLTIP = document.getElementById("the-tooltip");
const THE_TOOLTIP_BODY = document.getElementById("tooltip-body");
const SECTION_NO_DATA = document.getElementById("no-data");
const SECTION_ON_ERROR = document.getElementById("on-error");
const SECTION_ON_ERROR_DETAILS = document.getElementById("on-error-details");

const HEAD_USEFUL_DPS_ID = "head-useful-dps";
const HEAD_SPEEDRUN_TOTAL_LENGTH_ID = "head-speedrun-total-length";

const AURAS_CURRENT_COLUMNS = Array.from(document.querySelectorAll("thead .table-auras")).map(e => e.classList[1]);
const AURA_INDEX_TO_COLUMN_NAME = {
  0: "table-ext",
  1: "table-self",
  2: "table-rekt",
  3: "table-cls",
}

const INTERACTABLES = {
  server: SELECT_SERVER,
  raid: SELECT_RAID,
  boss: SELECT_BOSS,
  size: SELECT_SIZE,
  mode: CHECKBOX_DIFFICULTY,
  best: CHECKBOX_COMBINE,
  cls: SELECT_CLASS,
  spec: SELECT_SPEC,
};

const LOCAL_STORAGE = {
  keys: {
    [SELECT_SERVER.id]: "top_server",
    [SELECT_RAID.id]: "top_raid",
    [SELECT_BOSS.id]: "top_boss",
    [SELECT_CLASS.id]: "top_class",
    [SELECT_SPEC.id]: "top_spec",
    [TOGGLE_TOTAL_DAMAGE.id]: "top_total",
    [TOGGLE_USEFUL_DAMAGE.id]: "top_useful",
    [TOGGLE_LIMIT.id]: "top_limit",
    [TOGGLE_EXTERNALS.id]: "top_externals",
  },
  get(elm) {
    const key = this.convert_key(elm);
    return localStorage.getItem(key);
  },
  set(elm, value) {
    const key = this.convert_key(elm);
    return localStorage.setItem(key, value);
  },
  convert_key(elm) {
    return this.keys[elm.id];
  },
}

const IRRELEVANT_FOR_POINTS = [
  INTERACTABLES.size,
  INTERACTABLES.best,
  TOGGLE_TOTAL_DAMAGE,
  TOGGLE_USEFUL_DAMAGE,
  TOGGLE_EXTERNALS,
];
const IRRELEVANT_FOR_SPEEDRUN = [
  INTERACTABLES.size,
  INTERACTABLES.best,
  INTERACTABLES.cls,
  INTERACTABLES.spec,
  INTERACTABLES.best,
  TOGGLE_TOTAL_DAMAGE,
  TOGGLE_USEFUL_DAMAGE,
  TOGGLE_EXTERNALS,
];

const ROW_LIMIT = 1000;
const is_landscape = window.matchMedia("(orientation: landscape)");
const TOP_POST = window.location.pathname;
const BOSSES_WITH_HEROIC_MODE = new Set([
  "Halion",
  "XT-002 Deconstructor",
  "Assembly of Iron",
  "Freya",
  "Thorim",
  "Mimiron",
  "General Vezax",
  "Yogg-Saron",
]);
const RAID_WITH_HEROIC_MODE = new Set([
  "Icecrown Citadel",
  "Trial of the Crusader",
]);
const POINTS = [100, 99, 95, 90, 75, 50, 25, 0];
const DEFAULT_SPEC = [3, 1, 2, 2, 3, 3, 2, 1, 2, 2];
const SORT_VARS = {
  last_column_sort: {
    [TABLE_TOP.id]: HEAD_USEFUL_DPS_ID,
    [TABLE_SPEEDRUN.id]: HEAD_SPEEDRUN_TOTAL_LENGTH_ID,
  },
  reversed: false,
};
const DATA_KEYS = {
  reportID: "r",
  guid: "i",
  name: "n",
  spec: "s",
  uAmount: "u",
  tAmount: "d",
  duration: "t",
  auras: "a",
}
const TABLES = [
  TABLE_POINTS,
  TABLE_TOP,
  TABLE_SPEEDRUN,
];
const REQUESTS_CACHE = {};

function _css_rule(key) {
  const style = document.createElement("style");
  style.append(`.table-${key} {display: none}`);
  return style;
}
const TOGGLE_COLUMNS = {
  css_hide_total: _css_rule("d"),
  css_hide_useful: _css_rule("u"),
  useful_columns() {
    this._toggle_columns(TOGGLE_USEFUL_DAMAGE, this.css_hide_useful);
  },
  total_columns() {
    this._toggle_columns(TOGGLE_TOTAL_DAMAGE, this.css_hide_total);
  },
  _toggle_columns(checkbox, style) {
    if (checkbox.checked) {
      if (style.parentNode != document.head) return;
      this._table_modify_wrap(() => document.head.removeChild(style));
    } else if (style.parentNode != document.head) {
      this._table_modify_wrap(() => document.head.appendChild(style));
    }
  },
  _table_modify_wrap(callback) {
    if (TABLE_CONTAINER.style.display == "none") return callback();
  
    TABLE_CONTAINER.style.display = "none";
    LOADING_INFO_PANEL.style.removeProperty("display");
    setTimeout(() => {
      callback();
      setTimeout(() => {
        LOADING_INFO_PANEL.style.display = "none";
        TABLE_CONTAINER.style.removeProperty("display");
      });
    });
  }
}

function get_icon_link(icon_name) {
  return `/static/icons/${icon_name}.jpg`;
}
const DEFAULT_ICON = get_icon_link("undefined");
const FACTIONS_ICONS = {
  0: `/static/alliance.png`,
  1: `/static/horde.png`,
}

let timeout_hide;
let timeout_show_rows;
let timeout_table_add_new_data;

//////////////////////////////////////////

function has_heroic() {
  return RAID_WITH_HEROIC_MODE.has(SELECT_RAID.value) || BOSSES_WITH_HEROIC_MODE.has(SELECT_BOSS.value);
}
function toggle_difficulty_checkbox() {
  CHECKBOX_DIFFICULTY.disabled = !has_heroic();
}

function heroic_toggled() {
  return has_heroic() && CHECKBOX_DIFFICULTY.checked;
}
function points_selected() {
  return SELECT_RAID.value == "Points";
}
function speedrun_selected() {
  return SELECT_RAID.value == "Speedrun";
}
// function healing_toggled() {
//   return CHECKBOX_HEALING.checked;
// }

function selected_difficuty() {
  const size = SELECT_SIZE.value;
  const diff = heroic_toggled() ? 'H' : 'N';
  return `${size}${diff}`;
}

function _make_query_top() {
  const mode = selected_difficuty();
  return {
    server: SELECT_SERVER.value,
    boss: SELECT_BOSS.value,
    mode: mode,
    best_only: CHECKBOX_COMBINE.checked,
    class_i: SELECT_CLASS.value,
    spec_i: SELECT_SPEC.value,
    sort_by: SORT_VARS.last_column_sort[TABLE_TOP.id],
    limit: TOGGLE_LIMIT.checked ? 1000 : 10000,
    externals: TOGGLE_EXTERNALS.checked,
  };
}

function _make_query_points() {
  return {
    server: SELECT_SERVER.value,
    class_i: SELECT_CLASS.value,
    spec_i: SELECT_SPEC.value,
    limit: TOGGLE_LIMIT.checked ? 1000 : 10000,
  };
}

function _make_query_speedrun() {
  return {
    server: SELECT_SERVER.value,
    raid: SELECT_BOSS.value,
    sort_by: SORT_VARS.last_column_sort[TABLE_SPEEDRUN.id],
  };
}

function _make_query() {
  if (speedrun_selected()) return _make_query_speedrun();
  if (points_selected()) return _make_query_points();
    return _make_query_top();
}
function make_query() {
  const q = _make_query();
  console.log("Query:", q);
  return JSON.stringify(q);
}


function number_with_separator(x, sep = " ") {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}

function add_inner_text(element, text) {
  if (!isNaN(text)) text = number_with_separator(text);
  element.append(text);
}

function cell_name(name, spec) {
  const [spec_name, spec_icon, spec_class_id] = SPECS[spec];

  const td = document.createElement('td');
  td.classList.add("table-n");
  td.title = spec_name;

  const img = document.createElement("img");
  img.src = get_icon_link(spec_icon);
  td.appendChild(img);

  const a = document.createElement('a');
  a.classList.add(spec_class_id);
  a.href = `/character?name=${name}&server=${SELECT_SERVER.value}&spec=${spec % 4}`;
  a.target = "_blank";
  a.append(name);
  td.appendChild(a);

  return td;
}
function cell_guild(guild_name, faction) {
  const guild_cell = document.createElement('td');
  guild_cell.classList.add("table-n");
  const img = document.createElement("img");
  img.src = FACTIONS_ICONS[faction] ?? DEFAULT_ICON;
  guild_cell.appendChild(img);
  guild_cell.append(guild_name);
  return guild_cell
}

function cell_dps(dps, key) {
  const td = document.createElement('td');
  td.value = dps;
  td.classList.add("table-dps");
  td.classList.add(`table-${key}`);
  const _inside_data = dps.toFixed(1);
  add_inner_text(td, _inside_data);
  return td;
}

function cell_total(amount, key) {
  const td = document.createElement('td');
  td.value = amount;
  td.classList.add("table-dmg");
  td.classList.add(`table-${key}`);
  add_inner_text(td, amount);
  return td;
}

function pad_duration_value(v) {
  return v.toString().padStart(2, '0');
}
function format_duration(dur) {
  const seconds = Math.floor(dur % 60);
  const s_str = pad_duration_value(seconds);
  const minutes = Math.floor(dur / 60);
  const m_str = pad_duration_value(minutes);
  return `${m_str}:${s_str}`;
}
function format_duration_hours(dur) {
  const seconds = Math.floor(dur % 60);
  const s_str = pad_duration_value(seconds);
  const minutes = Math.floor(dur / 60 % 60);
  const m_str = pad_duration_value(minutes);
  const hours = Math.floor(dur / 3600);
  const h_str = pad_duration_value(hours);
  return `${h_str}:${m_str}:${s_str}`;
}

function cell_duration(value) {
  const td = document.createElement('td');
  td.value = value;
  td.className = `table-t`;
  td.append(format_duration(value));
  return td;
}
function cell_duration_hours(value) {
  const td = document.createElement('td');
  td.value = value;
  td.className = `table-bt`;
  td.append(format_duration_hours(value));
  return td;
}

function cell_date(report_ID) {
  const report_date = report_ID.toString().slice(0, 15);
  const [year, month, day, _, hour, minute] = report_date.split('-');
  const months_str = MONTHS[month - 1];
  const date_text = is_landscape.matches ? `${day} ${months_str} ${year} ${hour}:${minute}` : `${day} ${months_str} ${year}`;

  const a = document.createElement('a');
  const boss = SELECT_BOSS.value.toLowerCase().replaceAll(" ", "-");
  const link_root = `/reports/${report_ID}--${SELECT_SERVER.value}`;
  const link_query = `?boss=${boss}&mode=${selected_difficuty()}&attempt=kill`;
  a.href = `${link_root}/${link_query}`;
  a.target = "_blank";
  a.append(date_text);

  const td = document.createElement('td');
  td.appendChild(a);
  td.className = `table-r`;
  td.value = report_date.replaceAll('-', '');
  return td;
}

function show_tooltip(td) {
  clearTimeout(timeout_show_rows);
  const dataset = td.dataset;
  const keys = Object.keys(dataset);
  const rows = Array.from(THE_TOOLTIP_BODY.children);
  for (const i in keys) {
    const tr = rows[i];
    const spell_id = keys[i];
    const [count, uptime] = dataset[spell_id].split(',');

    const img = tr.querySelector("img");
    img.src = get_icon_link(AURAS_ICONS[spell_id]);
    img.alt = spell_id;

    tr.querySelector(".count").textContent = count;
    tr.querySelector(".uptime").textContent = `${parseFloat(uptime).toFixed(1)}%`;
  }
  timeout_show_rows = setTimeout(() => {
    for (const i in rows) {
      const tr = rows[i];
      if (i < keys.length) {
        tr.classList.remove("hidden");
      } else {
        tr.classList.add("hidden");
      }
    }
  }, TOGGLE_LIMIT.checked ? 10 : 150);
}
function mouseenter(event) {
  clearTimeout(timeout_hide);
  const td = event.target;
  show_tooltip(td);
  const bodyRect = document.body.getBoundingClientRect();
  const trRect = td.getBoundingClientRect();
  THE_TOOLTIP.style.top = `${trRect.bottom}px`;
  THE_TOOLTIP.style.right = `${bodyRect.right - trRect.left}px`;
  THE_TOOLTIP.style.removeProperty("display");
}
function mouseleave() {
  clearTimeout(timeout_hide);
  timeout_hide = setTimeout(() => {
    THE_TOOLTIP.style.display = "none"
  }, 300);
}

function aura_cell(column_class) {
  const td = document.createElement('td');
  td.className = column_class;
  return td;
}
function aura_column_data(column_class) {
  return {
    count: 0,
    td: aura_cell(column_class),
  }
}
function new_aura_empty_columns() {
  return Object.fromEntries(
    AURAS_CURRENT_COLUMNS.map(column_class => [column_class, aura_column_data(column_class)])
  );
}
function new_aura_columns(auras) {
  const columns = new_aura_empty_columns();
  for (const [spell_id, count, uptime, type] of auras) {
    const column_name = AURA_INDEX_TO_COLUMN_NAME[type];
    const column_data = columns[column_name];
    column_data.count += count;
    column_data.td.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
  }
  return columns;
}
function* cell_auras(auras) {
  const columns = new_aura_columns(auras);
  for (const column_name in columns) {
    const column_data = columns[column_name];
    const td = column_data.td;
    if (column_data.count != 0) {
      td.append(column_data.count);
      td.addEventListener("mouseleave", mouseleave);
      td.addEventListener("mouseenter", mouseenter);
    }
    yield td;
  }
}

function table_new_row_default(_data) {
  const row = document.createElement('tr');
  const [
    report_ID,
    duration,
    guid,
    name,
    uAmount,
    tAmount,
    spec,
    auras,
  ] = _data;

  [
    cell_name(name, spec),
    cell_dps(uAmount / duration, DATA_KEYS.uAmount),
    cell_total(uAmount, DATA_KEYS.uAmount),
    cell_dps(tAmount / duration, DATA_KEYS.tAmount),
    cell_total(tAmount, DATA_KEYS.tAmount),
    cell_duration(duration),
    ...cell_auras(auras),
    cell_date(report_ID),
  ].forEach(td => row.appendChild(td));

  return row;
}

function points_rank_class(v) {
  for (const i of POINTS) if (v - i >= 0) return `top${i}`;
}
function cell_points(v, is_total) {
  const td = document.createElement('td');
  td.classList.add("table-points");
  if (!is_total) {
    v = v.toFixed(2);
    td.classList.add((points_rank_class(v)));
  }
  td.append(v);
  return td;
}
function table_new_row_points(data, spec) {
  const row = document.createElement('tr');
  const [
    name,
    p_relative,
    p_total,
  ] = data;

  [
    cell_name(name, spec),
    cell_points(p_relative),
    cell_points(Math.floor(p_total), true),
  ].forEach(td => row.appendChild(td));

  return row;
}
function table_new_row_speedrun(data) {
  const row = document.createElement('tr');
  const [
    report_id,
    total_length,
    segments_sum,
    guild_name,
    faction,
  ] = data;

  [
    cell_guild(guild_name, faction),
    cell_duration_hours(total_length),
    cell_duration_hours(segments_sum),
    cell_date(report_id),
  ].forEach(td => row.appendChild(td));

  return row;
}


function update_progress_bar(done, total, network) {
  const percent = Math.round(done / total * 100);
  if (network) {
    done = `${(done / 1024).toFixed(1)}k`;
    total = `${(total / 1024).toFixed(1)}k`;
  }
  PROGRESS_BAR_PERCENTAGE.textContent = `${done} / ${total} (${percent}%)`;
  PROGRESS_BAR.style.width = `${percent}%`;
}

function table_new_row_wrap() {
  const current_table = get_cur_table();
  if (current_table == TABLE_TOP) return table_new_row_default;
  if (current_table == TABLE_SPEEDRUN) return table_new_row_speedrun;
  if (current_table == TABLE_POINTS) {
    const class_i = parseInt(SELECT_CLASS.value);
    const spec_i = parseInt(SELECT_SPEC.value);
    const spec_full_index = class_i * 4 + spec_i;
    return data => table_new_row_points(data, spec_full_index);
  }
  throw Error("no table handler found!");
}

function table_append_fragment(table_body, body_fragment) {
  LOADING_INFO.textContent = "Rendering table...";
  PROGRESS_BAR_PERCENTAGE.textContent = "Done!";

  setTimeout(() => {
    console.time("table_add_new_data | Rendering");
    table_body.append(body_fragment);
    TOGGLE_COLUMNS.useful_columns();
    TOGGLE_COLUMNS.total_columns();
    setTimeout(() => {
      LOADING_INFO_PANEL.style.display = "none";
      TABLE_CONTAINER.style.removeProperty("display");
      console.timeEnd("table_add_new_data | Rendering");
      console.timeEnd("table_add_new_data | Full");
    });
  })
}
function table_add_new_data(table_body, data) {
  clearTimeout(timeout_table_add_new_data);
  console.time("table_add_new_data | Clear Table");
  table_body.innerHTML = "";
  console.timeEnd("table_add_new_data | Clear Table");
  if (!data) return;
  
  console.log(data.length);
  
  const fragment = new DocumentFragment();
  LOADING_INFO.textContent = "Building table...";
  LOADING_INFO_PANEL.style.removeProperty("display");
  const LIMIT = TOGGLE_LIMIT.checked ? Math.min(ROW_LIMIT, data.length) : data.length;
  let current_row_index = 0;
  const table_new_row = table_new_row_wrap();
  console.time("table_add_new_data | Full");

  (function chunk() {
    update_progress_bar(current_row_index, LIMIT);

    if (current_row_index >= LIMIT) return table_append_fragment(table_body, fragment);

    const end = Math.min(current_row_index + 100, LIMIT);
    for (; current_row_index < end; current_row_index++) {
      const row = table_new_row(data[current_row_index]);
      fragment.appendChild(row);
    }

    timeout_table_add_new_data = setTimeout(chunk);
  })();
}
function get_cur_table() {
  if (points_selected()) return TABLE_POINTS;
  if (speedrun_selected()) return TABLE_SPEEDRUN;
  return TABLE_TOP;
}
function hide_other_tables(current_table) {
  TABLES.forEach(t => {
    if (t.id != current_table.id) {
      t.style.display = "none";
    }
  });
}
function table_add_new_data_wrap(data) {
  TABLE_CONTAINER.style.display = "none";

  const current_table = get_cur_table();
  hide_other_tables(current_table);
  
  current_table.style.removeProperty("display");
  const body = current_table.querySelector("tbody");

  setTimeout(() => table_add_new_data(body, data));
}

function get_post_endpoint() {
  if (speedrun_selected()) return "/top_speedrun";
  if (points_selected()) return "/top_points";
  return TOP_POST;
}

const TopRequest = new class extends XMLHttpRequest {
  constructor() {
    super();

    this.onprogress = this._onprogress;
    this.onload = this._onload;
    this.current_query = "";
  }
  get_new_data(query) {
    this.abort();
    update_progress_bar(0, 1);

    this.current_query = query;
    const post_endpoint = get_post_endpoint();
    this.open("POST", post_endpoint);
    this.setRequestHeader("Content-Type", "application/json");
    console.time("TopRequest | Response");
    this.send(query);
  }
  _onprogress(e) {
    const contentLength = e.lengthComputable ? e.total : this._get_full_length();
    update_progress_bar(e.loaded, contentLength, true);
  }
  _get_full_length() {
    return parseInt(this.getResponseHeader('Content-Length-Full'));
  }
  _onload() {
    console.timeEnd("TopRequest | Response");
    LOADING_INFO_PANEL.style.display = "none";

    if (this.status == 500) this.show_error("Server error!"); 
  
    const not_json = this.getResponseHeader("content-type") != "application/json";
    if (not_json) return this.show_error("Server error!");
  
    const data_parsed = this.response_json();
    const current_query = make_query();
    
    if (data_parsed.length != 0) {
      if (current_query != this.current_query) return;
      REQUESTS_CACHE[current_query] = data_parsed;
      table_add_new_data_wrap(data_parsed);
      return;
    }
  
    REQUESTS_CACHE[current_query] = [];
  
    try {
      const error_msg = data_parsed.detail[0].msg;
      return this.show_error(error_msg); 
    } catch (error) {
      return this.show_no_data();
    }
  }
  response_json() {
    console.time("TopRequest | JSONparse");
    const data_parsed = JSON.parse(this.response);
    console.timeEnd("TopRequest | JSONparse");
    return data_parsed;
  }
  show_no_data() {
    SECTION_NO_DATA.style.removeProperty("display");
  }
  show_error(error) {
    SECTION_ON_ERROR.style.removeProperty("display");
    SECTION_ON_ERROR_DETAILS.textContent = error;
  }
}

function new_state() {
  LOADING_INFO.textContent = "Downloading top:";
  TABLE_CONTAINER.style.display = "none";
  SECTION_NO_DATA.style.display = "none";
  SECTION_ON_ERROR.style.display = "none";
  LOADING_INFO_PANEL.style.removeProperty("display");
  
  const query = make_query();
  const data = REQUESTS_CACHE[query];
  data ? table_add_new_data_wrap(data) : TopRequest.get_new_data(query);
}

function fetch_column(event) {
  const current_table = get_cur_table();
  SORT_VARS.last_column_sort[current_table.id] = event.target.id;
  new_state();
}

function push_new_state() {
  const mode = selected_difficuty();
  const title = `UwU Logs - Top - ${SELECT_BOSS.value} - ${mode}`;
  document.title = title;

  const parsed = {
    server: SELECT_SERVER.value,
    raid: SELECT_RAID.value,
    boss: SELECT_BOSS.value,
    size: SELECT_SIZE.value,
    mode: heroic_toggled() ? 1 : 0,
    best: CHECKBOX_COMBINE.checked ? 1 : 0,
    cls: SELECT_CLASS.value,
    spec: SELECT_SPEC.value,
  };

  const new_params = new URLSearchParams(parsed).toString();
  const url = `?${new_params}`;
  history.pushState(parsed, title, url);
}

function state_changed() {
  push_new_state();
  new_state();
}

///////////////////////////////

function find_value_index(select, option_name) {
  for (const e of select.children) {
    if (e.value == option_name) return e.index;
  }
}

function get_default_index(select) {
  switch (select) {
    case SELECT_SERVER:
      return find_value_index(select, "Lordaeron");
    case SELECT_CLASS:
      return find_value_index(select, "Priest");
    case SELECT_SPEC:
      return DEFAULT_SPEC[SELECT_CLASS.value];
    default:
      return 0;
  }
}

function find_select_index(select, value) {
  if (select == SELECT_SPEC && value == -1 && points_selected()) {
    return get_default_index(select);
  }
  return find_value_index(select, value) ?? get_default_index(select);
}

function element_init(elm) {
  switch (elm) {
    case SELECT_RAID:
      return on_change_instance();
    case SELECT_CLASS:
      return on_change_class();
  }
}

function element_set_value(elm, value) {
  if (elm.nodeName == "INPUT") {
    elm.checked = value != 0;
  } else if (elm.nodeName == "SELECT") {
    elm.selectedIndex = find_select_index(elm, value);
    element_init(elm);
  } else {
    console.error("! Wrong element type:", elm, value);
  }
}

function init_from_query(search_params) {
  for (const key in INTERACTABLES) {
    const elm = INTERACTABLES[key];
    const value = search_params.get(key);
    element_set_value(elm, value);
  }
}
function init_from_localstorage() {
  for (const key in INTERACTABLES) {
    const elm = INTERACTABLES[key];
    const value = LOCAL_STORAGE.get(elm);
    element_set_value(elm, value);
  }
}

function add_toggle_functions(toggle, callback) {
  toggle.addEventListener('change', () => {
    LOCAL_STORAGE.set(toggle, toggle.checked);
    callback();
  });
}
function init_other_elements() {
  const show_total = LOCAL_STORAGE.get(TOGGLE_TOTAL_DAMAGE);
  TOGGLE_TOTAL_DAMAGE.checked = show_total == "true" ? true : show_total == "false" ? false : is_landscape.matches;
  TOGGLE_USEFUL_DAMAGE.checked = LOCAL_STORAGE.get(TOGGLE_USEFUL_DAMAGE) != "false";
  TOGGLE_LIMIT.checked = LOCAL_STORAGE.get(TOGGLE_LIMIT) != "false";
  TOGGLE_EXTERNALS.checked = LOCAL_STORAGE.get(TOGGLE_EXTERNALS) != "false";

  add_toggle_functions(TOGGLE_TOTAL_DAMAGE, () => TOGGLE_COLUMNS.total_columns());
  add_toggle_functions(TOGGLE_USEFUL_DAMAGE, () => TOGGLE_COLUMNS.useful_columns());
  add_toggle_functions(TOGGLE_LIMIT, new_state);
  add_toggle_functions(TOGGLE_EXTERNALS, new_state);

  toggle_difficulty_checkbox();
}

///////////////////////////////

function new_option(value, index) {
  const option = document.createElement('option');
  option.value = index === undefined ? value : index;
  option.innerHTML = value;
  return option;
}

function on_change_instance() {
  SELECT_BOSS.innerHTML = "";
  BOSSES[SELECT_RAID.value].forEach(boss_name => SELECT_BOSS.appendChild(new_option(boss_name)));

  const _speedrun_selected = speedrun_selected();
  IRRELEVANT_FOR_SPEEDRUN.forEach(e => e.disabled = _speedrun_selected);

  const _points_selected = points_selected();
  IRRELEVANT_FOR_POINTS.forEach(e => e.disabled = _points_selected);

  toggle_difficulty_checkbox();
  
  if (_points_selected && SELECT_CLASS.selectedIndex == 0) {
    SELECT_CLASS.selectedIndex = 1;
    add_specs();
  }

  LOCAL_STORAGE.set(SELECT_RAID, SELECT_RAID.value);
}

function set_default_spec() {
  SELECT_SPEC.selectedIndex = DEFAULT_SPEC[SELECT_CLASS.value];
}
function add_specs() {
  SELECT_SPEC.innerHTML = "";
  const class_index = CLASSES[SELECT_CLASS.value];
  const specs = SPECS_SELECT_OPTIONS[class_index];
  SELECT_SPEC.appendChild(new_option('All specs', -1));
  if (!specs) return;
  
  specs.forEach((spec_name, i) => SELECT_SPEC.appendChild(new_option(spec_name, i + 1)));

  set_default_spec();
}
function on_change_class(e) {
  if (points_selected() && SELECT_CLASS.selectedIndex == 0) {
    SELECT_CLASS.selectedIndex = 1;
  }

  add_specs();

  if (!e) return;
  LOCAL_STORAGE.set(SELECT_CLASS, SELECT_CLASS.value);
  LOCAL_STORAGE.set(SELECT_SPEC, SELECT_SPEC.value);
}

function on_change_spec() {
  if (points_selected() && SELECT_SPEC.value == -1) {
    SELECT_SPEC.selectedIndex = DEFAULT_SPEC[SELECT_CLASS.value];
  }
  LOCAL_STORAGE.set(SELECT_SPEC, SELECT_SPEC.value);
}

function set_new_server_default() {
  LOCAL_STORAGE.set(SELECT_SERVER, SELECT_SERVER.value);
}

function add_extra_function() {
  SELECT_RAID.addEventListener('change', on_change_instance);
  SELECT_BOSS.addEventListener('change', toggle_difficulty_checkbox);
  SELECT_CLASS.addEventListener('change', on_change_class);
  SELECT_SPEC.addEventListener('change', on_change_spec);
  SELECT_SERVER.addEventListener('change', set_new_server_default);
}

function add_refresh_on_change() {
  for (const elm of Object.values(INTERACTABLES)) {
    elm.addEventListener('change', state_changed);
  }
}

function init() {
  Object.keys(BOSSES).forEach(name => SELECT_RAID.appendChild(new_option(name)));
  CLASSES.forEach((name, i) => SELECT_CLASS.appendChild(new_option(name, i)));
  
  const search_params = new URLSearchParams(window.location.search);
  search_params.size ? init_from_query(search_params) : init_from_localstorage();

  init_other_elements();

  add_extra_function();
  add_refresh_on_change();

  state_changed();
  console.log(SELECT_SPEC);
  
  document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', fetch_column));
}

document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);
