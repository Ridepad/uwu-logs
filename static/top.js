import {
  BOSSES, CLASSES,SPECS, SPECS_SELECT_OPTIONS, AURAS_COLUMNS, DATA_KEYS,
  AURAS_ICONS, LOGS_URL, ICON_CDN_URL, MONTHS } from "./appConstants.js"

const LOC = window.location;
const screenX = window.matchMedia("(min-width: 1100px)");

const mainTableBody = document.getElementById("main-table-body");
const headDPS = document.getElementById('head-dps');

const serverSelect = document.getElementById('server-select');
const instanceSelect = document.getElementById('instance-select');
const bossSelect = document.getElementById('boss-select');
const sizeSelect = document.getElementById('size-select');
const difficultyCheckbox = document.getElementById('difficulty-checkbox');
const combineCheckbox = document.getElementById('combine-checkbox');
const classSelect = document.getElementById('class-select');
const specSelect = document.getElementById('spec-select');

const INTERACTABLES = {
  server: serverSelect,
  raid: instanceSelect,
  boss: bossSelect,
  size: sizeSelect,
  mode: difficultyCheckbox,
  best: combineCheckbox,
  cls: classSelect,
  spec: specSelect,
}

const loading = document.getElementById('loading-info');
const toggleTotalDamage = document.getElementById('toggle-total-damage');
const toggleUsefulDamage = document.getElementById('toggle-useful-damage');
const headUsefulDps = document.getElementById('head-useful-dps');
const headUsefulAmount = document.getElementById('head-useful-amount');
const headTotalDps = document.getElementById('head-total-dps');
const headTotalAmount = document.getElementById('head-total-amount');
const toggleLimit = document.getElementById('toggle-limit');
const LIMITED_ROWS = 1000;

function toggleColumn(className, display) {
  document.querySelectorAll(className).forEach(e => e.style.display = display);
}

function toggleUsefulColumns(first) {
  if (first && toggleUsefulDamage.checked) return;

  const display = toggleUsefulDamage.checked ? "table-cell" : 'none';
  headTotalDps.style.display = display;
  headTotalAmount.style.display = display;
  toggleColumn(".table-ud", display);
  toggleColumn(".table-ua", display);
}
function toggleTotalColumns(first) {
  if (first && toggleTotalDamage.checked) return;

  const display = toggleTotalDamage.checked ? "table-cell" : 'none';
  headUsefulDps.style.display = display;
  headUsefulAmount.style.display = display;
  toggleColumn(".table-td", display);
  toggleColumn(".table-ta", display);
}

function toggleColumns(event) {
  event.target == toggleTotalDamage ? toggleTotalColumns() : toggleUsefulColumns();
}

function newOption(value, index) {
  const _option = document.createElement('option');
  _option.value = index === undefined ? value : index;
  _option.innerHTML = value;
  return _option
}

function addBosses() {
  bossSelect.innerHTML = "";
  BOSSES[instanceSelect.value].forEach(boss_name => bossSelect.appendChild(newOption(boss_name)));
};

function addSpecs() {
  specSelect.innerHTML = "";
  const class_index = CLASSES[classSelect.value];
  const specs = SPECS_SELECT_OPTIONS[class_index];
  specSelect.appendChild(newOption('All specs', -1));
  if (!specs) return;

  specs.forEach((spec_name, i) => specSelect.appendChild(newOption(spec_name, i+1)));
};

function newLink(report_ID) {
  const _a = document.createElement('a');
  _a.href = `${LOGS_URL}/reports/${report_ID}/`;
  _a.target = "_blank";
  return _a
}

function numberWithSeparator(x, sep=" ") {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}
function add_inner_text(cell, text) {
  if (!isNaN(text)) text = numberWithSeparator(text);
  
  const innerText = document.createTextNode(text);
  cell.appendChild(innerText);
}

function addNameCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];

  const [spec_name, spec_icon, spec_class_id] = SPECS[data[DATA_KEYS.spec]];
  const imgsrc = `${ICON_CDN_URL}/${spec_icon}.jpg`;
  cell.innerHTML = `<img src="${imgsrc}">${data_value}`;
  cell.title = spec_name;
  cell.className = `${spec_class_id} table-n`;
  row.appendChild(cell);
}

function addDPSCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];
  cell.value = data_value;
  cell.className = `table-${key}`;
  const _inside_data = data_value.toFixed(1);
  add_inner_text(cell, _inside_data);
  row.appendChild(cell);
}

function addTotalCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];
  cell.value = data_value;
  cell.className = `table-${key}`;
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
  const _inside_data = formatDuration(data_value);
  add_inner_text(cell, _inside_data);
  row.appendChild(cell);
}

function addDateCell(row, data, key) {
  const cell = document.createElement('td');
  const data_value = data[key];

  const report_date = data_value.toString().slice(0, 15);
  cell.value = report_date.replaceAll('-', '');
  
  const _link = newLink(data_value);
  const [year, month, day, _, hour, minute] = report_date.split('-');
  const months_str = MONTHS[Number(month) - 1];
  const date = `${day} ${months_str} ${year}`;
  _link.innerText = screenX.matches ? `${date} ${hour}:${minute}` : date;
  cell.appendChild(_link);
  
  cell.className = `table-${key}`;
  row.appendChild(cell);
}

function new_li(spell_id, count, uptime) {
  const li = document.createElement('li');
  const imgsrc = `${ICON_CDN_URL}/${AURAS_ICONS[spell_id]}.jpg`;
  li.innerHTML = `<img src="${imgsrc}" alt="${spell_id}"><span>${count}</span><span>${uptime}%</span>`;
  return li
}

function addAurasCells(row, data, key) {
  const data_value = data[key];

  const AURAS_COUNT = [];
  const AURAS_TABLE = [];
  const AURAS_CELLS = [];
  for (let i=0; i<AURAS_COLUMNS.length; i++) {
    AURAS_COUNT.push(0);
    const td = document.createElement('td');
    AURAS_CELLS.push(td);
    const fragment = new DocumentFragment();
    AURAS_TABLE.push(fragment);
  }

  for (let spell_id in data_value) {
    const [count, uptime, type] = data_value[spell_id];
    const li = new_li(spell_id, count, uptime);
    AURAS_COUNT[type] += count;
    AURAS_TABLE[type].append(li);
  }
  
  for (let i=0; i<AURAS_COLUMNS.length; i++) {
    const cell = AURAS_CELLS[i];
    cell.value = AURAS_COUNT[i];

    if (AURAS_COUNT[i] > 0) {
      const table = document.createElement('ul');
      table.append(AURAS_TABLE[i])
      cell.appendChild(table);
    }
    
    add_inner_text(cell, AURAS_COUNT[i]);
    cell.classList.add(`table-${AURAS_COLUMNS[i]}`);
    row.appendChild(cell);
  }
}

function newRow(data) {
  const row = document.createElement('tr');

  addNameCell(row, data, DATA_KEYS.name);
  addDPSCell(row, data, DATA_KEYS.uDPS);
  addTotalCell(row, data, DATA_KEYS.uAmount);
  addDPSCell(row, data, DATA_KEYS.tDPS);
  addTotalCell(row, data, DATA_KEYS.tAmount);
  addDurationCell(row, data, DATA_KEYS.duration);
  addAurasCells(row, data, DATA_KEYS.auras);
  addDateCell(row, data, DATA_KEYS.reportID);

  return row
}

const reverseSorted = ["head-duration", "head-external", "head-self", "head-rekt"]
const SORT_VARS = {column: -1, order: 1}
const getCellValue = (tr, idx) => tr.children[idx].value;
const tableSort = idx => (a, b) => (getCellValue(b, idx) - getCellValue(a, idx)) * SORT_VARS.order;
function sort_table_by_column(event) {
  const th = event ? event.target : headDPS;
  const column_n = th.cellIndex;
  SORT_VARS.order = column_n == SORT_VARS.column ? -SORT_VARS.order : reverseSorted.includes(th.id) ? -1 : 1;
  Array.from(mainTableBody.querySelectorAll('tr:nth-child(n+1)'))
       .sort(tableSort(column_n))
       .forEach(tr => mainTableBody.appendChild(tr));
  SORT_VARS.column = column_n;
}

const newClassFilter = class_i => x => class_i <= x[DATA_KEYS.spec] && x[DATA_KEYS.spec] < class_i+4;
const newSpecFilter = spec_i => x => x[DATA_KEYS.spec] == spec_i;

function filterDataByClass(data) {
  const class_i = Number(classSelect.value);
  if (class_i === -1) return data;
  const spec_i = Number(specSelect.value);
  const _filter = spec_i === -1 ? newClassFilter(class_i*4) : newSpecFilter(class_i*4 + spec_i);
  return data.filter(_filter);
}

function noDublicates(data) {
  let data2 = {}
  for (let i=0; i < data.length; i++) {
    const current = data[i];
    const guid = current[DATA_KEYS.guid];
    const best = data2[guid];
    if (!best || current[DATA_KEYS.uDPS] > best[DATA_KEYS.uDPS]) {
      data2[guid] = current;
    }
  }
  return Object.values(data2);
}


let mainTimeout;
function tableAddNewData(data) {
  mainTableBody.innerHTML = "";
  clearTimeout(mainTimeout);
  if (!data) return;
  data = filterDataByClass(data)
  if (!data) return;
  data = combineCheckbox.checked ? noDublicates(data) : data;
  if (!data) return;

  let i = 0;
  SORT_VARS.column = 1;
  loading.parentElement.style.display = "block";
  const LIMIT = toggleLimit.checked ? Math.min(LIMITED_ROWS, data.length) : data.length;
  (function chunk() {
    const end = Math.min(i+250, LIMIT)
    for ( ; i < end; i++) {
      const row = newRow(data[i]);
      mainTableBody.appendChild(row);
    }
    if (i < LIMIT) {
      loading.innerText = `Done: ${i}/${LIMIT}`
      mainTimeout = setTimeout(chunk);
    } else {
      loading.innerText = '';
      loading.parentElement.style.display = "none";
      toggleUsefulColumns(true);
      toggleTotalColumns(true);
    }
  })();
}

function makeQuery() {
  const sizeValue = sizeSelect.value;
  const diffValue = difficultyCheckbox.checked ? 'H' : 'N';
  const diff_str = `${sizeValue}${diffValue}`;
  const q = {
    server: serverSelect.value,
    boss: bossSelect.value,
    diff: diff_str,
  };
  return JSON.stringify(q);
}

const CACHE = {
  lastQuery: "",
  setNewData: function(data) {
    const query = makeQuery();
    if (query == this.lastQuery) {
      this[query] = data;
    }
  }
};

const sortNewData = (a, b) => b.ud - a.ud;
const TOP_POST = window.location.pathname;
const xrequest = new XMLHttpRequest();
xrequest.onreadystatechange = () => {
  if (xrequest.status != 200 || xrequest.readyState != 4) return;
  console.timeEnd("query");
  const parsed_json = xrequest.response ? JSON.parse(xrequest.response) : [];

  console.time("sort");
  const data = parsed_json.sort(sortNewData);
  console.timeEnd("sort");

  CACHE.setNewData(data);

  console.time("tableAddNewData");
  tableAddNewData(data);
  console.timeEnd("tableAddNewData");
}

function queryServer(query) {
  console.time("query");
  xrequest.open("POST", TOP_POST);
  xrequest.setRequestHeader("Content-Type", "application/json");
  xrequest.send(query);
}

function fetchData() {
  const query = makeQuery();
  CACHE.lastQuery = query;
  const data = CACHE[query];
  data ? tableAddNewData(data) : queryServer(query);
}

function searchChanged() {
  const __diff = difficultyCheckbox.checked ? 'H' : "N";
  const title = `UwU Logs - Top - ${bossSelect.value} - ${sizeSelect.value}${__diff}`;
  document.title = title;

  const parsed = {
    server: serverSelect.value,
    raid: instanceSelect.value,
    boss: bossSelect.value,
    size: sizeSelect.value,
    mode: difficultyCheckbox.checked ? 1 : 0,
    best: combineCheckbox.checked ? 1 : 0,
    cls: classSelect.value,
    spec: specSelect.value,
  };

  const new_params = new URLSearchParams(parsed).toString();
  const url = `?${new_params}`;
  history.pushState(parsed, title, url);

  fetchData();
}

function isValidParam(elm, par) {
  return [...elm.options].map(o => o.value).includes(par);
}

function init() {
  Object.keys(BOSSES).forEach(name => instanceSelect.appendChild(newOption(name)));
  CLASSES.forEach((name, i) => classSelect.appendChild(newOption(name, i)));
  
  const currentParams = new URLSearchParams(LOC.search);
  for (let key in INTERACTABLES) {
    const par = currentParams.get(key);
    const elm = INTERACTABLES[key];
    if (elm.nodeName == "INPUT") {
      elm.checked = par != 0;
    } else if (!isValidParam(elm, par)) {
      elm.selectedIndex = elm == classSelect ? 6 : 0;
    } else if (par) {
      elm.value = par;
    }

    if (elm == instanceSelect) {
      elm.addEventListener('change', addBosses);
      addBosses();
    } else if (elm == classSelect) {
      elm.addEventListener('change', addSpecs);
      addSpecs();
    }
    elm.addEventListener('change', searchChanged);
  }
  
  toggleTotalDamage.addEventListener('change', toggleColumns);
  toggleUsefulDamage.addEventListener('change', toggleColumns);
  
  searchChanged();
  document.querySelectorAll('th.sortable').forEach(th => th.addEventListener('click', sort_table_by_column));
}

document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);
