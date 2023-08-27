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

const CONFIG = {
  timeout: 30000,
}
// const ws_host = `wss://${window.location.hostname}:8765`
const ws_host = `wss://uwu-logs.xyz:8765`
const socket = new WebSocket(ws_host);

const fragments = {};
const mtimes = {};
const donetimes = {};

const mainshitbody = document.getElementById("mainshit-body");
const mainshitfoot = document.getElementById("mainshit-foot");
const fightsplayers = document.getElementById("fights-players");
const FIGHTS_PLAYERS_TABLE = document.getElementById("fights-players-table");

const select_server = document.getElementById("select-server");
const select_size = document.getElementById("select-size");
const select_mode = document.getElementById("select-mode");
const select_timeout = document.getElementById("select-timeout");
const select_faction = document.getElementById("select-faction");
const checkbox_show_done = document.getElementById("show-done");
const checkbox_show_live = document.getElementById("show-live");
const checkbox_players = document.getElementById("show-players");

const dummy = () => true;
const has_attr = (attr_name, value) => tr => tr.getAttribute(attr_name) == value;
const has_attr_wrap = (attr_name, value) => value == "all" ? dummy : has_attr(attr_name, value);
function show_row_wrap() {
  const faction = has_attr_wrap("data-faction", select_faction.value);
  const mode = has_attr_wrap("data-mode", select_mode.value);
  const size = has_attr_wrap("data-size", select_size.value);
  const server = has_attr_wrap("data-server", select_server.value);
  return tr => faction(tr) && mode(tr) && size(tr) && server(tr);
}
function filter_table() {
  const show_row = show_row_wrap();
  mainshitbody.querySelectorAll("tr").forEach(tr => {
    show_row(tr) ? tr.style.display = "" : tr.style.display = "none";
  });
  checkbox_show_done_changed();
}
function checkbox_show_done_changed() {
  if (!checkbox_show_done.checked) return;
  checkbox_show_done.querySelectorAll("tr").forEach(tr => {
    show_row(tr) ? tr.style.display = "" : tr.style.display = "none";
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
  mtimes[row.id] = d;
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

function players_span(data) {
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
    td_name.classList.add(spec2);
    const _img = document.createElement("img");
    _img.src = `/static/icons/${spec_icon}.jpg`;
    _img.alt = spec;
    td_name.appendChild(_img);
    td_name.append(players[i]);
  
    const td_guild = document.createElement("td");
    td_guild.append(guilds[pguilds[i]]);
    td_guild.classList.add("cell-guild");

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
  delete mtimes[row.id];
  setTimeout(() => {
    mainshitfoot.appendChild(row);
  }, CONFIG.timeout);
}

function add_row(data) {
  const _id = data["id"];
  const time = data["t"];
  const _type = data["parent"];

  const prev_row = document.getElementById(_id);

  if (prev_row) {
    if (prev_row.classList.contains(_type)) return;
    
    auto_hide(prev_row);

    prev_row.className = _type;

    prev_row.querySelector(".cell-time").textContent = time_to_text(time);
    const attempts = _type == "kill" ? data["w"] + 1 : data["w"];
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

  add_cell(row, data["w"], "attempts");
  
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

  show_row_wrap()(row) ? row.style.display = "" : row.style.display = "none";
  if (prev_row) {
    mainshitbody.replaceChild(row, prev_row);
  } else {
    mainshitbody.appendChild(row);
  }

  fragments[_id] = players_span(data);

  row.addEventListener("mouseenter", () => {
    FIGHTS_PLAYERS_TABLE.replaceChild(fragments[row.id], FIGHTS_PLAYERS_TABLE.firstElementChild);
    set_finish_time();
  });
}

function set_finish_time() {
  const tr = FIGHTS_PLAYERS_TABLE.querySelector("tbody").lastElementChild;
  if (!tr) return;
  const diff = Date.now() - tr.getAttribute("data-start");
  const t = Math.floor(diff / 1000 / 60);
  tr.lastElementChild.textContent = `${t} minutes ago`;
}


checkbox_show_done.addEventListener("change", () => {
  checkbox_show_done.checked ? mainshitfoot.style.display = "" : mainshitfoot.style.display = "none";
  checkbox_show_done_changed();
});
checkbox_show_live.addEventListener("change", () => {
  checkbox_show_live.checked ? mainshitbody.style.display = "" : mainshitbody.style.display = "none";
});
checkbox_players.addEventListener("change", () => {
  checkbox_players.checked ? fightsplayers.style.display = "" : fightsplayers.style.display = "none";
});
select_timeout.addEventListener("change", () => {
  CONFIG.timeout = select_timeout.value * 1000;
  console.log(CONFIG.timeout);
});

for (const select of [select_server, select_size, select_mode, select_faction, ]) {
  select.addEventListener("change", filter_table);
}

CONFIG.timeout = select_timeout.value * 1000;
checkbox_players.checked ? fightsplayers.style.display = "" : fightsplayers.style.display = "none";
checkbox_show_done.checked ? mainshitfoot.style.display = "" : mainshitfoot.style.display = "none";
checkbox_show_live.checked ? mainshitbody.style.display = "" : mainshitbody.style.display = "none";

setInterval(() => {
  const now = Date.now();
  for (const _id in mtimes) {
    const td = document.getElementById(_id).querySelector(".cell-time");
    const diff = now - mtimes[_id]
    const v = Math.max(diff/1000, 0);
    td.textContent = time_to_text(v);
  }
}, 1000);

setInterval(() => {
  set_finish_time();
}, 10000);

socket.addEventListener("message", event => {
  const data = JSON.parse(event.data);
  if (!Array.isArray(data)) {
    add_row(data);
    return
  }
  for (const _data of data) {
    add_row(_data);
  }
});
