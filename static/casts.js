const castsSectionWrap = document.getElementById("casts-section-wrap");
const timelineMultRange = document.getElementById("spell-timeline-mult");
const timelineMultLabel = document.getElementById("spell-timeline-mult-label");
const DEFAULT_COLORS = {
  "SWING_DAMAGE": "#DCDCDC",
  "SPELL_DAMAGE": "#3F3FCF",
  "SPELL_MISSED": "#5B5A99",
  "SPELL_PERIODIC_DAMAGE": "#783C9F",
  "SPELL_AURA_APPLIED": "#179900",
  "SPELL_AURA_APPLIED_DOSE": "#C0B300",
  "SPELL_AURA_REMOVED_DOSE": "#C0B300",
  "SPELL_AURA_REFRESH": "#C0B300",
  "SPELL_AURA_REMOVED": "#FF631A",
  "SPELL_CAST_SUCCESS": "#9200CC",
  "SPELL_PERIODIC_ENERGIZE": "#80ECFF",
}

const get_pad_value = e => e.getAttribute("data-pad");

function add_fake_applied(row, new_array) {
  if (new_array.length < 1) return;
  
  const spellHistory = row.querySelector(".spell-history");
  
  const firstEvent = new_array[0];
  if (firstEvent.classList[1] == "SPELL_AURA_REMOVED") {
    const div = document.createElement("div");
    div.setAttribute("data-time", "00:00.0");
    for (let x of ["data-source", "data-target", "data-etc"]) {
      div.setAttribute(x, firstEvent.getAttribute(x));
    }
    div.style.setProperty("--left", 0);
    div.style.width = get_pad_value(firstEvent) + "%";
    div.classList.add("cleu", "SPELL_AURA_APPLIED");
    spellHistory.insertBefore(div, spellHistory.firstChild);
  }
  
  const lastEvent = new_array.at(-1);
  if (lastEvent.classList[1] == "SPELL_AURA_APPLIED") {
    lastEvent.style.width = 100 - get_pad_value(lastEvent) + "%";
  }
}

function change_applied_width(new_array) {
  let start = null;
  for (let i=0; i<new_array.length; i++) {
    const div = new_array[i];
    const flag = div.classList[1];
    if (flag == "SPELL_AURA_APPLIED") {
      if (!start) start = div;
    } else if (start && flag == "SPELL_AURA_REMOVED") {
      start.style.width = get_pad_value(div) - get_pad_value(start) + "%";
      start = null;
    }
  }
}

function toggle_aura_duration(row) {
  const new_array = [];
  const spellHistory = row.querySelector(".spell-history");

  ["SPELL_AURA_APPLIED", "SPELL_AURA_REMOVED"].forEach(flag => {
    for (let div of row.getElementsByClassName(flag)) {
      new_array.push(div);
    }
  })

  new_array.sort((a, b) => get_pad_value(a) - get_pad_value(b));

  add_fake_applied(row, new_array);

  change_applied_width(new_array);
}

function toggle_aura_duration_wrap() {
  for (let row of document.getElementsByClassName("spell-row")) {
    toggle_aura_duration(row);
  }
}

function spell_count(row) {
  let c = 0;
  for (let cleu of row.getElementsByClassName("cleu")) {
    if (cleu.style.visibility != "hidden") c = c + 1;
  }
  return c
}

function sort_by_name(parent) {
  Array.from(parent.getElementsByClassName("spell-row"))
        .sort((a, b) => b.getAttribute("data-spell-name") < a.getAttribute("data-spell-name"))
        .forEach(row => parent.appendChild(row));
}

function toggle_rows(parent) {
  // sort_by_name(parent);

  // using array coz getElementsByClassName is dynamic
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
  to_sort
  .sort((a, b) => b.getAttribute("data-spell-name") < a.getAttribute("data-spell-name"))
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

function toggle_nodes(input) {
  const visibility = input.checked ? "visible" : "hidden";
  for (let div of document.getElementsByClassName(input.id)) {
    div.style.visibility = visibility; 
  }
}

function change_color(flag, color) {
  const style = document.createElement("style");
  style.append(`.${flag} {color: ${color}}`);
  document.head.appendChild(style);
}

const theTooltip = document.getElementById("the-tooltip");
const tooltipTime = document.getElementById("tooltip-time");
const tooltipFlag = document.getElementById("tooltip-flag");
const tooltipSource = document.getElementById("tooltip-source");
const tooltipTarget = document.getElementById("tooltip-target");
const tooltipData = document.getElementById("tooltip-data");

function init_flag_filter() {
  document.querySelectorAll("#flag-filter li").forEach(li => {
    const label = li.querySelector("label");
    const checkbox = li.querySelector(".flag-checkbox");
    const colorPicker = li.querySelector(".flag-color-picker");
    const color_ID = `${checkbox.id}_COLOR`;

    checkbox.checked = localStorage.getItem(checkbox.id) !== "false";
    colorPicker.value = localStorage.getItem(color_ID) ?? DEFAULT_COLORS[checkbox.id] ?? "#DCDCDC";
    label.style.setProperty('--secondary-color', colorPicker.value);
    change_color(checkbox.id, colorPicker.value);
    toggle_nodes(checkbox);
    
    checkbox.addEventListener("change", () => {
      toggle_nodes(checkbox);
      toggle_rows_wrap();
      localStorage.setItem(checkbox.id, checkbox.checked);
    });
    colorPicker.addEventListener("change", () => {
      localStorage.setItem(color_ID, colorPicker.value);
      label.style.setProperty('--secondary-color', colorPicker.value);
      change_color(checkbox.id, colorPicker.value);
    });
  })
}
function add_tooltip_info(cleu) {
  tooltipFlag.textContent = cleu.classList[1];
  tooltipTime.textContent = cleu.getAttribute("data-time");
  tooltipSource.textContent = cleu.getAttribute("data-source");
  tooltipTarget.textContent = cleu.getAttribute("data-target");
  tooltipData.textContent = cleu.getAttribute("data-etc");
}
function move_tooltip_to(cleu) {
  const bodyRect = document.body.getBoundingClientRect();
  const elemRect = cleu.getBoundingClientRect();
  const elemRect2 = cleu.parentElement.previousElementSibling.getBoundingClientRect();
  const _left = Math.max(elemRect.left, elemRect2.right);
  theTooltip.style.top = elemRect.bottom - bodyRect.top + 'px';
  theTooltip.style.right = bodyRect.right - _left + 'px';
}
function add_tooltip_events() {
  document.querySelectorAll(".cleu").forEach(cleu => {
    cleu.addEventListener("mouseleave", () => theTooltip.style.display = "none");
    cleu.addEventListener("mouseenter", () => {
      move_tooltip_to(cleu);
      add_tooltip_info(cleu);
      theTooltip.style.display = "";
    });
  });
}

function toggle_timeline_labels_big(lessthan) {
  const zoom = timelineMultRange.value;
  const visibility = zoom < lessthan ? "hidden" : "visible";
  const divs = document.getElementsByClassName("timeline-ruler-second");
  for (let i = 0; i < divs.length; i++) {
    if (i%5 == 0) continue;
    divs[i].firstElementChild.style.visibility = visibility;
  }
}

function toggle_timeline_labels(classname, lessthan) {
  const zoom = timelineMultRange.value;
  const visibility = zoom < lessthan ? "hidden" : "visible";
  for (let div of document.getElementsByClassName(classname)) {
    div.firstElementChild.style.visibility = visibility;
  }
}

function change_zoom() {
  console.time('zoom');
  const zoom = timelineMultRange.value;
  localStorage.setItem("ZOOM", zoom);
  timelineMultLabel.innerText = `${zoom}x`;
  castsSectionWrap.style.setProperty("--mult", zoom);
  console.timeEnd('zoom');
  console.time('toggle');
  const m = window.screen.width > 2000 ? 2 : 1;
  toggle_timeline_labels("timeline-ruler-tenth-second", 35 * m);
  toggle_timeline_labels("timeline-ruler-half-second", 10 * m);
  toggle_timeline_labels_big(6 * m);
  console.timeEnd('toggle');
}

function make_timeline() {
  console.time('make_timeline');

  const timelineWrap = castsSectionWrap.querySelector(".casts-table-timeline");
  const duration = timelineWrap.getAttribute("data-duration") * 10 - 1;
  const TICK_TYPES = {
    0: "timeline-ruler-second",
    5: "timeline-ruler-half-second"
  }

  const time_to_text = (sec, tenth) => {
    const minutes = Math.floor(sec/60);
    const seconds = `${sec%60}`.padStart(2, '0');
    return tenth ? `${minutes}:${seconds}.${tenth}` : `${minutes}:${seconds}`;
  }
  const create_timeline_tick = milliseconds => {
    const tick = document.createElement("div");
    const tenth_of_sec = milliseconds%10;
    const tick_type = TICK_TYPES[tenth_of_sec] ?? "timeline-ruler-tenth-second";
    tick.classList.add("timeline-ruler-tick", tick_type);
    const number = document.createElement("div");
    number.classList.add("timeline-ruler-number");
    const seconds = Math.floor(milliseconds/10);
    number.innerText = time_to_text(seconds, tenth_of_sec);
    tick.appendChild(number);
    return tick
  }
  
  // 25% performance improvement
  const fragment = new DocumentFragment();
  for (let milliseconds=0; milliseconds<=duration; milliseconds++) {
    fragment.appendChild(create_timeline_tick(milliseconds));
  }
  timelineWrap.append(fragment);

  console.timeEnd('make_timeline');
}

function add_control_events() {
  const castsSection = castsSectionWrap.querySelector(".casts-section");
  const sectionMain = castsSection.querySelector("spells-main");
  const auraControls = document.getElementById("aura-controls");
  const auraFav = document.getElementById("aura-fav");
  const auraDel = document.getElementById("aura-del");

  const _data = {
    fav: {},
    hide: {},
  }

  for (let z in _data) {
    const spells = localStorage.getItem(z) ? localStorage.getItem(z).split(",") : [];
    _data[z]["spells"] = Array.from(new Set(spells));
    _data[z]["element"] = castsSection.querySelector(`spells-${z}`);
  }

  for (let row of sectionMain.querySelectorAll("spell-row")) {
    const spell_id = row.getAttribute("data-spell-id");
    for (let z in _data) {
      if (_data[z]["spells"].includes(spell_id)) {
        _data[z]["element"].appendChild(row);
      }
    }
  }
  
  const array_remove = (array, item) => {
    let index = array.indexOf(item);
    while (index > -1) {
      array.splice(index, 1);
      index = array.indexOf(item);
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
  const spellsHide = _data["hide"]["spells"];
  const onevent = e => {
    const row = e.target.closest("spell-row");
    const spell_id = row.getAttribute("data-spell-id");
    array_remove(spellsFav, spell_id);
    array_remove(spellsHide, spell_id);
    
    const key = e.target == auraFav ? "fav" : "hide";
    const section = _data[key]["element"];
    if (row.parentElement != section) {
      const array = _data[key]["spells"];
      array.push(spell_id);
      insert_before(section, row);
    } else {
      insert_before(sectionMain, row);
    }

    localStorage.setItem("fav", spellsFav.toString());
    localStorage.setItem("hide", spellsHide.toString());
  }
  auraFav.addEventListener("click", onevent);
  auraDel.addEventListener("click", onevent);

  castsSection.querySelectorAll(".spell-name").forEach(e => {
    const div = e.querySelector("div");
    e.addEventListener('mouseover', () => {
      const section = e.closest("spell-row").parentElement;
      auraFav.textContent = section == _data["fav"]["element"] ? "▼" : "▲";
      auraDel.textContent = section == _data["hide"]["element"] ? "✚" : "✖";
      div.appendChild(auraControls);
      auraControls.style.display = "";
    });
    e.addEventListener("mouseleave", () => {
      auraControls.style.display = "none";
    });
  });

  const spellToggleHidden = document.getElementById("spell-toggle-hidden");
  spellToggleHidden.checked = localStorage.getItem("show-hidden") === "true";
  const onchange = () => {
    for (let spellsHide of castsSectionWrap.querySelectorAll("spells-hide")) {
      spellsHide.style.display = spellToggleHidden.checked ? "" : "none";
      localStorage.setItem("show-hidden", spellToggleHidden.checked);
    }
  }
  onchange();
  spellToggleHidden.addEventListener("change", onchange);
}

function init() {
  make_timeline();
  timelineMultRange.value = localStorage.getItem("ZOOM") ?? "3";
  change_zoom();
  timelineMultRange.addEventListener("change", change_zoom);
  toggle_aura_duration_wrap();
  init_flag_filter();
  toggle_rows_wrap();
  add_tooltip_events();
  add_control_events();

  document.querySelector(".table-wrap").style.display = "";
}

window.addEventListener('DOMContentLoaded', () => setTimeout(init));
