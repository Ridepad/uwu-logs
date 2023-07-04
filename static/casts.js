const CASTS_SECTION_WRAP = document.getElementById("casts-section-wrap");
const TIMELINE_MULT_RANGE = document.getElementById("spell-timeline-mult");
const TIMELINE_MULT_LABEL = document.getElementById("spell-timeline-mult-label");
const TIMELINE_RULER = document.getElementById("timeline-ruler");
const SECTION_FAV = document.getElementById("spells-fav");
const TABS_WRAP = document.getElementById("tabs-wrap");

const TOOLTIP = document.getElementById("the-tooltip");
const TOOLTIP_TIME = document.getElementById("tooltip-time");
const TOOLTIP_FLAG = document.getElementById("tooltip-flag");
const TOOLTIP_SOURCE = document.getElementById("tooltip-source");
const TOOLTIP_TARGET = document.getElementById("tooltip-target");
const TOOLTIP_DATA = document.getElementById("tooltip-data");

const AURA_CONTROLS = document.getElementById("aura-controls");
const BUTTON_FAV = document.getElementById("button-fav");
const BUTTON_DEL = document.getElementById("button-del");

const TABLE_WRAP = document.querySelector(".table-wrap");
const SPELL_TOGGLE_HIDDEN = document.getElementById("spell-toggle-hidden");
const CDN_LINK = "https://icons.wowdb.com/retail/large";
const AURA_REFRESH = ["SPELL_AURA_APPLIED_DOSE", "SPELL_AURA_REMOVED_DOSE", "SPELL_AURA_REFRESH"];
const AURA_ONOFF = ["SPELL_AURA_APPLIED", "SPELL_AURA_REMOVED"];

const BOSS_REMINDER = document.getElementById("boss-reminder");
const SELECT_ATTEMPTS_WRAP = document.getElementById("select-attempts-wrap");
const SELECT_ATTEMPTS = document.getElementById("select-attempts");
const SELECT_PLAYERS_WRAP = document.getElementById("select-players-wrap");
const SELECT_PLAYERS = document.getElementById("select-players");
const DIALOG_MSG = document.getElementById("dialog-msg");
const DIALOG_CHARACTER_SELECTION = document.getElementById("add-character-dialog");
const BUTTON_ADD_CHARACTER = document.getElementById("add-character");
const INPUT_REPORT_ID = document.getElementById("input-report-id");
const BUTTON_FETCH_SEGMENTS = document.getElementById("fetch-report-slices");
const BUTTON_CONFIRM = document.getElementById("button-confirm");
const BUTTON_CANCEL = document.getElementById("button-cancel");

const DEFAULT_COLORS = {
  "SWING_DAMAGE": "#DCDCDC",
  "SPELL_DAMAGE": "#3F3FCF",
  "SPELL_MISSED": "#FF0000",
  "SWING_MISSED": "#FF0000",
  "RANGE_MISSED": "#FF0000",
  "SPELL_PERIODIC_MISSED": "#FF0000",
  "SPELL_PERIODIC_DAMAGE": "#783C9F",
  "SPELL_AURA_APPLIED": "#179900",
  "SPELL_AURA_APPLIED_DOSE": "#C0B300",
  "SPELL_AURA_REMOVED_DOSE": "#C0B300",
  "SPELL_AURA_REFRESH": "#C0B300",
  "SPELL_AURA_REMOVED": "#FF631A",
  "SPELL_CAST_START": "#9200CC",
  "SPELL_CAST_SUCCESS": "#00CC44",
  "SPELL_ENERGIZE": "#80ECFF",
  "SPELL_PERIODIC_ENERGIZE": "#80ECFF",
}
const TIMELINE_TICK_TYPES = {
  0: "timeline-ruler-second",
  5: "timeline-ruler-half-second",
}

const localStorage_to_array = key => (localStorage.getItem(key) ?? "").split(",");
const SPELLS_FAV = new Set(localStorage_to_array("fav"));
const SPELLS_HIDE = new Set(localStorage_to_array("hide"));

const CHARACTERS = [];

function get_pad_value(element) {
  return element.getAttribute("data-pad");
}

function create_new_cleu(flag) {
  const spellCleu = document.createElement("spell-cleu");
  spellCleu.className = flag;
  add_tooltip_event(spellCleu);
  return spellCleu;
}

function new_fake_applied(cleu) {
  const _applied = create_new_cleu("SPELL_AURA_APPLIED");
  _applied.setAttribute("data-time", 0);
  for (let attr of ["data-source", "data-target", "data-etc"]) {
    _applied.setAttribute(attr, cleu.getAttribute(attr));
  }
  _applied.style.setProperty("--left", 0);
  _applied.style.width = get_pad_value(cleu) + "%";
  return _applied;
}

function add_fake_applied(row, cleus) {
  const first_cleu = cleus[0];
  if (first_cleu.className == "SPELL_AURA_REMOVED") {
    const spellHistory = row.querySelector(".spell-history");
    const _applied = new_fake_applied(first_cleu);
    spellHistory.insertBefore(_applied, spellHistory.firstChild);
  }
  
  const last_cleu = cleus.at(-1);
  if (last_cleu.className == "SPELL_AURA_APPLIED") {
    last_cleu.style.width = 100 - get_pad_value(last_cleu) + "%";
  }
}

function change_applied_width(new_array) {
  let start = null;
  for (let i=0; i<new_array.length; i++) {
    const cleu = new_array[i];
    const flag = cleu.className;
    if (flag == "SPELL_AURA_APPLIED") {
      if (!start) start = cleu;
    } else if (start && flag == "SPELL_AURA_REMOVED") {
      start.style.width = get_pad_value(cleu) - get_pad_value(start) + "%";
      start = null;
    }
  }
}

function toggle_aura_duration(row) {
  const events = Array.from(row.querySelectorAll("spell-cleu"));
  const auras = events.filter(e => AURA_ONOFF.includes(e.className));

  if (auras.length > 0) {
    add_fake_applied(row, auras);
  } else {
    const lastEvent = events.filter(e => AURA_REFRESH.includes(e.className)).at(-1);
    if (lastEvent) {
      const _new = lastEvent.cloneNode();
      _new.setAttribute("data-pad", "100");
      const spellHistory = row.querySelector(".spell-history");
      spellHistory.insertBefore(new_fake_applied(_new), spellHistory.firstChild);
    }
  }

  change_applied_width(auras);
}

function toggle_aura_duration_wrap() {
  for (let row of document.getElementsByClassName("spell-row")) {
    toggle_aura_duration(row);
  }
}

function spell_count(row) {
  let c = 0;
  for (let cleu of row.querySelectorAll("spell-cleu")) {
    if (cleu.style.visibility != "hidden") c = c + 1;
  }
  return c
}

function toggle_rows(parent) {
  const to_hide = [];
  const to_sort = [];
  for (let row of parent.getElementsByClassName("spell-row")) {
    const count = spell_count(row);
    row.querySelector(".spell-name").setAttribute('data-count', count);
    if (count == 0) {
      row.style.display = "none";
      to_hide.push(row);
    } else {
      row.style.display = "";
      to_sort.push(row);
    }
  }

  to_sort.sort((a, b) => b.getAttribute("data-spell-name") < a.getAttribute("data-spell-name"))
         .forEach(row => parent.appendChild(row));
  to_hide.forEach(row => parent.appendChild(row));
}

function toggle_rows_wrap() {
  for (let section of document.getElementsByClassName("casts-section")) {
    for (let category of section.children) {
      toggle_rows(category);
    }
  }
}

function init_flag_filter() {
  function change_color(flag, color) {
    const style = document.createElement("style");
    style.append(`.${flag} {color: ${color}}`);
    document.head.appendChild(style);
  }
  function toggle_nodes(flag, checked) {
    const visibility = checked ? "visible" : "hidden";
    for (let div of document.getElementsByClassName(flag)) {
      div.style.visibility = visibility; 
    }
  }
  document.querySelectorAll("#flag-filter li").forEach(li => {
    const flag = li.id;
    const label = li.querySelector("label");
    const checkbox = li.querySelector(".flag-checkbox");
    const colorPicker = li.querySelector(".flag-color-picker");
    const color_ID = `${flag}_COLOR`;

    checkbox.checked = localStorage.getItem(flag) !== "false";
    colorPicker.value = localStorage.getItem(color_ID) ?? DEFAULT_COLORS[flag] ?? "#DCDCDC";
    label.style.setProperty('--secondary-color', colorPicker.value);
    change_color(flag, colorPicker.value);
    toggle_nodes(flag, checkbox.checked);
    
    checkbox.addEventListener("change", () => {
      toggle_nodes(flag, checkbox.checked);
      toggle_rows_wrap();
      localStorage.setItem(flag, checkbox.checked);
    });
    colorPicker.addEventListener("change", () => {
      label.style.setProperty('--secondary-color', colorPicker.value);
      change_color(flag, colorPicker.value);
      localStorage.setItem(color_ID, colorPicker.value);
    });
  })
}

function toggle_timeline_labels_big(lessthan) {
  const zoom = TIMELINE_MULT_RANGE.value;
  const visibility = zoom < lessthan ? "hidden" : "visible";
  const divs = document.getElementsByClassName("timeline-ruler-second");
  for (let i = 0; i < divs.length; i++) {
    if (i%5 == 0) continue;
    divs[i].firstElementChild.style.visibility = visibility;
  }
}
function toggle_timeline_labels(classname, lessthan) {
  const zoom = TIMELINE_MULT_RANGE.value;
  const visibility = zoom < lessthan ? "hidden" : "visible";
  for (let div of document.getElementsByClassName(classname)) {
    div.firstElementChild.style.visibility = visibility;
  }
}
function change_zoom() {
  TABLE_WRAP.style.display = "none";
  console.time('zoom');
  const zoom = TIMELINE_MULT_RANGE.value;
  localStorage.setItem("ZOOM", zoom);
  TIMELINE_MULT_LABEL.innerText = `${zoom}x`;
  CASTS_SECTION_WRAP.style.setProperty("--mult", zoom);
  console.timeEnd('zoom');
  console.time('toggle');
  const m = window.screen.width > 2000 ? 2 : 1;
  toggle_timeline_labels("timeline-ruler-tenth-second", 35 * m);
  toggle_timeline_labels("timeline-ruler-half-second", 10 * m);
  toggle_timeline_labels_big(6 * m);
  console.timeEnd('toggle');
  TABLE_WRAP.style.display = "";
}

function new_timeline_text(sec, tenth) {
  const minutes = Math.floor(sec/60);
  const seconds = `${sec%60}`.padStart(2, '0');
  return tenth ? `${minutes}:${seconds}.${tenth}` : `${minutes}:${seconds}`;
}
function create_timeline_tick(milliseconds) {
  const tick = document.createElement("div");
  const tenth_of_sec = milliseconds%10;
  const tick_type = TIMELINE_TICK_TYPES[tenth_of_sec] ?? "timeline-ruler-tenth-second";
  tick.classList.add("timeline-ruler-tick", tick_type);
  const number = document.createElement("div");
  number.classList.add("timeline-ruler-number");
  const seconds = Math.floor(milliseconds/10);
  number.innerText = new_timeline_text(seconds, tenth_of_sec);
  tick.appendChild(number);
  return tick
}
function make_timeline(start) {
  console.time('make_timeline');

  const fragment = new DocumentFragment();
  const duration = TIMELINE_RULER.getAttribute("data-duration") * 10 - 1;
  let milliseconds = start ?? 0;
  for (; milliseconds<=duration; milliseconds++) {
    fragment.appendChild(create_timeline_tick(milliseconds));
  }
  TIMELINE_RULER.append(fragment);

  console.timeEnd('make_timeline');
}

function array_remove(array, item) {
  let index = array.indexOf(item);
  while (index > -1) {
    array.splice(index, 1);
    index = array.indexOf(item);
  }
}

function add_control_events(CASTS_SECTION) {
  const tab_n = CASTS_SECTION.getAttribute("data-tab");
  const sectionMain = CASTS_SECTION.querySelector("spells-main");

  const _data = {
    fav: {},
    hide: {},
  }

  for (let z in _data) {
    const spells = localStorage.getItem(z) ? localStorage.getItem(z).split(",") : [];
    _data[z]["spells"] = Array.from(new Set(spells));
    _data[z]["element"] = CASTS_SECTION.querySelector(`spells-${z}`);
  }

  for (let row of sectionMain.querySelectorAll("spell-row")) {
    const spell_id = row.getAttribute("data-spell-id");
    for (let z in _data) {
      if (_data[z]["spells"].includes(spell_id)) {
        _data[z]["element"].appendChild(row);
      }
    }
  }
  
  const insert_before = (parent, element) => {
    const spellname = element.getAttribute("data-spell-name");
    for (let row of parent.children) {
      if (row.getAttribute("data-spell-name") > spellname) return parent.insertBefore(element, row);
    }
    parent.appendChild(element);
  }
  const spellsFav = _data["fav"]["spells"];
  const SPELLS_HIDE = _data["hide"]["spells"];
  const onevent = e => {
    const row = e.target.closest("spell-row");
    const spell_id = row.getAttribute("data-spell-id");
    array_remove(spellsFav, spell_id);
    array_remove(SPELLS_HIDE, spell_id);
    
    const key = e.target == BUTTON_FAV ? "fav" : "hide";
    const section = _data[key]["element"];
    if (row.parentElement != section) {
      const array = _data[key]["spells"];
      array.push(spell_id);
      insert_before(section, row);
    } else {
      insert_before(sectionMain, row);
    }

    localStorage.setItem("fav", spellsFav.toString());
    localStorage.setItem("hide", SPELLS_HIDE.toString());
  }
  BUTTON_FAV.addEventListener("click", onevent);
  BUTTON_DEL.addEventListener("click", onevent);

  CASTS_SECTION.querySelectorAll(".spell-name").forEach(e => {
    const div = e.querySelector("div");
    e.addEventListener('mouseover', () => {
      const section = e.closest("spell-row").parentElement;
      BUTTON_FAV.textContent = section == _data["fav"]["element"] ? "▼" : "▲";
      BUTTON_DEL.textContent = section == _data["hide"]["element"] ? "✚" : "✖";
      div.appendChild(AURA_CONTROLS);
      AURA_CONTROLS.style.display = "";
    });
    e.addEventListener("mouseleave", () => {
      AURA_CONTROLS.style.display = "none";
    });
  });
}

function add_tooltip_info(cleu) {
  // console.log(cleu.parentNode.parentNode);
  TOOLTIP_FLAG.textContent = cleu.className;
  TOOLTIP_TIME.textContent = new_timestamp(cleu.getAttribute("data-time"));
  TOOLTIP_SOURCE.textContent = cleu.getAttribute("data-source");
  TOOLTIP_TARGET.textContent = cleu.getAttribute("data-target");
  TOOLTIP_DATA.textContent = cleu.getAttribute("data-etc");
}
function move_tooltip_to(cleu) {
  const bodyRect = document.body.getBoundingClientRect();
  const elemRect = cleu.getBoundingClientRect();
  const elemRect2 = cleu.parentNode.previousSibling.getBoundingClientRect();
  const _left = Math.max(elemRect.left, elemRect2.right);
  TOOLTIP.style.top = elemRect.bottom - bodyRect.top + 'px';
  TOOLTIP.style.right = bodyRect.right - _left + 'px';
}
function mouseenter(event) {
    move_tooltip_to(event.target);
    add_tooltip_info(event.target);
    TOOLTIP.style.display = "";
}
function mouseleave() {
    TOOLTIP.style.display = "none";
}
function add_tooltip_event(cleu) {
  cleu.addEventListener("mouseenter", mouseenter);
  cleu.addEventListener("mouseleave", mouseleave);
}

function reveal_new_flags(flags_list) {
  for (let flag of flags_list) {
    const li = document.getElementById(flag);
    if (li.style.display == "none") li.style.display = "";
  }
}

function check_timeline(new_duraion) {
  const current_duration = parseFloat(TIMELINE_RULER.getAttribute("data-duration") || 0);
  console.log(new_duraion, current_duration);
  if (current_duration >= new_duraion) return;
  
  TIMELINE_RULER.setAttribute("data-duration", new_duraion);
  TABLE_WRAP.style.setProperty("--duration", new_duraion);
  make_timeline(parseInt(current_duration*10));
  change_zoom();
}



function makeQuery(name) {
  const current_query = new URLSearchParams(window.location.search);
  const boss = current_query.get("boss");
  const new_query = {
    name: name,
  };
  if (!boss) return;
  
  new_query.boss = boss;
  if (SELECT_ATTEMPTS.value) {
    new_query.attempt = SELECT_ATTEMPTS.value;
  } else {
    new_query.attempt = current_query.get("attempt") || -1;
  }
  console.log(JSON.stringify(new_query));
  return JSON.stringify(new_query);
}

function new_timestamp(t) {
  const m = ~~(t / 60);
  const s = (~~(t % 60)).toString().padStart(2, "0");
  const ms = (t * 1000 % 1000).toString().padStart(3, "0");
  return `${m}:${s}.${ms}`;
}

function section_append(section, row) {
  if (!row) return;

  if (section == SECTION_FAV) {
    const tab_n = row.getAttribute("data-tab-n");
    row.classList.add(`char-${tab_n}`);
  }
  
  const spellname = row.getAttribute("data-spell-name");
  for (let _row of section.children) {
    if (_row.getAttribute("data-spell-name") > spellname) {
      section.insertBefore(row, _row);
      return;
    }
  }
  
  section.appendChild(row);
}


class Character {
  constructor(report_id, name) {
    this.CASTS_SECTION = document.createElement("div");
    this.CASTS_SECTION.style.display = "none";
    CASTS_SECTION_WRAP.appendChild(this.CASTS_SECTION);
    this.REPORT_ID = report_id;
    this.NAME = name;
    this.TAB_N = CHARACTERS.length;
    CHARACTERS.push(this);
    
    const req = new XMLHttpRequest();
    req.onreadystatechange = () => {
      if (req.status != 200 || req.readyState != 4) return;
      
      this.PARSED_DATA = req.response ? JSON.parse(req.response) : {};

      this.CLASS = this.PARSED_DATA.CLASS;
      
      this.DURATION = parseFloat(this.PARSED_DATA.RDURATION);
      this.WIDTH = `calc(var(--mult) * ${this.DURATION*10}px + 2px)`;
      
      setTimeout(() => check_timeline(this.DURATION));      
      setTimeout(() => this.new_character());
    }
    req.open("POST", `/reports/${report_id}/casts/`);
    req.setRequestHeader("Content-Type", "application/json");
    req.send(makeQuery(name));
  }

  new_spell_name_cell(spell_id) {
    const name_cell = document.createElement("div");
    name_cell.className = "spell-name";

    const _img = document.createElement("img");
    _img.src = `${CDN_LINK}/${this.SPELLS[spell_id]['icon']}.jpg`;
    _img.alt = spell_id;
    name_cell.appendChild(_img);

    const _a = document.createElement("a");
    _a.className = this.SPELLS[spell_id]['color'];
    _a.href = `/reports/${this.REPORT_ID}/spell/${spell_id}/${window.location.search}`;
    _a.append(this.SPELLS[spell_id]['name']);
    name_cell.appendChild(_a);
    
    const _div = document.createElement("div");
    name_cell.appendChild(_div);
    
    return name_cell;
  }

  new_cleu(cleu_data) {
    const [timestamp, flag, source, target, etc] = cleu_data;
    const pad = (timestamp / this.DURATION * 100).toFixed(3);
    const spellCleu = create_new_cleu(flag);
    spellCleu.style.setProperty("--left", `${pad}%`);
    spellCleu.setAttribute("data-time", timestamp);
    spellCleu.setAttribute("data-source", source);
    spellCleu.setAttribute("data-target", target);
    spellCleu.setAttribute("data-etc", etc);
    spellCleu.setAttribute("data-pad", pad);
    return spellCleu;
  }

  new_spell_history_cell(spell_id) {
    const spellHistory = document.createElement("div");
    spellHistory.className = "spell-history";
    for (let cleu_data of this.CASTS_DATA[spell_id]) {
      spellHistory.appendChild(this.new_cleu(cleu_data));
    }
    return spellHistory;
  }

  add_spell_rows() {
    for (let spell_id in this.CASTS_DATA) {
      const spellRow = document.createElement("spell-row");
      spellRow.className = "spell-row";
      spellRow.setAttribute("data-tab-n", this.TAB_N);
      spellRow.setAttribute("data-spell-id", spell_id);
      spellRow.setAttribute("data-spell-name", this.SPELLS[spell_id]['name']);
      spellRow.appendChild(this.new_spell_name_cell(spell_id));
      spellRow.appendChild(this.new_spell_history_cell(spell_id));
      spellRow.style.width = this.WIDTH;

      this.SPELLS_MAIN.appendChild(spellRow);
    }
  }

  new_character() {
    console.log(this.PARSED_DATA);
    this.SPELLS = this.PARSED_DATA.SPELLS;
    this.CASTS_DATA = this.PARSED_DATA.DATA;

    this.SPELLS_MAIN = document.createElement("spells-main");
    this.SPELLS_MAIN.className = "casts-section-main";
    
    this.SPELLS_HIDE = document.createElement("spells-hide");
    this.SPELLS_HIDE.className = "spells-hide";
    this.SPELLS_HIDE.style.display = SPELL_TOGGLE_HIDDEN.checked ? "" : "none";
    
    this.CASTS_SECTION.appendChild(this.SPELLS_MAIN);
    this.CASTS_SECTION.appendChild(this.SPELLS_HIDE);
    this.CASTS_SECTION.className = "casts-section";
    this.CASTS_SECTION.setAttribute("data-tab", this.TAB_N);

    this.add_spell_rows();

    reveal_new_flags(this.PARSED_DATA.FLAGS);

    toggle_aura_duration_wrap();
    init_flag_filter();
    toggle_rows_wrap();
    this.add_control_events();
    this.new_tab();
    this.hide_other();
    this.CASTS_SECTION.style.display = "";
    DIALOG_CHARACTER_SELECTION.close();
  }

  add_control_events() {
    this.CASTS_SECTION.querySelectorAll(".spell-name").forEach(e => {
      const div = e.querySelector("div");
      e.addEventListener('mouseover', () => {
        const section = e.closest("spell-row").parentElement;
        BUTTON_DEL.textContent = section == this.SPELLS_HIDE ? "✚" : "✖";
        BUTTON_FAV.style.display = section == SECTION_FAV ? "none" : "";
        div.appendChild(AURA_CONTROLS);
        AURA_CONTROLS.style.display = "";
      });
      e.addEventListener("mouseleave", () => AURA_CONTROLS.style.display = "none");
    });

    for (let row of this.SPELLS_MAIN.querySelectorAll("spell-row")) {
      const spell_id = row.getAttribute("data-spell-id");
      if (SPELLS_FAV.has(spell_id)) {
        section_append(SECTION_FAV, row);
      } else if (SPELLS_HIDE.has(spell_id)) {
        section_append(this.SPELLS_HIDE, row);
      }
    }
  }
  new_tab() {
    const wrap = document.createElement("div");
    const input = document.createElement("input");
    input.id = `char-${this.TAB_N}-tab`;
    input.type = "radio";
    input.name = "char-tab";
    input.addEventListener("change", () => {
      this.CASTS_SECTION.style.display = input.checked ? "" : "none";
      this.hide_other();
    });
    wrap.appendChild(input);

    const label = document.createElement("label");
    label.className = "char-tab";
    label.htmlFor = input.id;
    label.textContent = this.NAME;
    wrap.appendChild(label);

    const report_link = document.createElement("a");
    report_link.className = "char-report-id";
    report_link.target = "_blank";
    report_link.href = `/reports/${this.REPORT_ID}`;
    report_link.textContent = this.REPORT_ID;
    wrap.appendChild(report_link);

    const armory_link = document.createElement("a");
    armory_link.className = "warmane-armory-link";
    armory_link.target = "_blank";
    const SERVER = this.REPORT_ID.split("--").at(-1);
    armory_link.href = `http://armory.warmane.com/character/${this.NAME}/${SERVER}`;
    armory_link.textContent = "Armory⇗";
    wrap.appendChild(armory_link);

    TABS_WRAP.insertBefore(wrap, BUTTON_ADD_CHARACTER);
  }
  hide_other() {
    for (let character of CHARACTERS) {
      if (this !== character) {
        character.CASTS_SECTION.style.display = "none";
      }
    }
  }
}

function save_spells_local_storage() {
  localStorage.setItem("fav", [...SPELLS_FAV]);
  localStorage.setItem("hide", [...SPELLS_HIDE]);
}

BUTTON_DEL.addEventListener("click", e => {
  const _row = e.target.closest("spell-row");
  const spell_id = _row.getAttribute("data-spell-id");
  const css_query = `[data-spell-id="${spell_id}"]`;
  SPELLS_FAV.delete(spell_id);
  SPELLS_HIDE.delete(spell_id);

  if (_row.parentElement == SECTION_FAV) {
    for (let row of document.querySelectorAll(css_query)) {
      const tab_n = row.getAttribute("data-tab-n");
      section_append(CHARACTERS[tab_n].SPELLS_MAIN, row);
    }
  } else if (_row.closest("spells-main")) {
    SPELLS_HIDE.add(spell_id);
    for (let character of CHARACTERS) {
      const row = character.CASTS_SECTION.querySelector(css_query);
      section_append(character.SPELLS_HIDE, row);
    }
  } else  {
    for (let character of CHARACTERS) {
      const row = character.CASTS_SECTION.querySelector(css_query);
      section_append(character.SPELLS_MAIN, row);
    }
  }

  save_spells_local_storage();
});

BUTTON_FAV.addEventListener("click", e => {
  const _row = e.target.closest("spell-row");
  const spell_id = _row.getAttribute("data-spell-id");
  const css_query = `[data-spell-id="${spell_id}"]`;
  SPELLS_FAV.add(spell_id);
  SPELLS_HIDE.delete(spell_id);

  for (let character of CHARACTERS) {
    const row = character.CASTS_SECTION.querySelector(css_query);
    section_append(SECTION_FAV, row);
  }

  save_spells_local_storage();
});

function newOption(value, text) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = text;
  return option;
}

function get_response_error_wrap(request) {
  DIALOG_MSG.style.color = "red";
    if (request.status == 404) {
      DIALOG_MSG.textContent = "Report wasn't found"
      DIALOG_MSG.style.visibility = "visible";
      return;
    }
    if (request.status == 429) {
      DIALOG_MSG.textContent = `Retry in: ${request.response}`;
      DIALOG_MSG.style.visibility = "visible";
      return;
    }
    if (request.status != 200 || request.readyState != 4) return;
    
    DIALOG_MSG.style.visibility = "hidden";
    return request.response;
}

function get_report_slices() {
  if (!boss) {
    DIALOG_MSG.textContent = "Required slice with boss";
    DIALOG_MSG.style.color = "red";
    DIALOG_MSG.style.visibility = "visible";
    return;
  }
  const report_id = INPUT_REPORT_ID.value;
  if (!report_id) return;

  const fetch_segments = new XMLHttpRequest();
  fetch_segments.onreadystatechange = () => {
    SELECT_ATTEMPTS.innerHTML = '';

    const response = get_response_error_wrap(fetch_segments);
    console.log(response);
    if (!response) return;
    const parsed_json = JSON.parse(response);
    
    const segments = parsed_json[boss];
    if (!segments) return;

    for (let i in segments) {
      const segment = segments[i];
      const segment_type = `${segment.duration_str} ${segment.segment_type}`;
      SELECT_ATTEMPTS.appendChild(newOption(i, segment_type))
    }
    SELECT_ATTEMPTS_WRAP.style.visibility = "visible";
    if (SELECT_PLAYERS_WRAP.style.visibility == "visible") {
      BUTTON_CONFIRM.style.visibility = "visible";
    }
  }

  fetch_segments.open("POST", `/reports/${report_id}/report_slices/`);
  fetch_segments.send();

  const fetch_players = new XMLHttpRequest();
  fetch_players.onreadystatechange = () => {
    SELECT_PLAYERS.innerHTML = '';

    const response = get_response_error_wrap(fetch_players);
    console.log(response);
    if (!response) return;
    const parsed_json = JSON.parse(response);
    
    for (let player_name in parsed_json) {
      if (parsed_json[player_name] == CHARACTERS[0].CLASS) {
        SELECT_PLAYERS.appendChild(newOption(player_name, player_name))
      }
    }

    SELECT_PLAYERS_WRAP.style.visibility = "visible";
    if (SELECT_ATTEMPTS_WRAP.style.visibility == "visible") {
      BUTTON_CONFIRM.style.visibility = "visible";
    }
  }

  fetch_players.open("POST", `/reports/${report_id}/players_classes/`);
  fetch_players.send();
}

TIMELINE_MULT_RANGE.value = localStorage.getItem("ZOOM") || "3";
TIMELINE_MULT_RANGE.addEventListener("change", change_zoom);
change_zoom();

SPELL_TOGGLE_HIDDEN.checked = localStorage.getItem("show-hidden") === "true";
SPELL_TOGGLE_HIDDEN.addEventListener("change", () => {
  for (let SPELLS_HIDE of CASTS_SECTION_WRAP.querySelectorAll("spells-hide")) {
    SPELLS_HIDE.style.display = SPELL_TOGGLE_HIDDEN.checked ? "" : "none";
    localStorage.setItem("show-hidden", SPELL_TOGGLE_HIDDEN.checked);
  }
});
BUTTON_ADD_CHARACTER.addEventListener("click", () => {
  DIALOG_MSG.style.visibility = "hidden";
  BUTTON_CONFIRM.style.visibility = "hidden";
  SELECT_ATTEMPTS_WRAP.style.visibility = "hidden";
  SELECT_PLAYERS_WRAP.style.visibility = "hidden";
  DIALOG_CHARACTER_SELECTION.showModal();
});
INPUT_REPORT_ID.addEventListener("keypress", event => event.key == "Enter" && get_report_slices());
BUTTON_FETCH_SEGMENTS.addEventListener("click", () => get_report_slices());
BUTTON_CONFIRM.addEventListener("click", () => {
  DIALOG_MSG.textContent = "Loading...";
  DIALOG_MSG.style.color = "gainsboro";
  DIALOG_MSG.style.visibility = "visible";
  new Character(INPUT_REPORT_ID.value, SELECT_PLAYERS.value);
});
BUTTON_CANCEL.addEventListener("click", () => DIALOG_CHARACTER_SELECTION.close());

const current_query = new URLSearchParams(window.location.search);
const boss = current_query.get("boss");
if (boss) {
  TABS_WRAP.style.display = "";
  BOSS_REMINDER.style.display = "none";
  const _pathname = window.location.pathname.split('/');
  new Character(_pathname[2], _pathname[4]);
} else {
  BOSS_REMINDER.style.display = "";
}
