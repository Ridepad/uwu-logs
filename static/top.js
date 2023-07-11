import { BOSSES, CLASSES,SPECS, SPECS_SELECT_OPTIONS, AURAS_COLUMNS, DATA_KEYS, AURAS_ICONS, MONTHS } from "./appConstants.js"

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
const headUsefulAmount = document.getElementById('head-useful-amount');
const headTotalDps = document.getElementById('head-total-dps');
const headTotalAmount = document.getElementById('head-total-amount');
const toggleTotalDamage = document.getElementById('toggle-total-damage');
const toggleUsefulDamage = document.getElementById('toggle-useful-damage');
const toggleLimit = document.getElementById('toggle-limit');
const LIMITED_ROWS = 1000;
const screenX = window.matchMedia("(orientation: landscape)");
const HAS_HEROIC = [
  "Icecrown Citadel",
  "The Ruby Sanctum",
  "Trial of the Crusader",
];

const SORT_VARS = {column: headUsefulDps, order: 1};
const DATA_KEYS2 = {
  "head-useful-amount": 'ua',
  "head-useful-dps": 'ud',
  "head-total-amount": 'ta',
  "head-total-dps": 'td',
  "head-duration": 't',
};
const CACHE = {
  lastQuery: "",
  setNewData(data) {
    const query = makeQuery();
    if (query == this.lastQuery) {
      this[query] = data;
    }
  },
  getCurrent() {
    const query = makeQuery();
    return this[query];
  }
};

function toggleColumn(className, display) {
  mainTableBody.querySelectorAll(className).forEach(e => e.style.display = display);
}

function toggleUsefulColumns(event) {
  if (!event && toggleUsefulDamage.checked) return;

  const display = toggleUsefulDamage.checked ? "" : 'none';
  headUsefulDps.style.display = display;
  headUsefulAmount.style.display = display;
  toggleColumn(".table-ud", display);
  toggleColumn(".table-ua", display);
}
function toggleTotalColumns(event) {
  if (!event && toggleTotalDamage.checked) return;

  const display = toggleTotalDamage.checked ? "" : 'none';
  headTotalDps.style.display = display;
  headTotalAmount.style.display = display;
  toggleColumn(".table-td", display);
  toggleColumn(".table-ta", display);
}

function newOption(value, index) {
  const _option = document.createElement('option');
  _option.value = index === undefined ? value : index;
  _option.innerHTML = value;
  return _option;
}

function addBosses() {
  selectBoss.innerHTML = "";
  BOSSES[selectInstance.value].forEach(boss_name => selectBoss.appendChild(newOption(boss_name)));
  const has_heroic = HAS_HEROIC.includes(selectInstance.value);
};

function addSpecs() {
  selectSpec.innerHTML = "";
  const class_index = CLASSES[selectClass.value];
  const specs = SPECS_SELECT_OPTIONS[class_index];
  selectSpec.appendChild(newOption('All specs', -1));
  if (!specs) return;

  specs.forEach((spec_name, i) => selectSpec.appendChild(newOption(spec_name, i+1)));
};

function numberWithSeparator(x, sep=" ") {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}
function add_inner_text(cell, text) {
  if (!isNaN(text)) text = numberWithSeparator(text);
  cell.append(text);
}

function addNameCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];

  const [spec_name, spec_icon, spec_class_id] = SPECS[data[DATA_KEYS.spec]];
  const img = document.createElement("img");
  img.src = `/static/icons/${spec_icon}.jpg`;
  cell.appendChild(img);
  cell.append(data_value);
  cell.title = spec_name;
  cell.className = `${spec_class_id} table-n`;
  row.appendChild(cell);
}

function addDPSCell(row, data, key) {
  const cell = document.createElement('td');
  const data_damage = data[key];
  const data_value = data_damage / data.t;
  cell.value = data_value;
  key = key[0];
  cell.className = `table-${key}d`;
  const _input = key == "u" ? toggleUsefulDamage : toggleTotalDamage;
  if (!_input.checked) {
    cell.style.display = "none";
  }
  const _inside_data = data_value.toFixed(1);
  add_inner_text(cell, _inside_data);
  row.appendChild(cell);
}

function addTotalCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];
  cell.value = data_value;
  cell.className = `table-${key}`;
  const _input = key == "ta" ? toggleTotalDamage : toggleUsefulDamage;
  if (!_input.checked) {
    cell.style.display = "none";
  }
  add_inner_text(cell, data_value);
  row.appendChild(cell);
}

function formatDuration(dur) {
  const minutes = Math.floor(dur/60);
  const seconds = Math.floor(dur%60);
  const m_str = minutes.toString().padStart(2, '0');
  const s_str = seconds.toString().padStart(2, '0');
  return `${m_str}:${s_str}`;
}
function addDurationCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];
  cell.value = data_value;
  cell.className = `table-${key}`;
  cell.append(formatDuration(data_value));
  row.appendChild(cell);
}

function addDateCell(row, data, key) {
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

const theTooltip = document.getElementById("the-tooltip");
const theTooltipBody = theTooltip.querySelector("tbody");
function show_tooltip(td) {
  while(theTooltipBody.firstChild) theTooltipBody.removeChild(theTooltipBody.firstChild);
  
  const dataset = td.dataset;
  const fragment = new DocumentFragment();
  for (let spell_id in dataset) {
    const tr = document.createElement("tr");
    const [count, uptime] = dataset[spell_id].split(',');

    const td_icon = document.createElement("td");
    const img = document.createElement("img");
    img.src = `/static/icons/${AURAS_ICONS[spell_id]}.jpg`;
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
  theTooltip.style.display = "";
}

function addAurasCells(row, data, key) {
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
  for (let spell_id in data_value) {
    const [count, uptime, type] = data_value[spell_id];
    const td = cells[type];
    td.setAttribute(`data-${spell_id}`, `${count},${uptime}`);
    all_count[type] += count;
  }
  for (let i=0; i<all_count.length; i++) {
    const td = cells[i];
    td.append(all_count[i]);
    if (all_count[i] == 0) continue;
    td.addEventListener("mouseleave", () => theTooltip.style.display = "none");
    td.addEventListener("mouseenter", () => show_tooltip(td));
  }
}

function newRow(data) {
  const row = document.createElement('tr');

  addNameCell(row, data, DATA_KEYS.name);
  addDPSCell(row, data, DATA_KEYS.uAmount);
  addTotalCell(row, data, DATA_KEYS.uAmount);
  addDPSCell(row, data, DATA_KEYS.tAmount);
  addTotalCell(row, data, DATA_KEYS.tAmount);
  addDurationCell(row, data, DATA_KEYS.duration);
  addAurasCells(row, data, DATA_KEYS.auras);
  addDateCell(row, data, DATA_KEYS.reportID);

  return row
}

const newClassFilter = class_i => x => class_i <= x[DATA_KEYS.spec] && x[DATA_KEYS.spec] < class_i+4;
const newSpecFilter = spec_i => x => x[DATA_KEYS.spec] == spec_i;

function filterDataByClass(data) {
  const class_i = Number(selectClass.value);
  if (class_i === -1) return data;
  const spec_i = Number(selectSpec.value);
  const _filter = spec_i === -1 ? newClassFilter(class_i*4) : newSpecFilter(class_i*4 + spec_i);
  return data.filter(_filter);
}

const getbest = () => SORT_VARS.order == 1 ? (a, b) => a > b : (a, b) => a < b;
function noDublicates(data) {
  const getbest_f = getbest();
  const key = DATA_KEYS2[SORT_VARS.column.id];
  const best_data = {};
  for (let i=0; i < data.length; i++) {
    const current = data[i];
    const guid = current[DATA_KEYS.guid];
    const best = best_data[guid];
    if (!best || getbest_f(current[key], best[key])) {
      best_data[guid] = current;
    }
  }
  return Object.values(best_data);
}

function update_progress(done, total) {
  const percent = Math.round(done / total * 100);
  progressBarPercentage.textContent = `${done} / ${total} (${percent}%)`;
  progressBar.style.width = `${percent}%`;
}

let mainTimeout;
const sortNewData = key => (a, b) => (b[key] - a[key]) * SORT_VARS.order;
function tableAddNewData(data) {
  clearTimeout(mainTimeout);
  console.time("clear table");
  mainTableBody.innerHTML = "";
  console.timeEnd("clear table");
  if (!data) return;
  
  data = filterDataByClass(data);
  if (!data) return;
  
  const key = DATA_KEYS2[SORT_VARS.column.id];
  data = data.sort(sortNewData(key));
  data = checkboxCombine.checked ? noDublicates(data) : data;
  if (!data) return;

  console.time("tableAddRows");
  loadingInfo.textContent = "Building table...";
  loadingInfoPanel.style.display = "";
  const LIMIT = toggleLimit.checked ? Math.min(LIMITED_ROWS, data.length) : data.length;
  const fragment = new DocumentFragment();
  let i = 0;

  (function chunk() {
    const end = Math.min(i+100, LIMIT);
    for ( ; i < end; i++) {
      const row = newRow(data[i]);
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
      console.time("tableAddNewData Rendering");
      mainTableBody.append(fragment);
      toggleUsefulColumns();
      toggleTotalColumns();
      setTimeout(() => {
        loadingInfoPanel.style.display = "none";
        tableContainer.style.display = "";
        console.timeEnd("tableAddRows");
        console.timeEnd("tableAddNewData Rendering");
      });
    })
  })();
}

function tableAddNewDataWrap(data) {
  tableContainer.style.display = "none";
  setTimeout(() => tableAddNewData(data));
}

function is_heroic() {
  return HAS_HEROIC.includes(selectInstance.value) && checkboxDifficulty.checked;
}

function makeQuery() {
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

const TOP_POST = window.location.pathname;
const xrequest = new XMLHttpRequest();

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

  CACHE.setNewData(parsed_json);

  tableAddNewDataWrap(parsed_json);
}

function queryServer(query) {
  loadingInfo.textContent = "Downloading top:";
  tableContainer.style.display = "none";
  loadingInfoPanel.style.display = "";
  console.time("query");
  xrequest.open("POST", TOP_POST);
  xrequest.setRequestHeader("Content-Type", "application/json");
  xrequest.send(query);
}

function fetchData() {
  const query = makeQuery();
  CACHE.lastQuery = query;
  const data = CACHE[query];
  data ? tableAddNewDataWrap(data) : queryServer(query);
}

function searchChanged() {
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

  fetchData();
}

function isValidParam(elm, par) {
  return [...elm.options].map(o => o.value).includes(par);
}

function findValueIndex(select, option_name) {
  for (let i=0; i < select.childElementCount; i++) {
    if (select[i].textContent == option_name) return i;
  }
}
function getDefaultIndex(select) {
  if (select == selectClass) {
    return findValueIndex(select, "Priest");
  } else if (select == selectServer) {
    return findValueIndex(select, "Lordaeron");
  }
  return 0;
}

const REVERSE_SORTED = ["head-duration", "head-external", "head-rekt"];
const getCellValue = (tr, idx) => tr.children[idx].value;
const tableSort = idx => (a, b) => (getCellValue(b, idx) - getCellValue(a, idx)) * SORT_VARS.order;
function sort_table_by_column(event) {
  const th = event ? event.target : headDPS;
  SORT_VARS.order = th == SORT_VARS.column ? -SORT_VARS.order : REVERSE_SORTED.includes(th.id) ? -1 : 1;
  SORT_VARS.column = th;
  if (DATA_KEYS2[th.id] && (toggleLimit.checked || checkboxCombine.checked)) {
    const data = CACHE.getCurrent();
    tableAddNewDataWrap(data);
    return;
  }

  Array.from(mainTableBody.querySelectorAll('tr'))
       .sort(tableSort(th.cellIndex))
       .forEach(tr => mainTableBody.appendChild(tr));
}


function init() {
  Object.keys(BOSSES).forEach(name => selectInstance.appendChild(newOption(name)));
  CLASSES.forEach((name, i) => selectClass.appendChild(newOption(name, i)));

  const currentParams = new URLSearchParams(window.location.search);
  for (let key in INTERACTABLES) {
    const par = currentParams.get(key);
    const elm = INTERACTABLES[key];
    if (elm.nodeName == "INPUT") {
      elm.checked = par != 0;
    } else if (isValidParam(elm, par)) {
      elm.value = par;
    } else {
      elm.selectedIndex = getDefaultIndex(elm);
    }

    if (elm == selectInstance) {
      elm.addEventListener('change', addBosses);
      addBosses();
    } else if (elm == selectClass) {
      elm.addEventListener('change', addSpecs);
      addSpecs();
    }
    elm.addEventListener('change', searchChanged);
  }

  if (screenX.matches) {
    document.getElementById("head-external").textContent = "Ext";
    document.getElementById("head-self").textContent = "Slf";
    document.getElementById("head-rekt").textContent = "Rkt";
  }
  
  toggleTotalDamage.checked = localStorage.getItem("showtotal") == "false" ? false : screenX.matches;
  toggleUsefulDamage.checked = localStorage.getItem("showuseful") == "false" ? false : true;
  toggleLimit.checked = localStorage.getItem("showlimit") == "false" ? false : true;
  
  toggleTotalDamage.addEventListener('change', event => {
    localStorage.setItem("showtotal", toggleTotalDamage.checked);
    toggleTotalColumns(event);
  });
  toggleUsefulDamage.addEventListener('change', event => {
    localStorage.setItem("showuseful", toggleUsefulDamage.checked);
    toggleUsefulColumns(event);
  });
  toggleLimit.addEventListener('change', () => {
    localStorage.setItem("showlimit", toggleLimit.checked);
    const data = CACHE.getCurrent();
    tableAddNewDataWrap(data);
  });

  searchChanged();
  document.querySelectorAll('th').forEach(th => th.addEventListener('click', sort_table_by_column));
}

document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);
// window.addEventListener('DOMContentLoaded', init);
