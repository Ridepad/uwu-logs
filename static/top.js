import {
  BOSSES,
  CLASSES,SPECS,
  SPECS_SELECT_OPTIONS,
  AURAS_COLUMNS,
  AURAS_ICONS,
  MONTHS,
} from "./appConstants.js"

const selectServer = document.getElementById('select-server');
const selectInstance = document.getElementById('select-instance');
const selectBoss = document.getElementById('select-boss');
const selectSize = document.getElementById('select-size');
const selectClass = document.getElementById('select-class');
const selectSpec = document.getElementById('select-spec');
const checkboxDifficulty = document.getElementById('checkbox-difficulty');
const checkboxCombine = document.getElementById('checkbox-combine');

const INTERACTABLES = {
  server: selectServer,
  raid: selectInstance,
  boss: selectBoss,
  size: selectSize,
  mode: checkboxDifficulty,
  best: checkboxCombine,
  cls: selectClass,
  spec: selectSpec,
};

const mainTableBody = document.getElementById("main-table-body");
const headDPS = document.getElementById('head-dps');
const progressBar = document.getElementById('upload-progress-bar');
const progressBarPercentage = document.getElementById('upload-progress-bar-percentage');
const tableContainer = document.getElementById('table-container');
const loadingInfo = document.getElementById('loading-info');
const loadingInfoPanel = document.getElementById('loading-info-panel');
const headUsefulDps = document.getElementById('head-useful-dps');
const toggleTotalDamage = document.getElementById('toggle-total-damage');
const toggleUsefulDamage = document.getElementById('toggle-useful-damage');
const toggleLimit = document.getElementById('toggle-limit');
const theTooltip = document.getElementById("the-tooltip");
const theTooltipBody = document.getElementById("tooltip-body");

const LIMITED_ROWS = 1000;
const screenX = window.matchMedia("(orientation: landscape)");
const TOP_POST = window.location.pathname;
const xrequest = new XMLHttpRequest();
const HAS_HEROIC = new Set([
  ...BOSSES["Icecrown Citadel"],
  ...BOSSES["Trial of the Crusader"],
  "Halion",
]);
const REVERSE_SORTED = new Set([
  "head-duration",
  "head-date",
  "head-external",
  "head-rekt",
]);
const SORT_VARS = {column: headUsefulDps, reversed: false};
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
const sort_default = key => (a, b) => b[key] - a[key];
const sort_string = key => (a, b) => b[key] > a[key] ? -1 : 1;
const SORT_FUNC = {
  "head-useful-dps": (a, b) => (b.u/b.t - a.u/a.t),
  "head-total-dps": (a, b) => (b.d/b.t - a.d/a.t),
  "head-useful-amount": sort_default(DATA_KEYS.uAmount),
  "head-total-amount": sort_default(DATA_KEYS.tAmount),
  "head-duration": sort_default(DATA_KEYS.duration),
  "head-date": sort_string(DATA_KEYS.reportID),
  "head-name": sort_string(DATA_KEYS.name),
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

function is_heroic() {
  return HAS_HEROIC.has(selectBoss.value) && checkboxDifficulty.checked;
}

function make_query() {
  const sizeValue = selectSize.value;
  const diffValue = is_heroic() ? 'H' : 'N';
  const diff_str = `${sizeValue}${diffValue}`;
  const q = {
    server: selectServer.value,
    boss: selectBoss.value,
    diff: diff_str,
  };
  return JSON.stringify(q);
}


function table_modify_wrap(callback) {
  if (tableContainer.style.display == "none") return callback();

  tableContainer.style.display = "none";
  loadingInfoPanel.style.removeProperty("display");
  setTimeout(() => {
    callback();
    setTimeout(() => {
      loadingInfoPanel.style.display = "none";
      tableContainer.style.removeProperty("display");
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
  toggle_columns(toggleUsefulDamage, hide_useful);
}
function toggle_total_columns() {
  toggle_columns(toggleTotalDamage, hide_total);
}


function number_with_separator(x, sep=" ") {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}
function add_inner_text(cell, text) {
  if (!isNaN(text)) text = number_with_separator(text);
  cell.append(text);
}

function add_name_cell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];

  const [spec_name, spec_icon, spec_class_id] = SPECS[data[DATA_KEYS.spec]];
  const img = document.createElement("img");
  img.src = get_icon_link(spec_icon);
  cell.appendChild(img);
  cell.append(data_value);
  cell.title = spec_name;
  cell.classList.add("table-n");
  cell.classList.add(spec_class_id);
  row.appendChild(cell);
}

function add_dps_cell(row, data, key) {
  const data_value = data[key];
  const cell = document.createElement('td');
  const dps = data_value / data.t;
  cell.value = dps;
  cell.classList.add("table-dps");
  cell.classList.add(`table-${key}`);
  const _inside_data = dps.toFixed(1);
  add_inner_text(cell, _inside_data);
  row.appendChild(cell);
}

function add_total_cell(row, data, key) {
  const data_value = data[key];
  const cell = document.createElement('td');
  cell.value = data_value;
  cell.classList.add("table-dmg");
  cell.classList.add(`table-${key}`);
  add_inner_text(cell, data_value);
  row.appendChild(cell);
}

function format_duration(dur) {
  const minutes = Math.floor(dur/60);
  const seconds = Math.floor(dur%60);
  const m_str = minutes.toString().padStart(2, '0');
  const s_str = seconds.toString().padStart(2, '0');
  return `${m_str}:${s_str}`;
}
function add_duration_cell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];
  cell.value = data_value;
  cell.className = `table-${key}`;
  cell.append(format_duration(data_value));
  row.appendChild(cell);
}

function add_date_cell(row, data, key) {
  const report_ID = data[key];
  const report_date = report_ID.toString().slice(0, 15);
  const [year, month, day, _, hour, minute] = report_date.split('-');
  const months_str = MONTHS[month - 1];
  const date_text = screenX.matches ? `${day} ${months_str} ${year} ${hour}:${minute}` : `${day}-${month}-${year}`;

  const _a = document.createElement('a');
  _a.href = `/reports/${report_ID}/`;
  _a.target = "_blank";
  _a.append(date_text);

  const cell = document.createElement('td');
  cell.appendChild(_a);
  cell.className = `table-${key}`;
  cell.value = report_date.replaceAll('-', '');
  row.appendChild(cell);
}

function show_tooltip(td) {
  while(theTooltipBody.firstChild) theTooltipBody.removeChild(theTooltipBody.firstChild);
  
  const dataset = td.dataset;
  const fragment = new DocumentFragment();
  const sorted = Object.keys(dataset).sort();
  for (const spell_id of sorted) {
    const tr = document.createElement("tr");
    const [count, uptime] = dataset[spell_id].split(',');

    const td_icon = document.createElement("td");
    const img = document.createElement("img");
    img.src = get_icon_link(AURAS_ICONS[spell_id]);
    img.alt = spell_id;
    td_icon.appendChild(img);
    
    const td_count = document.createElement("td");
    td_count.append(count);

    const td_uptime = document.createElement("td");
    td_uptime.append(parseFloat(uptime).toFixed(1) + "%");

    tr.appendChild(td_icon);
    tr.appendChild(td_count);
    tr.appendChild(td_uptime);
    fragment.appendChild(tr);
  }
  theTooltipBody.append(fragment);

  const bodyRect = document.body.getBoundingClientRect();
  const trRect = td.getBoundingClientRect();
  theTooltip.style.top = trRect.bottom - bodyRect.top + 'px';
  theTooltip.style.right = bodyRect.right - trRect.left + 'px';
  theTooltip.style.removeProperty("display");
}

function add_auras_cells(row, data, key) {
  const cells = [];
  const all_count = [];
  for (let i=0; i<AURAS_COLUMNS.length; i++) {
    const td = document.createElement('td');
    td.className = `table-${AURAS_COLUMNS[i]}`;
    row.appendChild(td);
    cells.push(td);
    all_count.push(0);
  }
  const data_value = data[key];
  if (data_value instanceof Array) {
    for (const [spell_id, count, uptime, type] of data_value) {
      const td = cells[type];
      td.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
      all_count[type] += count;
    }
  } else {
    for (const spell_id in data_value) {
      const [count, uptime, type] = data_value[spell_id];
      const td = cells[type];
      td.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
      all_count[type] += count;
    }
  }

  for (let i=0; i<all_count.length; i++) {
    const td = cells[i];
    if (all_count[i] == 0) continue;
    td.append(all_count[i]);
    td.addEventListener("mouseleave", () => theTooltip.style.display = "none");
    td.addEventListener("mouseenter", () => show_tooltip(td));
  }
}

function new_row(data) {
  const row = document.createElement('tr');

  add_name_cell(row, data, DATA_KEYS.name);
  add_dps_cell(row, data, DATA_KEYS.uAmount);
  add_total_cell(row, data, DATA_KEYS.uAmount);
  add_dps_cell(row, data, DATA_KEYS.tAmount);
  add_total_cell(row, data, DATA_KEYS.tAmount);
  add_duration_cell(row, data, DATA_KEYS.duration);
  add_auras_cells(row, data, DATA_KEYS.auras);
  add_date_cell(row, data, DATA_KEYS.reportID);

  return row;
}


const new_class_filter = class_i => x => class_i <= x[DATA_KEYS.spec] && x[DATA_KEYS.spec] < class_i+4;
const new_spec_filter = spec_i => x => x[DATA_KEYS.spec] == spec_i;

function filter_data_by_class(data) {
  const class_i = Number(selectClass.value);
  if (class_i === -1) return data;
  const spec_i = Number(selectSpec.value);
  const _filter = spec_i === -1 ? new_class_filter(class_i*4) : new_spec_filter(class_i*4 + spec_i);
  return data.filter(_filter);
}

function no_dublicates(data) {
  const _data = {};
  for (const entry of data) {
    const guid = entry.i;
    if (_data[guid]) continue;
    _data[guid] = entry;
  }
  return Object.values(_data);
}

function update_progress(done, total) {
  const percent = Math.round(done / total * 100);
  progressBarPercentage.textContent = `${done} / ${total} (${percent}%)`;
  progressBar.style.width = `${percent}%`;
}

let mainTimeout;
function table_add_new_data(data) {
  clearTimeout(mainTimeout);
  console.time("clear table");
  mainTableBody.innerHTML = "";
  console.timeEnd("clear table");
  if (!data) return;
  
  data = filter_data_by_class(data);
  if (!data) return;
  
  const sort_func = SORT_FUNC[SORT_VARS.column.id] ?? SORT_FUNC[headUsefulDps.id];
  console.time("sortNewData");
  data = data.sort(sort_func);
  if (SORT_VARS.reversed) data = data.reverse();
  console.timeEnd("sortNewData");

  if (checkboxCombine.checked) data = no_dublicates(data);

  loadingInfo.textContent = "Building table...";
  loadingInfoPanel.style.removeProperty("display");
  const LIMIT = toggleLimit.checked ? Math.min(LIMITED_ROWS, data.length) : data.length;
  const fragment = new DocumentFragment();
  let i = 0;

  console.time("tableAddRows");
  (function chunk() {
    const end = Math.min(i+100, LIMIT);
    for ( ; i < end; i++) {
      const row = new_row(data[i]);
      fragment.appendChild(row);
    }
    update_progress(i, LIMIT);
    
    if (i < LIMIT) {
      mainTimeout = setTimeout(chunk);
      return;
    }
    
    loadingInfo.textContent = "Rendering table...";
    progressBarPercentage.textContent = "Done!";

    setTimeout(() => {
      console.time("table_add_new_data Rendering");
      mainTableBody.append(fragment);
      toggle_useful_columns();
      toggle_total_columns();
      setTimeout(() => {
        loadingInfoPanel.style.display = "none";
        tableContainer.style.removeProperty("display");
        console.timeEnd("table_add_new_data Rendering");
        console.timeEnd("tableAddRows");
      });
    })
  })();
}
function table_add_new_data_wrap(data) {
  tableContainer.style.display = "none";
  setTimeout(() => table_add_new_data(data));
}

xrequest.onprogress = e => {
  let contentLength;
  if (e.lengthComputable) {
    contentLength = e.total;
  } else {
    contentLength = parseInt(e.target.getResponseHeader('X-Full-Content-length'));
  }
  update_progress(e.loaded, contentLength);
};

xrequest.onreadystatechange = () => {
  if (xrequest.status != 200 || xrequest.readyState != 4) return;

  console.timeEnd("query");
  const parsed_json = xrequest.response ? JSON.parse(xrequest.response) : [];
  CACHE.set_new_data(parsed_json);
  table_add_new_data_wrap(parsed_json);
}

function query_server(query) {
  loadingInfo.textContent = "Downloading top:";
  tableContainer.style.display = "none";
  loadingInfoPanel.style.removeProperty("display");
  console.time("query");
  xrequest.open("POST", TOP_POST);
  xrequest.setRequestHeader("Content-Type", "application/json");
  xrequest.send(query);
}

function fetch_data() {
  const query = make_query();
  CACHE.lastQuery = query;
  const data = CACHE[query];
  data ? table_add_new_data_wrap(data) : query_server(query);
}

function search_changed() {
  const __diff = is_heroic() ? 'H' : "N";
  const title = `UwU Logs - Top - ${selectBoss.value} - ${selectSize.value}${__diff}`;
  document.title = title;

  const parsed = {
    server: selectServer.value,
    raid: selectInstance.value,
    boss: selectBoss.value,
    size: selectSize.value,
    mode: is_heroic() ? 1 : 0,
    best: checkboxCombine.checked ? 1 : 0,
    cls: selectClass.value,
    spec: selectSpec.value,
  };

  const new_params = new URLSearchParams(parsed).toString();
  const url = `?${new_params}`;
  history.pushState(parsed, title, url);

  fetch_data();
}

function is_valid_param(elm, par) {
  return [...elm.options].map(o => o.value).includes(par);
}

function find_value_index(select, option_name) {
  for (let i=0; i < select.childElementCount; i++) {
    if (select[i].textContent == option_name) return i;
  }
}
function get_default_index(select) {
  if (select == selectClass) {
    return find_value_index(select, "Priest");
  } else if (select == selectServer) {
    return find_value_index(select, "Lordaeron");
  }
  return 0;
}


const get_cell_value = (tr, idx) => tr.children[idx].value;
const table_sort = idx => (a, b) => (get_cell_value(b, idx) - get_cell_value(a, idx));
const table_sort_reversed = idx => (a, b) => (get_cell_value(a, idx) - get_cell_value(b, idx));
function sort_table_by_column(event) {
  const th = event ? event.target : headDPS;
  const same_column = th == SORT_VARS.column;
  const sort_order = same_column ? !SORT_VARS.reversed : REVERSE_SORTED.has(th.id);
  SORT_VARS.column = th;
  SORT_VARS.reversed = sort_order;
  if (toggleLimit.checked || checkboxCombine.checked) {
    const data = CACHE.get_current();
    table_add_new_data_wrap(data);
    return;
  }
  const sort_func = sort_order ? table_sort_reversed : table_sort;
  
  table_modify_wrap(() => {
    const fragment = new DocumentFragment();
    console.time("sort_table_by_column");
    Array.from(mainTableBody.querySelectorAll('tr'))
        .sort(sort_func(th.cellIndex))
        .forEach(tr => fragment.appendChild(tr));
    mainTableBody.append(fragment);
    console.timeEnd("sort_table_by_column");
  });
}


function new_option(value, index) {
  const _option = document.createElement('option');
  _option.value = index === undefined ? value : index;
  _option.innerHTML = value;
  return _option;
}

function add_bosses() {
  selectBoss.innerHTML = "";
  BOSSES[selectInstance.value].forEach(boss_name => selectBoss.appendChild(new_option(boss_name)));
};

function add_specs() {
  selectSpec.innerHTML = "";
  const class_index = CLASSES[selectClass.value];
  const specs = SPECS_SELECT_OPTIONS[class_index];
  selectSpec.appendChild(new_option('All specs', -1));
  if (!specs) return;

  specs.forEach((spec_name, i) => selectSpec.appendChild(new_option(spec_name, i+1)));
};

function init() {
  Object.keys(BOSSES).forEach(name => selectInstance.appendChild(new_option(name)));
  CLASSES.forEach((name, i) => selectClass.appendChild(new_option(name, i)));

  const currentParams = new URLSearchParams(window.location.search);
  for (let key in INTERACTABLES) {
    const par = currentParams.get(key);
    const elm = INTERACTABLES[key];
    if (elm.nodeName == "INPUT") {
      elm.checked = par != 0;
    } else if (is_valid_param(elm, par)) {
      elm.value = par;
    } else {
      elm.selectedIndex = get_default_index(elm);
    }

    if (elm == selectInstance) {
      elm.addEventListener('change', add_bosses);
      add_bosses();
    } else if (elm == selectClass) {
      elm.addEventListener('change', add_specs);
      add_specs();
    }
    elm.addEventListener('change', search_changed);
  }

  if (screenX.matches) {
    document.getElementById("head-external").textContent = "Ext";
    document.getElementById("head-self").textContent = "Slf";
    document.getElementById("head-rekt").textContent = "Rkt";
  }
  
  toggleTotalDamage.checked = localStorage.getItem("showtotal") == "false" ? false : screenX.matches;
  toggleUsefulDamage.checked = localStorage.getItem("showuseful") == "false" ? false : true;
  toggleLimit.checked = localStorage.getItem("showlimit") == "false" ? false : true;
  
  toggleTotalDamage.addEventListener('change', () => {
    localStorage.setItem("showtotal", toggleTotalDamage.checked);
    toggle_total_columns();
  });
  toggleUsefulDamage.addEventListener('change', () => {
    localStorage.setItem("showuseful", toggleUsefulDamage.checked);
    toggle_useful_columns();
  });
  toggleLimit.addEventListener('change', () => {
    localStorage.setItem("showlimit", toggleLimit.checked);
    const data = CACHE.get_current();
    table_add_new_data_wrap(data);
  });

  search_changed();
  document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', sort_table_by_column));
}

document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);
