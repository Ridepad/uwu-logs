const CASTS_SECTION_WRAP = document.getElementById("casts-section-wrap");
const TIMELINE_MULT_RANGE = document.getElementById("spell-timeline-mult");
const TIMELINE_MULT_LABEL = document.getElementById("spell-timeline-mult-label");
const TIMELINE_RULER = document.getElementById("timeline-ruler");
const SECTION_FAV = document.getElementById("spells-fav");
const TABS_WRAP = document.getElementById("tabs-wrap");
const FIGHT_START = document.getElementById("fight-start");

const TOOLTIP = document.getElementById("the-tooltip");
const TOOLTIP_TIME = document.getElementById("tooltip-time");
const TOOLTIP_FLAG = document.getElementById("tooltip-flag");
const TOOLTIP_SOURCE = document.getElementById("tooltip-source");
const TOOLTIP_TARGET = document.getElementById("tooltip-target");
const TOOLTIP_DATA = document.getElementById("tooltip-data");

const AURA_CONTROLS = document.getElementById("aura-controls");
const BUTTON_FAV = document.getElementById("button-fav");
const BUTTON_HIDE = document.getElementById("button-hide");
const BUTTON_UNHIDE = document.getElementById("button-unhide");
const SELECT_BEFORE_PULL = document.getElementById("before-pull");

const TABLE_WRAP = document.querySelector(".table-wrap");
const SPELL_TOGGLE_HIDDEN = document.getElementById("spell-toggle-hidden");
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
const HTML_MAIN = document.querySelector("main");

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

CONFIG = {
  max_duration: 0,
  shift: parseInt(SELECT_BEFORE_PULL.value),
}

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
  _applied.setAttribute("data-time", (-CONFIG.shift).toFixed(1));
  for (let attr of ["data-source", "data-target", "data-etc", "data-guid"]) {
    _applied.setAttribute(attr, cleu.getAttribute(attr));
  }
  _applied.style.width = get_pad_value(cleu) + "%";
  return _applied;
}

function add_fake_applied(spellHistory, events) {
  const first_cleu = events[0];
  if (first_cleu.className == "SPELL_AURA_REMOVED") {
    const end = Math.abs(first_cleu.getAttribute("data-time"));
    const start = SELECT_BEFORE_PULL.value;
    if (start > end) {
      const _applied = new_fake_applied(first_cleu);
      spellHistory.insertBefore(_applied, spellHistory.firstChild);
    }
  }
  
  const last_cleu = events.at(-1);
  if (last_cleu.className == "SPELL_AURA_APPLIED") {
    last_cleu.style.width = 100 - get_pad_value(last_cleu) + "%";
  }
}

function split_by_guid(row) {
  const events = Array.from(row.querySelectorAll("spell-cleu"));
  const events_split = {};
  for (const event of events) {
    const guid = event.getAttribute("data-guid");
    if (!events_split[guid]) events_split[guid] = [];
    events_split[guid].push(event);
  }
  return events_split;
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

function toggle_aura_duration_guid(events, parent) {
  const auras = events.filter(e => AURA_ONOFF.includes(e.className));

  if (auras.length > 0) {
    add_fake_applied(parent, auras);
  } else {
    const lastEvent = events.filter(e => AURA_REFRESH.includes(e.className)).at(-1);
    if (lastEvent) {
      const _new = lastEvent.cloneNode();
      _new.setAttribute("data-pad", "100");
      parent.insertBefore(new_fake_applied(_new), parent.firstChild);
    }
  }

  change_applied_width(auras);
}

function toggle_aura_duration(row) {
  const events_split = split_by_guid(row);
  const spellHistory = row.querySelector(".spell-history");
  for (const guid in events_split) {
    toggle_aura_duration_guid(events_split[guid], spellHistory);
  }
}

function get_uptime(events, duration) {
  const shifted_dur = duration + CONFIG.shift;
  const applied = events.filter(e => e.classList.contains("SPELL_AURA_APPLIED"));
  let uptime = 0;
  for (const event of applied) {
    const width = parseFloat(event.style.getPropertyValue("width")) || 0;
    const buff_duration = width * shifted_dur;
    const t = Number(event.getAttribute("data-time")) || 0;
    const before_combat = Math.abs(Math.min(t, 0)) * 100;
    if (buff_duration < before_combat) continue;
    uptime += buff_duration - before_combat;
  }
  return (uptime / duration).toFixed(1) + "%";
}

function spell_row_click(event) {
  const row = event.target.closest("spell-row");
  const spellnamewrap = row.querySelector("spell-name");
  const spellhistory = row.querySelector(".spell-history");
  const spell_history_wrap = row.querySelector("spell-history-wrap");
  if (row.style.getPropertyValue("--row-targets")) {
    row.style.removeProperty("--row-targets");
    row.classList.remove("openned");
    return
  }
  row.classList.add("openned");
  const known_len = row.getAttribute("data-len");
  if (known_len) {
    row.style.setProperty("--row-targets", known_len);
    return
  }

  const events_split = split_by_guid(spellhistory);
  const len = Object.keys(events_split).length;
  row.style.setProperty("--row-targets", len+2);
  row.setAttribute("data-len", len+2);

  const tab_n = row.getAttribute("data-tab-n");
  const duration = CHARACTERS[tab_n].DURATION;
  for (const guid in events_split) {
    const spellinfo = document.createElement("div");
    spellinfo.className = "copy";
    spellinfo.setAttribute("data-uptime", get_uptime(events_split[guid], duration));
    const tname = events_split[guid][0].getAttribute("data-target");
    spellinfo.append(tname);
    spellnamewrap.appendChild(spellinfo);

    const spellrowrow = document.createElement("div");
    spellrowrow.classList.add("spell-history", "copy");
    for (const event of events_split[guid]) {
      const cleu = event.cloneNode();
      add_tooltip_event(cleu);
      spellrowrow.appendChild(cleu);
    }
    spell_history_wrap.appendChild(spellrowrow)
  }
}

function toggle_aura_duration_wrap() {
  for (let row of document.getElementsByClassName("spell-row")) {
    toggle_aura_duration(row);
  }
}

function spell_count(row) {
  let c = 0;
  for (let cleu of row.querySelector(".spell-history").querySelectorAll("spell-cleu")) {
    if (cleu.style.visibility != "hidden") c = c + 1;
  }
  return c
}

function toggle_rows(parent) {
  const to_hide = [];
  const to_sort = [];
  for (let row of parent.getElementsByClassName("spell-row")) {
    const count = spell_count(row);
    row.querySelector("spell-name-data").setAttribute('data-count', count);
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
  toggle_rows(SECTION_FAV);
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
function create_timeline_tick(milliseconds, negative) {
  const tick = document.createElement("div");
  const tenth_of_sec = milliseconds%10;
  const tick_type = TIMELINE_TICK_TYPES[tenth_of_sec] ?? "timeline-ruler-tenth-second";
  tick.classList.add("timeline-ruler-tick", tick_type);
  const number = document.createElement("div");
  number.classList.add("timeline-ruler-number");
  if (negative) {
    number.classList.add("negative");
  }
  const seconds = Math.floor(milliseconds/10);
  number.append(new_timeline_text(seconds, tenth_of_sec));
  tick.appendChild(number);
  if (milliseconds == 0) {
    tick.appendChild(FIGHT_START);
  }
  return tick;
}
function make_timeline(milliseconds) {
  console.time('make_timeline');

  let shift_ms = CONFIG.shift * 10;
  const fragment = new DocumentFragment();
  const duration = CONFIG.max_duration * 10 - 1;

  if (!milliseconds) {
    milliseconds = 0;
    for (; shift_ms>0; shift_ms--) {
      fragment.appendChild(create_timeline_tick(shift_ms, true));
    }

  }
  for (; milliseconds<=duration; milliseconds++) {
    fragment.appendChild(create_timeline_tick(milliseconds));
  }
  TIMELINE_RULER.append(fragment);

  console.timeEnd('make_timeline');
}
function new_timestamp(t) {
  if (t == 0) return "0:00.000";
  const negative = t.charAt(0) == "-" ? "-" : "";
  const [_s, _ms] = t.split(".");
  const _s_abs = Math.abs(_s)
  const m = Math.floor(_s_abs / 60);
  const s = Math.floor(_s_abs % 60).toString().padStart(2, "0");
  const ms = _ms.padEnd(3, "0");
  return `${negative}${m}:${s}.${ms}`;
}
function format_dmg_line(e) {
  const [, dmg, ok, , res, , abs, iscrit,] = e.map(v => parseInt(v)); 
  const crit = iscrit ? "🌟" : "";
  const whole_dmg = dmg + res + abs;
  const res_p = ~~(res / whole_dmg * 100 + 0.1);
  const res_p_s = res == 0 ? 0 : `${res}(${res_p}%)`;
  const abs_s = abs ? `+🛡️${abs}` : "";
  const ok_s = ok ? ` | 💀${ok} ` : "";
  return `${crit}${whole_dmg}${crit} | 🎯${dmg}+🖤${res_p_s}${abs_s}${ok_s}`;
}
function parse_etc(etc) {
  const e = etc.split(",");
  if (e.length == 2) {
    return e[1];
  } else if (e.length == 3) {
    return `${e[1]} (${e[2]})`;
  } else if (e.length == 10) {
    return format_dmg_line(e);
  }
}
function add_tooltip_info(cleu) {
  TOOLTIP_FLAG.textContent = cleu.className;
  TOOLTIP_TIME.textContent = new_timestamp(cleu.getAttribute("data-time"));
  TOOLTIP_SOURCE.textContent = cleu.getAttribute("data-source");
  TOOLTIP_TARGET.textContent = cleu.getAttribute("data-target");
  TOOLTIP_DATA.textContent = parse_etc(cleu.getAttribute("data-etc"));
}
function move_tooltip_to(cleu) {
  const main_rect = document.querySelector("main").getBoundingClientRect();
  const elemRect = cleu.getBoundingClientRect();
  const elemRect2 = cleu.parentNode.parentNode.previousSibling.getBoundingClientRect();
  const _left = Math.max(elemRect.left, elemRect2.right);
  TOOLTIP.style.top = elemRect.bottom - main_rect.top + 'px';
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
  const current_duration = CONFIG.max_duration;
  console.log(new_duraion, current_duration);
  if (current_duration >= new_duraion) return;
  
  CONFIG.max_duration = new_duraion;
  TABLE_WRAP.style.setProperty("--duration", new_duraion+CONFIG.shift);
  make_timeline(parseInt(current_duration*10));
  change_zoom();
}



function makeQuery(name) {
  const current_query = new URLSearchParams(window.location.search);
  const boss = current_query.get("boss");
  const new_query = {
    name: name,
    shift: CONFIG.shift,
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
    this.REPORT_ID = report_id;
    this.NAME = name;

    for (let i=0; i<=CHARACTERS.length+1; i++) {
      if (CHARACTERS[i] === undefined) {
        console.log('char', i, CHARACTERS[i]);
        this.TAB_N = i;
        CHARACTERS[i] = this;
        break
      }
    }
    
    const req = new XMLHttpRequest();
    req.onreadystatechange = () => {
      if (req.status != 200 || req.readyState != 4) return;
      
      const PARSED_DATA = req.response ? JSON.parse(req.response) : {};

      this.SPELLS = PARSED_DATA.SPELLS;
      this.CASTS_DATA = PARSED_DATA.DATA;

      Character.PLAYER_CLASS = Character.PLAYER_CLASS ?? PARSED_DATA.CLASS
      
      this.DURATION = parseFloat(PARSED_DATA.RDURATION);
      setTimeout(() => {
        this.init();
        reveal_new_flags(PARSED_DATA.FLAGS);
      });
    }
    req.open("POST", `/reports/${report_id}/casts/`);
    req.setRequestHeader("Content-Type", "application/json");
    req.send(makeQuery(name));
  }

  init() {
    this.CASTS_SECTION = document.createElement("div");
    this.CASTS_SECTION.style.display = "none";
    CASTS_SECTION_WRAP.appendChild(this.CASTS_SECTION);

    this.WIDTH = `calc(var(--mult) * ${((this.DURATION + CONFIG.shift)*10).toFixed(2)}px)`;
    check_timeline(this.DURATION);
    this.new_character();
  }

  new_spell_name_cell(spell_id) {
    const name_cell_wrap = document.createElement("spell-name");
    name_cell_wrap.className = "spell-name";
    const name_cell = document.createElement("spell-name-data");

    const _img = document.createElement("img");
    _img.src = `/static/icons/${this.SPELLS[spell_id]['icon']}.jpg`;
    _img.alt = spell_id;
    name_cell.appendChild(_img);

    const _a = document.createElement("a");
    _a.className = this.SPELLS[spell_id]['color'];
    _a.href = `/reports/${this.REPORT_ID}/spell/${spell_id}/${window.location.search}`;
    _a.append(this.SPELLS[spell_id]['name']);
    name_cell.appendChild(_a);
    
    name_cell_wrap.appendChild(name_cell);
    return name_cell_wrap;
  }

  new_cleu(cleu_data) {
    const timestamp = cleu_data[0]/1000;
    const pad = (timestamp + CONFIG.shift) / (this.DURATION+CONFIG.shift) * 100;
    const spell_cleu = create_new_cleu(cleu_data[1]);
    spell_cleu.style.setProperty("left", `${pad}%`);
    spell_cleu.setAttribute("data-time", timestamp);
    spell_cleu.setAttribute("data-source", cleu_data[2]);
    spell_cleu.setAttribute("data-target", cleu_data[3]);
    spell_cleu.setAttribute("data-guid", cleu_data[4]);
    spell_cleu.setAttribute("data-etc", cleu_data.at(-1));
    spell_cleu.setAttribute("data-pad", pad);
    return spell_cleu;
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
      
      const spellhistorywrap = document.createElement("spell-history-wrap");
      spellhistorywrap.appendChild(this.new_spell_history_cell(spell_id));
      spellRow.appendChild(spellhistorywrap);
      
      spellRow.style.width = this.WIDTH;
      spellhistorywrap.addEventListener("click", spell_row_click);

      this.SPELLS_MAIN.appendChild(spellRow);
    }
  }

  new_character() {

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
    this.CASTS_SECTION.querySelectorAll("spell-name").forEach(element => {
      element.addEventListener("mouseleave", () => AURA_CONTROLS.style.display = "none");
      element.addEventListener('mouseover', () => {
        element.appendChild(AURA_CONTROLS);
        AURA_CONTROLS.style.removeProperty("display");
      });
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
    const input = document.createElement("input");
    input.id = `char-${this.TAB_N}-tab`;
    input.type = "radio";
    input.name = "char-tab";
    input.addEventListener("change", () => {
      this.CASTS_SECTION.style.display = input.checked ? "" : "none";
      this.hide_other();
    });
    input.checked = true;

    const label = document.createElement("label");
    label.classList.add("char-tab");
    label.classList.add("char-tab");
    label.classList.add(`char-${this.TAB_N}`);
    label.htmlFor = input.id;

    const report_link_wrap = document.createElement("span");
    report_link_wrap.className = "char-report-id";
    const report_link = document.createElement("a");
    report_link.target = "_blank";
    report_link.href = `/reports/${this.REPORT_ID}`;
    report_link.textContent = this.REPORT_ID;
    report_link_wrap.appendChild(report_link)

    const armory_link = document.createElement("a");
    armory_link.className = "warmane-armory-link";
    armory_link.target = "_blank";
    const SERVER = this.REPORT_ID.split("--")[3];
    armory_link.href = `http://armory.warmane.com/character/${this.NAME}/${SERVER}`;
    armory_link.textContent = "Armory⇗";

    const close = document.createElement("button");
    close.className = "button-close";
    close.textContent = "X";
    close.addEventListener("click", () => {
      CASTS_SECTION_WRAP.removeChild(this.CASTS_SECTION);
      console.log('removed', this.CASTS_SECTION)
      
      TABS_WRAP.removeChild(this.TAB_INPUT);
      console.log('removed', this.TAB_INPUT)
      
      TABS_WRAP.removeChild(this.TAB_LABEL);
      console.log('removed', this.TAB_LABEL)
      
      for (let child of Array.from(SECTION_FAV.children)) {
        if (child.getAttribute("data-tab-n") == this.TAB_N) {
          console.log('removed', child)
          SECTION_FAV.removeChild(child);
        }
      }
      CHARACTERS[this.TAB_N] = undefined;
    });

    const tab_nav = document.createElement("div");
    tab_nav.appendChild(report_link_wrap);
    tab_nav.appendChild(armory_link);
    tab_nav.appendChild(close);
    label.appendChild(tab_nav);
    label.append(this.NAME);

    this.TAB_INPUT = input;
    this.TAB_LABEL = label;

    // TABS_WRAP.insertBefore(tab_nav, BUTTON_ADD_CHARACTER);
    TABS_WRAP.insertBefore(input, BUTTON_ADD_CHARACTER);
    TABS_WRAP.insertBefore(label, BUTTON_ADD_CHARACTER);
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
function get_spell_row_css_query(event, add_to) {
  const spell_row = event.target.closest("spell-row");
  const spell_id = spell_row.getAttribute("data-spell-id");
  const css_query = `[data-spell-id="${spell_id}"]`;
  SPELLS_FAV.delete(spell_id);
  SPELLS_HIDE.delete(spell_id);
  if (add_to == "fav") {
    SPELLS_FAV.add(spell_id);
  } else if (add_to == "hide") {
    SPELLS_HIDE.add(spell_id);
  }
  save_spells_local_storage();
  return css_query;
}
BUTTON_HIDE.addEventListener("click", event => {
  if (event.target.closest("spells-main")) {
    const css_query = get_spell_row_css_query(event, "hide");
    for (let character of CHARACTERS) {
      const row = character.CASTS_SECTION.querySelector(css_query);
      section_append(character.SPELLS_HIDE, row);
    }
  } else if (!event.target.closest("spells-hide")) {
    const css_query = get_spell_row_css_query(event);
    for (let row of document.querySelectorAll(css_query)) {
      const tab_n = row.getAttribute("data-tab-n");
      section_append(CHARACTERS[tab_n].SPELLS_MAIN, row);
    }
  }
});
BUTTON_UNHIDE.addEventListener("click", event => {
  const css_query = get_spell_row_css_query(event);
  for (let character of CHARACTERS) {
    const row = character.CASTS_SECTION.querySelector(css_query);
    section_append(character.SPELLS_MAIN, row);
  }
});
BUTTON_FAV.addEventListener("click", event => {
  const css_query = get_spell_row_css_query(event, "fav");
  for (let character of CHARACTERS) {
    const row = character.CASTS_SECTION.querySelector(css_query);
    section_append(SECTION_FAV, row);
  }
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
      if (parsed_json[player_name] == Character.PLAYER_CLASS) {
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
  CASTS_SECTION_WRAP.style.display = "";
});
BUTTON_CANCEL.addEventListener("click", () => DIALOG_CHARACTER_SELECTION.close());

const current_query = new URLSearchParams(window.location.search);
const boss = current_query.get("boss");
if (boss) {
  TABS_WRAP.style.display = "";
  BOSS_REMINDER.style.display = "none";
  const _pathname = decodeURI(window.location.pathname).split('/');
  new Character(_pathname[2], _pathname[4]);
} else {
  BOSS_REMINDER.style.display = "";
}
SELECT_BEFORE_PULL.addEventListener("change", () => {
  CONFIG.max_duration = 0;
  CONFIG.shift = parseInt(SELECT_BEFORE_PULL.value);
  HTML_MAIN.appendChild(FIGHT_START);
  HTML_MAIN.appendChild(BUTTON_ADD_CHARACTER);
  TIMELINE_RULER.innerHTML = "";
  TABS_WRAP.innerHTML = "";
  TABS_WRAP.appendChild(BUTTON_ADD_CHARACTER);
  CASTS_SECTION_WRAP.querySelectorAll(".casts-section").forEach(e => CASTS_SECTION_WRAP.removeChild(e));
  SECTION_FAV.querySelectorAll(".spell-row").forEach(e => SECTION_FAV.removeChild(e));
  for (const char of CHARACTERS) {
    char.init();
  }
})