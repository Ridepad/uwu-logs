import {
  BOSSES,
  CLASSES,
  SPECS,
  SPECS_SELECT_OPTIONS,
  AURAS_ICONS,
  MONTHS,
} from "./constants.js"

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
const HEAD_USEFUL_DPS = document.getElementById('head-useful-dps');
const TOGGLE_TOTAL_DAMAGE = document.getElementById('toggle-total-damage');
const TOGGLE_USEFUL_DAMAGE = document.getElementById('toggle-useful-damage');
const TOGGLE_LIMIT = document.getElementById('toggle-limit');
const THE_TOOLTIP = document.getElementById("the-tooltip");
const THE_TOOLTIP_BODY = document.getElementById("tooltip-body");

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
const LOCAL_STORAGE_KEYS = {
  [SELECT_SERVER.id]: "top_server",
  [SELECT_RAID.id]: "top_raid",
  [SELECT_BOSS.id]: "top_boss",
  [SELECT_CLASS.id]: "top_class",
  [SELECT_SPEC.id]: "top_spec",
  [TOGGLE_TOTAL_DAMAGE.id]: "top_total",
  [TOGGLE_USEFUL_DAMAGE.id]: "top_useful",
  [TOGGLE_LIMIT.id]: "top_limit",
}

const IRRELEVANT_FOR_POINTS = [
  SELECT_SIZE,
  CHECKBOX_DIFFICULTY,
  CHECKBOX_COMBINE,
  TOGGLE_TOTAL_DAMAGE,
  TOGGLE_USEFUL_DAMAGE,
];

const ROW_LIMIT = 1000;
const is_landscape = window.matchMedia("(orientation: landscape)");
const TOP_POST = window.location.pathname;
const xrequest = new XMLHttpRequest();
const HAS_HEROIC = new Set([
  ...BOSSES["Icecrown Citadel"],
  ...BOSSES["Trial of the Crusader"],
  "Halion",
  "Points",
]);
const POINTS = [100, 99, 95, 90, 75, 50, 25, 0];
const DEFAULT_SPEC = [3, 1, 2, 2, 3, 3, 2, 1, 2, 2];
const SORT_VARS = {
  column: HEAD_USEFUL_DPS,
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
const POSTS = {
  "Points": "/top_points",
  "Speedrun": "/top_speedrun",
}
const CACHE = {
  lastQuery: "",
  set_new_data(data) {
    const query = make_query();
    if (query == this.lastQuery) {
      this[query] = data;
    }
  },
  get_current() {
    const query = make_query();
    return this[query];
  }
};

function get_icon_link(icon_name) {
  return `/static/icons/${icon_name}.jpg`;
}

function heroic_toggled() {
  return HAS_HEROIC.has(SELECT_BOSS.value) && CHECKBOX_DIFFICULTY.checked;
}
function points_selected() {
  return SELECT_RAID.value == "Points";
}
function speedrun_selected() {
  return SELECT_RAID.value == "Speedrun";
}

function make_query() {
  const size = SELECT_SIZE.value;
  const diff = heroic_toggled() ? 'H' : 'N';
  const mode = `${size}${diff}`;
  const q = {
    server: SELECT_SERVER.value,
    boss: SELECT_BOSS.value,
    mode: mode,
    best_only: CHECKBOX_COMBINE.checked,
    class_i: SELECT_CLASS.value,
    spec_i: SELECT_SPEC.value,
    sort_by: SORT_VARS.column.id,
    limit: TOGGLE_LIMIT.checked ? 1000 : 10000,
  };
  console.log("Query:", q);
  return JSON.stringify(q);
}


function table_modify_wrap(callback) {
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


function create_css_rule(key) {
  const style = document.createElement("style");
  style.append(`.table-${key} {display: none}`);
  return style;
}
const hide_total = create_css_rule("d");
const hide_useful = create_css_rule("u");

function toggle_columns(checkbox, style) {
  if (checkbox.checked) {
    if (style.parentNode != document.head) return;
    table_modify_wrap(() => document.head.removeChild(style));
  } else if (style.parentNode != document.head) {
    table_modify_wrap(() => document.head.appendChild(style));
  }
}

function toggle_useful_columns() {
  toggle_columns(TOGGLE_USEFUL_DAMAGE, hide_useful);
}

function toggle_total_columns() {
  toggle_columns(TOGGLE_TOTAL_DAMAGE, hide_total);
}


function number_with_separator(x, sep = " ") {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}

function add_inner_text(cell, text) {
  if (!isNaN(text)) text = number_with_separator(text);
  cell.append(text);
}

function cell_name(name, spec) {
  const [spec_name, spec_icon, spec_class_id] = SPECS[spec];

  const cell = document.createElement('td');
  cell.classList.add("table-n");
  cell.title = spec_name;

  const img = document.createElement("img");
  img.src = get_icon_link(spec_icon);
  cell.appendChild(img);

  const a = document.createElement('a');
  a.classList.add(spec_class_id);
  a.href = `/character?name=${name}&server=${SELECT_SERVER.value}&spec=${spec % 4}`;
  a.target = "_blank";
  a.append(name);
  cell.appendChild(a);

  return cell;
}

function cell_dps(dps, key) {
  const cell = document.createElement('td');
  cell.value = dps;
  cell.classList.add("table-dps");
  cell.classList.add(`table-${key}`);
  const _inside_data = dps.toFixed(1);
  add_inner_text(cell, _inside_data);
  return cell;
}

function cell_total(amount, key) {
  const cell = document.createElement('td');
  cell.value = amount;
  cell.classList.add("table-dmg");
  cell.classList.add(`table-${key}`);
  add_inner_text(cell, amount);
  // row.appendChild(cell);
  return cell;
}

function format_duration(dur) {
  const minutes = Math.floor(dur / 60);
  const seconds = Math.floor(dur % 60);
  const m_str = minutes.toString().padStart(2, '0');
  const s_str = seconds.toString().padStart(2, '0');
  return `${m_str}:${s_str}`;
}

function cell_duration(value) {
  const cell = document.createElement('td');
  cell.value = value;
  cell.className = `table-t`;
  cell.append(format_duration(value));
  return cell;
}

function cell_date(report_ID) {
  const report_date = report_ID.toString().slice(0, 15);
  const [year, month, day, _, hour, minute] = report_date.split('-');
  const months_str = MONTHS[month - 1];
  const date_text = is_landscape.matches ? `${day} ${months_str} ${year} ${hour}:${minute}` : `${day} ${months_str} ${year}`;

  const a = document.createElement('a');
  a.href = `/reports/${report_ID}`;
  a.target = "_blank";
  a.append(date_text);

  const cell = document.createElement('td');
  cell.appendChild(a);
  cell.className = `table-r`;
  cell.value = report_date.replaceAll('-', '');
  return cell;
}

let timeout_hide;
let timeout_show_rows;
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
    cell: aura_cell(column_class),
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
    column_data.cell.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
  }
  return columns;
}
function* cell_auras(auras) {
  const columns = new_aura_columns(auras);
  for (const column_name in columns) {
    const column_data = columns[column_name];
    const td = column_data.cell;
    if (column_data.count != 0) {
      td.append(column_data.count);
      td.addEventListener("mouseleave", mouseleave);
      td.addEventListener("mouseenter", mouseenter);
    }
    yield td;
  }
}

function new_row(_data) {
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
  const cell = document.createElement('td');
  cell.classList.add("table-points");
  if (!is_total) {
    v = v.toFixed(2);
    cell.classList.add((points_rank_class(v)));
  }
  cell.append(v);
  return cell;
}
function new_row_points(data, spec) {
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


function update_progress(done, total, network) {
  const percent = Math.round(done / total * 100);
  if (network) {
    done = `${(done / 1024).toFixed(1)}k`;
    total = `${(total / 1024).toFixed(1)}k`;
  }
  PROGRESS_BAR_PERCENTAGE.textContent = `${done} / ${total} (${percent}%)`;
  PROGRESS_BAR.style.width = `${percent}%`;
}

let mainTimeout;

function _new_row() {
  const class_i = parseInt(SELECT_CLASS.value);
  const spec_i = parseInt(SELECT_SPEC.value);
  const spec_full_index = class_i * 4 + spec_i;
  if (points_selected()) {
    return data => new_row_points(data, spec_full_index);
  }
  return new_row;
}

function finish(table_body, body_fragment) {
  LOADING_INFO.textContent = "Rendering table...";
  PROGRESS_BAR_PERCENTAGE.textContent = "Done!";

  setTimeout(() => {
    console.time("table_add_new_data Rendering");
    table_body.append(body_fragment);
    toggle_useful_columns();
    toggle_total_columns();
    setTimeout(() => {
      LOADING_INFO_PANEL.style.display = "none";
      TABLE_CONTAINER.style.removeProperty("display");
      console.timeEnd("table_add_new_data Rendering");
      console.timeEnd("tableAddRows");
    });
  })
}
function table_add_new_data(table_body, data) {
  clearTimeout(mainTimeout);
  console.time("clear table");
  table_body.innerHTML = "";
  console.timeEnd("clear table");
  if (!data) return;
  
  console.log(data.length);
  
  const fragment = new DocumentFragment();
  LOADING_INFO.textContent = "Building table...";
  LOADING_INFO_PANEL.style.removeProperty("display");
  const LIMIT = TOGGLE_LIMIT.checked ? Math.min(ROW_LIMIT, data.length) : data.length;
  let current_row_index = 0;
  const _row = _new_row();
  console.time("tableAddRows");

  (function chunk() {
    update_progress(current_row_index, LIMIT);

    if (current_row_index >= LIMIT) return finish(table_body, fragment);

    const end = Math.min(current_row_index + 100, LIMIT);
    for (; current_row_index < end; current_row_index++) {
      const row = _row(data[current_row_index]);
      fragment.appendChild(row);
    }

    mainTimeout = setTimeout(chunk);
  })();
}
function get_cur_table() {
  if (points_selected()) return TABLE_POINTS;
  else if (speedrun_selected()) return TABLE_SPEEDRUN;
  else return TABLE_TOP;
}
function hide_other_tables(current_table) {
  TABLES.forEach(t => {
    if (t.id == current_table.id) return;
    t.style.display = "none";
  });
}
function table_add_new_data_wrap(data) {
  TABLE_CONTAINER.style.display = "none";

  const current_table = get_cur_table();
  hide_other_tables(current_table);
  
  current_table.style.removeProperty("display");
  const body = current_table.querySelector("tbody");
  console.time("JSONparse");
  data = JSON.parse(data);
  console.timeEnd("JSONparse");
  setTimeout(() => table_add_new_data(body, data));
}

xrequest.onprogress = e => {
  let contentLength;
  if (e.lengthComputable) {
    contentLength = e.total;
  } else {
    contentLength = parseInt(e.target.getResponseHeader('Content-Length-Full'));
  }
  update_progress(e.loaded, contentLength, true);
};

xrequest.onreadystatechange = () => {
  if (xrequest.readyState != 4) return;
  if (xrequest.status == 422) {
    TABLE_CONTAINER.style.removeProperty("display");
    LOADING_INFO_PANEL.style.display = "none";
    return;
  }
  if (xrequest.status != 200) return;

  table_add_new_data_wrap(xrequest.response);
}

function query_server(query) {
  LOADING_INFO.textContent = "Downloading top:";
  TABLE_CONTAINER.style.display = "none";
  LOADING_INFO_PANEL.style.removeProperty("display");
  console.timeEnd("query");
  console.time("query");
  xrequest.abort();
  update_progress(0, 1);
  const post_endpoint = POSTS[SELECT_BOSS.value] ?? TOP_POST;
  xrequest.open("POST", post_endpoint);
  xrequest.setRequestHeader("Content-Type", "application/json");
  xrequest.send(query);
}

function fetch_data() {
  const query = make_query();
  console.log(query);
  const data = CACHE[query];
  data ? table_add_new_data_wrap(data) : query_server(query);
}

function search_changed() {
  const __diff = heroic_toggled() ? 'H' : "N";
  const title = `UwU Logs - Top - ${SELECT_BOSS.value} - ${SELECT_SIZE.value}${__diff}`;
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

  fetch_data();
}

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

function local_storage_key(elm) {
  return LOCAL_STORAGE_KEYS[elm.id]
}
function local_storage_get(elm) {
  const key = local_storage_key(elm);
  return localStorage.getItem(key);
}
function local_storage_set(elm, value) {
  const key = local_storage_key(elm);
  return localStorage.setItem(key, value);
}

function fetch_column(event) {
  SORT_VARS.column = event.target;
  fetch_data();
}


function new_option(value, index) {
  const _option = document.createElement('option');
  _option.value = index === undefined ? value : index;
  _option.innerHTML = value;
  return _option;
}

function on_change_instance() {
  SELECT_BOSS.innerHTML = "";
  BOSSES[SELECT_RAID.value].forEach(boss_name => SELECT_BOSS.appendChild(new_option(boss_name)));

  const _points_selected = points_selected();
  IRRELEVANT_FOR_POINTS.forEach(e => e.disabled = _points_selected);
  
  if (_points_selected && SELECT_CLASS.selectedIndex == 0) {
    SELECT_CLASS.selectedIndex = 1;
    add_specs();
  }
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
    e.preventDefault();
    SELECT_CLASS.selectedIndex = 1;
  }

  add_specs();
}

function set_default_spec() {
  SELECT_SPEC.selectedIndex = DEFAULT_SPEC[SELECT_CLASS.value];
}
function check_spec() {
  if (points_selected() && SELECT_SPEC.value == -1) {
    SELECT_SPEC.selectedIndex = DEFAULT_SPEC[SELECT_CLASS.value];
  }
}

function set_new_server_default() {
  localStorage.setItem('top_server', SELECT_SERVER.value);
}

function add_extra_function() {
  SELECT_RAID.addEventListener('change', on_change_instance);
  SELECT_CLASS.addEventListener('change', add_specs);
  SELECT_SPEC.addEventListener('change', check_spec);
  SELECT_SERVER.addEventListener('change', set_new_server_default);
}
function add_refresh_on_change() {
  for (const elm of Object.values(INTERACTABLES)) {
    elm.addEventListener('change', search_changed);
  }
}
function add_toggle_functions(toggle, callback) {
  toggle.addEventListener('change', () => {
    local_storage_set(toggle, toggle.checked);
    callback();
  });
}

function parse_custom() {
  TOGGLE_TOTAL_DAMAGE.checked = local_storage_get(TOGGLE_TOTAL_DAMAGE) == "false" ? false : is_landscape.matches;
  TOGGLE_USEFUL_DAMAGE.checked = local_storage_get(TOGGLE_USEFUL_DAMAGE) == "false" ? false : true;
  TOGGLE_LIMIT.checked = local_storage_get(TOGGLE_LIMIT) == "false" ? false : true;
  
  const _server = local_storage_get(SELECT_SERVER) || "Lordaeron";
  SELECT_SERVER.selectedIndex = find_value_index(SELECT_SERVER, _server);
}

function shorten_aura_column_names() {
  if (is_landscape.matches) return;

  Array.from(document.querySelectorAll("thead .table-auras")).forEach(th => {
    th.textContent = th.textContent.charAt(0);
  });
}



function init() {
  Object.keys(BOSSES).forEach(name => SELECT_RAID.appendChild(new_option(name)));
  CLASSES.forEach((name, i) => SELECT_CLASS.appendChild(new_option(name, i)));
  
  console.log(window.location.search);
  const currentParams = new URLSearchParams(window.location.search);
  console.log(currentParams);
  if (window.location.search == "") {
    console.log("currentParams empty");
  } else {
    console.log("currentParams");
  }

  for (const key in INTERACTABLES) {
    const value = currentParams.get(key);
    const elm = INTERACTABLES[key];
    console.log(key, value, elm);
    if (elm.nodeName == "INPUT") {
      elm.checked = value == 1;
    } else if (elm.nodeName == "SELECT") {
      elm.selectedIndex = find_select_index(elm, value);
    } else {
      console.log("! Wrong element type:", elm, value);
    }
  }

  shorten_aura_column_names();
  
  on_change_instance();
  on_change_class();

  add_extra_function();
  add_refresh_on_change();

  add_toggle_functions(TOGGLE_TOTAL_DAMAGE, toggle_total_columns);
  add_toggle_functions(TOGGLE_USEFUL_DAMAGE, toggle_useful_columns);
  add_toggle_functions(TOGGLE_LIMIT, fetch_data);

  search_changed();
  document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', fetch_column));
}

document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);