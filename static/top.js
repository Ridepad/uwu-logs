import {
  BOSSES,
  CLASSES,
  SPECS,
  SPECS_SELECT_OPTIONS,
  AURAS_COLUMNS,
  AURAS_ICONS,
  MONTHS,
} from "./constants.js"

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

const tableTop = document.getElementById("table-top");
const tablePoints = document.getElementById("table-points");
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

const IRRELEVANT_FOR_POINTS = [
  selectSize,
  checkboxDifficulty,
  checkboxCombine,
  toggleTotalDamage,
  toggleUsefulDamage,
  toggleLimit,
];

const ROW_LIMIT = 1000;
const screenX = window.matchMedia("(orientation: landscape)");
const TOP_POST = window.location.pathname;
const xrequest = new XMLHttpRequest();
const HAS_HEROIC = new Set([
  ...BOSSES["Icecrown Citadel"],
  ...BOSSES["Trial of the Crusader"],
  "Halion",
  "Points",
]);
const DEFAULT_SPEC = [3, 1, 2, 2, 3, 3, 2, 1, 2, 2];
const SORT_VARS = {
  column: headUsefulDps,
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
function is_points() {
  return selectInstance.value == "Points";
}

function make_query() {
  const size = selectSize.value;
  const diff = is_heroic() ? 'H' : 'N';
  const mode = `${size}${diff}`;
  const q = {
    server: selectServer.value,
    boss: selectBoss.value,
    mode: mode,
    best_only: checkboxCombine.checked,
    class_i: selectClass.value,
    spec_i: selectSpec.value,
    sort_by: SORT_VARS.column.id,
    limit: toggleLimit.checked ? 1 : 0,
  };
  console.log(q);
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
  a.href = `/character?name=${name}&server=${selectServer.value}&spec=${spec%4}`;
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
  const date_text = screenX.matches ? `${day} ${months_str} ${year} ${hour}:${minute}` : `${day}-${month}-${year}`;

  const a = document.createElement('a');
  a.href = `/reports/${report_ID}--${selectServer.value}`;
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
  const sorted = Object.keys(dataset).sort();
  const rows = Array.from(theTooltipBody.children);
  for (const i in sorted) {
    const tr = rows[i];
    const spell_id = sorted[i];
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
      if (i < sorted.length) {
        tr.classList.remove("hidden");
      } else {
        tr.classList.add("hidden");
      }
    }
  }, toggleLimit.checked ? 10 : 150);
}
function mouseenter(event) {
  clearTimeout(timeout_hide);
  const td = event.target;
  show_tooltip(td);
  const bodyRect = document.body.getBoundingClientRect();
  const trRect = td.getBoundingClientRect();
  theTooltip.style.top = `${trRect.bottom}px`;
  theTooltip.style.right = `${bodyRect.right - trRect.left}px`;
  theTooltip.style.removeProperty("display");
}
function mouseleave() {
  clearTimeout(timeout_hide);
  timeout_hide = setTimeout(() => {
    theTooltip.style.display = "none"
  }, 300);
}

function cell_auras(auras) {
  const cells = [];
  const all_count = [];
  for (let i = 0; i < AURAS_COLUMNS.length; i++) {
    const td = document.createElement('td');
    td.className = `table-${AURAS_COLUMNS[i]}`;
    cells.push(td);
    all_count.push(0);
  }
  if (auras instanceof Array) {
    for (const [spell_id, count, uptime, type] of auras) {
      const td = cells[type];
      td.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
      all_count[type] += count;
    }
  } else {
    for (const spell_id in auras) {
      const [count, uptime, type] = auras[spell_id];
      const td = cells[type];
      td.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
      all_count[type] += count;
    }
  }

  for (let i = 0; i < all_count.length; i++) {
    const td = cells[i];
    if (all_count[i] == 0) continue;
    td.append(all_count[i]);
    td.addEventListener("mouseleave", mouseleave);
    td.addEventListener("mouseenter", mouseenter);
  }
  return cells;
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
    let class_color;
    if (v > 99.99) {
        class_color = "top1";
    } else if (v >= 99) {
        class_color = "top99";
    } else if (v >= 95) {
        class_color = "top95";
    } else if (v >= 75) {
        class_color = "top75";
    } else if (v >= 50) {
        class_color = "top50";
    } else if (v >= 25) {
        class_color = "top25";
    } else {
        class_color = "topkek";
    }
    return class_color;
}
function cell_points(v, is_total) {
  const cell = document.createElement('td');
  cell.classList.add("table-points");
  if (!is_total) {
    v = (v / 100).toFixed(2);
    cell.classList.add((points_rank_class(v)));
  }
  cell.append(v);
  return cell;  
}
function new_row_points(data, spec) {
  const row = document.createElement('tr');
  console.log(data);
  const [
    p_relative,
    p_total,
    name,
  ] = data;

  [
    cell_name(name, spec),
    cell_points(p_relative),
    cell_points(Math.floor(p_total), true),
  ].forEach(td => row.appendChild(td));

  return row;
}


function update_progress(done, total) {
  const percent = Math.round(done / total * 100);
  progressBarPercentage.textContent = `${done} / ${total} (${percent}%)`;
  progressBar.style.width = `${percent}%`;
}

let mainTimeout;
function table_add_new_data(table, data) {
  clearTimeout(mainTimeout);
  console.time("clear table");
  table.innerHTML = "";
  console.timeEnd("clear table");
  if (!data) return;

  loadingInfo.textContent = "Building table...";
  loadingInfoPanel.style.removeProperty("display");
  const LIMIT = toggleLimit.checked ? Math.min(ROW_LIMIT, data.length) : data.length;
  const fragment = new DocumentFragment();
  let i = 0;

  const spec = parseInt(selectClass.value)*4+parseInt(selectSpec.value);
  const points = i => new_row_points(data[i], spec);
  const top = i => new_row(data[i]);
  const _new_row = is_points() ? points : top;

  console.time("tableAddRows");
  (function chunk() {
    const end = Math.min(i + 100, LIMIT);
    for (; i < end; i++) {
      const row = _new_row(i);
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
      table.append(fragment);
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
  let t1, t2;
  if (is_points()) {
    t1 = tablePoints;
    t2 = tableTop;
  } else {
    t2 = tablePoints;
    t1 = tableTop;
  }
  t2.style.display = "none";
  t1.style.removeProperty("display");
  const body = t1.querySelector("tbody");
  setTimeout(() => table_add_new_data(body, data));
}

xrequest.onprogress = e => {
  let contentLength;
  if (e.lengthComputable) {
    contentLength = e.total;
  } else {
    contentLength = parseInt(e.target.getResponseHeader('Content-Length-Full'));
  }
  update_progress(e.loaded, contentLength);
};

xrequest.onreadystatechange = () => {
  if (xrequest.status != 200 || xrequest.readyState != 4) return;
  const parsed_json = JSON.parse(xrequest.response);
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
  for (let i = 0; i < select.childElementCount; i++) {
    if (select[i].textContent == option_name) return i;
  }
}

function get_default_index(select) {
  if (select == selectServer) {
    return find_value_index(select, "Lordaeron");
  } else if (select == selectClass) {
    return find_value_index(select, "Priest");
  } else if (select == selectSpec) {
    return find_value_index(select, "Shadow");
  }
  return 0;
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
  selectBoss.innerHTML = "";
  BOSSES[selectInstance.value].forEach(boss_name => selectBoss.appendChild(new_option(boss_name)));
  
  const points_selected = is_points();
  IRRELEVANT_FOR_POINTS.forEach(e => e.disabled = points_selected);
  
  on_change_class();
};

function add_specs() {
  selectSpec.innerHTML = "";
  const class_index = CLASSES[selectClass.value];
  const specs = SPECS_SELECT_OPTIONS[class_index];
  selectSpec.appendChild(new_option('All specs', -1));
  if (!specs) return;

  specs.forEach((spec_name, i) => selectSpec.appendChild(new_option(spec_name, i + 1)));
};
function on_change_class(_new) {
  if (is_points() && selectClass.value == -1) {
    selectClass.selectedIndex = 1;
    _new = true;
  }
  
  if (_new != undefined) add_specs();

  on_change_spec();
}

function on_change_spec() {
  if (is_points() && selectSpec.value == -1) {
    selectSpec.selectedIndex = DEFAULT_SPEC[selectClass.value];
  }
}
function add_on_change_events(elm) {
  if (elm == selectInstance) {
    on_change_instance();
    elm.addEventListener('change', on_change_instance);
  } else if (elm == selectClass) {
    on_change_class(true);
    elm.addEventListener('change', on_change_class);
  } else if (elm == selectSpec) {
    elm.addEventListener('change', on_change_spec);
  }
  elm.addEventListener('change', search_changed);
}

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
    add_on_change_events(elm);
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
    fetch_data();
  });

  search_changed();
  document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', fetch_column));
}

document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);