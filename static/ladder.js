const SPECS = [
  ["Death Knight", "class_deathknight", "death-knight"],
  ["Blood", "spell_deathknight_bloodpresence", "death-knight"],
  ["Frost", "spell_deathknight_frostpresence", "death-knight"],
  ["Unholy", "spell_deathknight_unholypresence", "death-knight"],
  ["Druid", "class_druid", "druid"],
  ["Balance", "spell_nature_starfall", "druid"],
  ["Feral Combat", "ability_racial_bearform", "druid"],
  ["Restoration", "spell_nature_healingtouch", "druid"],
  ["Hunter", "class_hunter", "hunter"],
  ["Beast Mastery", "ability_hunter_beasttaming", "hunter"],
  ["Marksmanship", "ability_marksmanship", "hunter"],
  ["Survival", "ability_hunter_swiftstrike", "hunter"],
  ["Mage", "class_mage", "mage"],
  ["Arcane", "spell_holy_magicalsentry", "mage"],
  ["Fire", "spell_fire_firebolt02", "mage"],
  ["Frost", "spell_frost_frostbolt02", "mage"],
  ["Paladin", "class_paladin", "paladin"],
  ["Holy", "spell_holy_holybolt", "paladin"],
  ["Protection", "spell_holy_devotionaura", "paladin"],
  ["Retribution", "spell_holy_auraoflight", "paladin"],
  ["Priest", "class_priest", "priest"],
  ["Discipline", "spell_holy_wordfortitude", "priest"],
  ["Holy", "spell_holy_guardianspirit", "priest"],
  ["Shadow", "spell_shadow_shadowwordpain", "priest"],
  ["Rogue", "class_rogue", "rogue"],
  ["Assassination", "ability_rogue_eviscerate", "rogue"],
  ["Combat", "ability_backstab", "rogue"],
  ["Subtlety", "ability_stealth", "rogue"],
  ["Shaman", "class_shaman", "shaman"],
  ["Elemental", "spell_nature_lightning", "shaman"],
  ["Enhancement", "spell_nature_lightningshield", "shaman"],
  ["Restoration", "spell_nature_magicimmunity", "shaman"],
  ["Warlock", "class_warlock", "warlock"],
  ["Affliction", "spell_shadow_deathcoil", "warlock"],
  ["Demonology", "spell_shadow_metamorphosis", "warlock"],
  ["Destruction", "spell_shadow_rainoffire", "warlock"],
  ["Warrior", "class_warrior", "warrior"],
  ["Arms", "ability_rogue_eviscerate", "warrior"],
  ["Fury", "ability_warrior_innerrage", "warrior"],
  ["Protection", "ability_warrior_defensivestance", "warrior"]
]
const MAIN_TABLE_WRAP = document.getElementById("main-table-wrap");
const MAIN_TABLE_BODY = document.getElementById("main-table-body");
const MAIN_TABLE_FOOT = document.getElementById("main-table-foot");
const PLAYERS_TABLE_WRAP = document.getElementById("players-table-wrap");
const PLAYERS_TABLE = document.getElementById("players-table-table");

const SELECT_SERVER = document.getElementById("select-server");
const SELECT_SIZE = document.getElementById("select-size");
const SELECT_MODE = document.getElementById("select-mode");
const SELECT_TIMEOUT = document.getElementById("select-timeout");
const SELECT_FACTION = document.getElementById("select-faction");
const CHECKBOX_SHOW_DONE = document.getElementById("show-done");
const CHECKBOX_SHOW_LIVE = document.getElementById("show-live");
const CHECKBOX_PLAYERS = document.getElementById("show-players");

const CONFIG = {
  timeout: 30000,
}

const MOD_TIMES = {};
const FRAGMENTS = {};

function toogle_display(element, show) {
  show ? element.style.removeProperty("display") : element.style.display = "none";
}
function toogle_display_checkbox(element, cbox) {
  toogle_display(element, cbox.checked);
}

const dummy = () => true;
const has_attr = (attr_name, value) => tr => tr.getAttribute(attr_name) == value;
const has_attr_wrap = (attr_name, value) => value == "all" ? dummy : has_attr(attr_name, value);
function show_row_wrap() {
  const faction = has_attr_wrap("data-faction", SELECT_FACTION.value);
  const mode = has_attr_wrap("data-mode", SELECT_MODE.value);
  const size = has_attr_wrap("data-size", SELECT_SIZE.value);
  const server = has_attr_wrap("data-server", SELECT_SERVER.value);
  return tr => faction(tr) && mode(tr) && size(tr) && server(tr);
}
function filter_table() {
  const show_row = show_row_wrap();
  MAIN_TABLE_BODY.querySelectorAll("tr").forEach(tr => {
    toogle_display(tr, show_row(tr))
  });
  checkbox_show_done_changed();
}
function checkbox_show_done_changed() {
  if (!CHECKBOX_SHOW_DONE.checked) return;

  const show_row = show_row_wrap();
  MAIN_TABLE_FOOT.querySelectorAll("tr").forEach(tr => {
    toogle_display(tr, show_row(tr))
  });
}
function time_to_text(t) {
  const minutes = `${Math.floor(t/60)}`.padStart(2, '0');
  const seconds = `${Math.floor(t%60)}`.padStart(2, '0');
  return `${minutes}:${seconds}`
}

function add_stopwatch_cell(row, d) {
  const td = document.createElement("td");
  td.classList.add("cell-time");
  MOD_TIMES[row.id] = d;
  row.appendChild(td);
}
function add_cell(row, value, type, inner) {
  const td = document.createElement("td");
  td.classList.add(`cell-${type}`);
  if (inner) {
    td.appendChild(inner);
  }
  td.append(value);
  row.appendChild(td);
}

function get_guild_index(dataset, guild_names) {
  let majority;
  const counts = {};
  const half = dataset.length / 2 + .1;
  const third = dataset.length / 3 + .1;
  const no_guild_index = guild_names.indexOf("");
  for (const value of dataset) {
    if (value == no_guild_index) continue;
    counts[value] = (counts[value] || 0) + 1;
    if (counts[value] > half) return guild_names[value];
    if (counts[value] > third) majority = value;
  }
  return majority == undefined ? "Pug" : `Pug (${guild_names[majority]})`;
}

function to_title(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function link(name, server, is_guild) {
  const type = is_guild ? "guild" : "character";
  const a = document.createElement("a");
  a.target = "_blank";
  a.href = `https://armory.warmane.com/${type}/${name}/${server}`;
  a.append(name);
  return a;
}

function players_span(data, server) {
  server = to_title(server);
  const players = data["pn"];
  const guilds = data["g"];
  const pguilds = data["pg"];
  const pspecs = data["ps"];
  const mtime = (new Date(data["mtime"] * 1000)).valueOf();
  const body = document.createElement("tbody");

  for (const i in players) {
    const row = document.createElement("tr");
    const [spec, spec_icon, spec2] = SPECS[pspecs[i]]
    
    const td_name = document.createElement("td");
    td_name.classList.add("cell-name");
    const _img = document.createElement("img");
    _img.src = `/static/icons/${spec_icon}.jpg`;
    _img.alt = spec;
    td_name.appendChild(_img);
    const player_link = link(players[i], server);
    player_link.classList.add(spec2);
    td_name.appendChild(player_link);
  
    const td_guild = document.createElement("td");
    td_guild.classList.add("cell-guild");
    td_guild.appendChild(link(guilds[pguilds[i]], server, true));

    row.appendChild(td_name);
    row.appendChild(td_guild);
    body.appendChild(row);
  }
  
  const time_row = document.createElement("tr");
  time_row.setAttribute("data-start", mtime);
  const td_name = document.createElement("td");
  td_name.append("Started");
  time_row.appendChild(td_name);
  time_row.appendChild(document.createElement("td"));
  body.appendChild(time_row);
  
  return body;
}

function auto_hide(row) {
  delete MOD_TIMES[row.id];
  setTimeout(() => {
    MAIN_TABLE_FOOT.appendChild(row);
  }, CONFIG.timeout);
}

function add_row(data) {
  const _id = data["id"];
  const time = data["t"];
  const _type = data["parent"];
  const attempts = _type == "kill" ? data["w"] + 1 : data["w"];
  
  const prev_row = document.getElementById(_id);

  if (prev_row) {
    if (prev_row.classList.contains(_type)) return;
    
    auto_hide(prev_row);

    prev_row.className = _type;

    prev_row.querySelector(".cell-time").textContent = time_to_text(time);
    prev_row.querySelector(".cell-attempts").textContent = attempts;

    return;
  }

  const row = document.createElement("tr");
  row.classList.add(_type);
  row.id = _id;

  add_cell(row, _id, "id");
  
  const server = data["server"].toLowerCase();
  const img_server = document.createElement("img");
  img_server.src = `/static/${server}.png`;
  add_cell(row, img_server, "server");
  row.setAttribute("data-server", server);

  if (time == 0 && _type == "live") {
    const mtime = new Date(data["mtime"] * 1000);
    add_stopwatch_cell(row, mtime);
  } else {
    add_cell(row, time_to_text(time), "time");
    auto_hide(row);
  }

  add_cell(row, attempts, "attempts");
  
  const boss_name = data["b"] != "" ? data["b"] : "Sister Svalna";
  add_cell(row, boss_name, "boss");
  
  add_cell(row, data["s"], "size");
  row.setAttribute("data-size", data["s"]);
  
  const mode = data["m"] == 1 ? "Heroic" : "Normal"
  add_cell(row, mode, "mode");
  row.setAttribute("data-mode", mode);

  const faction = data["pf"][0] == 1 ? "horde" : "alliance"
  const img = document.createElement("img");
  img.src = `/static/${faction}.png`;
  const guild = get_guild_index(data["pg"], data["g"]);
  add_cell(row, guild, "guild", img)
  row.setAttribute("data-faction", faction);

  const show_row = show_row_wrap();
  toogle_display(row, show_row(row))
  if (prev_row) {
    MAIN_TABLE_BODY.replaceChild(row, prev_row);
  } else {
    MAIN_TABLE_BODY.appendChild(row);
  }

  FRAGMENTS[_id] = players_span(data, server);

  row.addEventListener("mouseenter", () => {
    PLAYERS_TABLE.replaceChild(FRAGMENTS[row.id], PLAYERS_TABLE.firstElementChild);
    set_finish_time();
  });
}

function set_finish_time() {
  const tr = PLAYERS_TABLE.querySelector("tbody").lastElementChild;
  if (!tr) return;
  const diff = Date.now() - tr.getAttribute("data-start");
  const t = Math.floor(diff / 1000 / 60);
  tr.lastElementChild.textContent = `${t} minutes ago`;
}

function onmsg(event) {
  const data = JSON.parse(event.data);
  if (!Array.isArray(data)) {
    add_row(data);
    return
  }
  for (const _data of data) {
    add_row(_data);
  }
}


function init() {
  CHECKBOX_SHOW_DONE.addEventListener("change", () => {
    toogle_display_checkbox(MAIN_TABLE_FOOT, CHECKBOX_SHOW_DONE);
    checkbox_show_done_changed();
  });
  CHECKBOX_SHOW_LIVE.addEventListener("change", () => {
    toogle_display_checkbox(MAIN_TABLE_BODY, CHECKBOX_SHOW_LIVE);
  });
  CHECKBOX_PLAYERS.addEventListener("change", () => {
    toogle_display_checkbox(PLAYERS_TABLE_WRAP, CHECKBOX_PLAYERS);
  });
  SELECT_TIMEOUT.addEventListener("change", () => {
    CONFIG.timeout = SELECT_TIMEOUT.value * 1000;
    console.log(CONFIG.timeout);
  });
  
  for (const select of [SELECT_SERVER, SELECT_SIZE, SELECT_MODE, SELECT_FACTION]) {
    select.addEventListener("change", filter_table);
  }
  
  setInterval(() => {
    const now = Date.now();
    for (const _id in MOD_TIMES) {
      const td = document.getElementById(_id).querySelector(".cell-time");
      const diff = now - MOD_TIMES[_id]
      const v = Math.max(diff/1000, 0);
      td.textContent = time_to_text(v);
    }
  }, 1000);
  
  setInterval(() => {
    set_finish_time();
  }, 10000);
  
  // const ws_host = `wss://${window.location.hostname}:8765`
  const ws_host = `ws://${window.location.hostname}:8765`
  const socket = new WebSocket(ws_host);
  socket.onmessage = event => {
    CONFIG.timeout = 0;
    onmsg(event);
    setTimeout(() => {
      MAIN_TABLE_WRAP.style.removeProperty("display");
    });
    
    CONFIG.timeout = (SELECT_TIMEOUT.value ?? 30) * 1000;
    toogle_display_checkbox(PLAYERS_TABLE_WRAP, CHECKBOX_PLAYERS);
    toogle_display_checkbox(MAIN_TABLE_FOOT, CHECKBOX_SHOW_DONE);
    toogle_display_checkbox(MAIN_TABLE_BODY, CHECKBOX_SHOW_LIVE);
    socket.onmessage = onmsg;
  };
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
