const SELECT_CLASS = document.getElementById("select-class");
const SELECT_SPELL = document.getElementById("select-spell");
const COMPARE_TABLE = document.getElementById("compare-field-table");
const COMPARE_TABLE_BODY = document.getElementById("compare-field-table-tbody");
const TARGET_SELECT = document.getElementById("target-select");
const LOADING_SECTION = document.getElementById("loading-info");
const POST_ENDPOINT = `${window.location.pathname}${window.location.search}`;
const PLAYER_LINK = window.location.pathname.replace("compare", "player");
const CACHE = {};

const XHR_COMPARE = new XMLHttpRequest();

const COLUMNS_ORDER = {
  "total": "count-small border-thin",
  "hits": "count-small",
  "hit_avg": "count border-thin",
  "crits": "count-small",
  "crit_avg": "count",
  "percent": "count border",
};

const get_cell_value = (tr, idx) => tr.children[idx].innerText.replace(/[% ]/g, "");
const comparer = idx => (a, b) => get_cell_value(b, idx) - get_cell_value(a, idx);
function sort_by_column(th) {
  Array.from(COMPARE_TABLE_BODY.querySelectorAll("tr"))
       .sort(comparer(th.cellIndex))
       .forEach(tr => COMPARE_TABLE_BODY.appendChild(tr));
}

function get_targets_cache() {
  if (!CACHE[SELECT_CLASS.value]) CACHE[SELECT_CLASS.value] = {};
  return CACHE[SELECT_CLASS.value];
}

function object_is_empty(o) {
  return Object.keys(o).length === 0;
}

function new_option(value, name) {
  const option = document.createElement("option");
  option.value = value;
  option.append(name);
  return option;
}

function add_targets(targets) {
  TARGET_SELECT.innerHTML = "";
  TARGET_SELECT.style.display = object_is_empty(targets) ? "none" : "";
  TARGET_SELECT.appendChild(new_option("all", "Any target"));
  for (const guid in targets) {
    TARGET_SELECT.appendChild(new_option(guid, targets[guid]));
  }
}

function add_spells(spells) {
  SELECT_SPELL.innerHTML = "";
  SELECT_SPELL.style.display = object_is_empty(spells) ? "none" : "";
  for (const id in spells) {
    SELECT_SPELL.appendChild(new_option(id, spells[id]["name"]));
  }
}

function new_table_cell(value, class_name) {
  const td = document.createElement("td");
  td.className = class_name;
  if (value) td.append(value);
  return td;
}

function player_name_cell(player_name) {
  const a = document.createElement("a");
  a.className = SELECT_CLASS.value;
  a.href = `${PLAYER_LINK}${player_name}/${window.location.search}`;
  a.target = "_blank";
  a.append(player_name);

  const name_cell = new_table_cell(a, "player-cell");
  return name_cell;
}

function new_table_row(spell_data) {
  const row = document.createElement("tr");

  row.appendChild(player_name_cell(spell_data["NAME"]));

  const spell_name = SELECT_SPELL.value;
  row.appendChild(new_table_cell(spell_data.ACTUAL[spell_name] ?? "0", "total-cell"));
  row.appendChild(new_table_cell(spell_data.REDUCED[spell_name], "total-cell border"));
  row.appendChild(new_table_cell(spell_data.CASTS[spell_name], "count-small"));
  row.appendChild(new_table_cell(spell_data.MISSES[spell_name], "count-small border"));
  
  const hits = spell_data.HITS[spell_name] ?? {};
  for (const t of ["HIT", "DOT"]) {
    const h = hits[t] ?? {};
    for (const key in COLUMNS_ORDER) {
      row.appendChild(new_table_cell(h[key], COLUMNS_ORDER[key]));
    }
  }

  return row;
}

function populate_table() {
  COMPARE_TABLE_BODY.innerHTML = "";

  const _cache = get_targets_cache();
  const parsed_json = _cache[TARGET_SELECT.value];
  if (!parsed_json || parsed_json.PLAYERS.length == 0) {
    LOADING_SECTION.className = "no-players";
    return;
  }
  
  for (const player_data of parsed_json.PLAYERS) {
    COMPARE_TABLE_BODY.append(new_table_row(player_data));
  }

  const totalHeader = document.querySelector("th.player-cell + th");
  sort_by_column(totalHeader);

  LOADING_SECTION.style.display = "none";
  COMPARE_TABLE.style.removeProperty("display");
}

function display_new_data(parsed_json) {
  COMPARE_TABLE.style.display = "none";

  const current_target = TARGET_SELECT.value;
  const current_spell = SELECT_SPELL.value;
  
  add_targets(parsed_json.TARGETS);
  add_spells(parsed_json.SPELLS);
  
  if (!parsed_json || parsed_json.PLAYERS.length == 0) {
    LOADING_SECTION.className = "no-players";
    return;
  }
  
  TARGET_SELECT.value = current_target;
  if (TARGET_SELECT.value == "") TARGET_SELECT.value = "all";
  SELECT_SPELL.value = current_spell;
  if (SELECT_SPELL.value == "") SELECT_SPELL.value = SELECT_SPELL.firstElementChild.value;

  populate_table();
}

function new_post_json() {
  const json = {
    "class": SELECT_CLASS.value,
  };
  if (TARGET_SELECT.value && TARGET_SELECT.value != "all") {
    json["target"] = TARGET_SELECT.value;
  }
  return json;
}

function new_class_selected() {
  COMPARE_TABLE.style.display = "none";

  const _cache = get_targets_cache();
  const parsed_json = _cache[TARGET_SELECT.value];
  if (parsed_json) {
    display_new_data(parsed_json);
    return;
  }

  LOADING_SECTION.className = "loading";
  LOADING_SECTION.style.removeProperty("display");

  XHR_COMPARE.open("POST", POST_ENDPOINT);
  XHR_COMPARE.send(JSON.stringify(new_post_json()));
}


function init() {
  new_class_selected();

  document.querySelectorAll("#compare-field-table-headers th").forEach(th => th.addEventListener("click", () => sort_by_column(th)));
  
  SELECT_CLASS.addEventListener("change", new_class_selected);
  SELECT_SPELL.addEventListener("change", populate_table);
  TARGET_SELECT.addEventListener("change", new_class_selected);

  XHR_COMPARE.onreadystatechange = () => {
    if (XHR_COMPARE.status != 200 || XHR_COMPARE.readyState != 4) return;
    
    const parsed_json = JSON.parse(XHR_COMPARE.response);
    
    const _cache = get_targets_cache();
    const current_target = TARGET_SELECT.value || "all";
    _cache[current_target] = parsed_json;
  
    
    display_new_data(parsed_json);
  }
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
