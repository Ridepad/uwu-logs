import {
  SPECS,
} from "./constants.js?v=240830-1";

const MAIN_TABLE_WRAP = document.getElementById("main-table-wrap");
const MAIN_TABLE_BODY = document.getElementById("main-table-body");
const MAIN_TABLE_FOOT = document.getElementById("main-table-foot");
const PLAYERS_TABLE_WRAP = document.getElementById("players-table-wrap");
const PLAYERS_TABLE = document.getElementById("players-table-table");
const PLAYERS_TABLE_LABEL = document.getElementById("players-table-label");
const PLAYERS_TABLE_TIME = document.getElementById("players-table-time");

const SELECT_SERVER = document.getElementById("select-server");
const SELECT_SIZE = document.getElementById("select-size");
const SELECT_MODE = document.getElementById("select-mode");
const SELECT_TIMEOUT = document.getElementById("select-timeout");
const SELECT_FACTION = document.getElementById("select-faction");
const CHECKBOX_SHOW_DONE = document.getElementById("show-done");
const CHECKBOX_SHOW_LIVE = document.getElementById("show-live");
const CHECKBOX_PLAYERS = document.getElementById("show-players");
const SPAN_STATUS = document.getElementById("span-status");

const KEYS = {
  type: "type",
  server: "server",
  timestamp: "timestamp",
  id: "id",
  fight_name: "b",
  size: "s",
  difficulty: "m",
  wipes: "w",
  duration: "t",
  player_names: "pn",
  guild_names: "g",
  player_guilds: "pg",
  player_specs: "ps",
  player_factions: "pf",
}

const CONFIG = {
  timeout: 0,
}
const WEBSOCKET = {
  websocket: null,
  reconnect_interval: 10 * 1000,
  reconnect_interval_id: 0,
}

const IN_PROGRESS = {};
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
    toogle_display(tr, show_row(tr));
  });
  checkbox_show_done_changed();
}
function checkbox_show_done_changed() {
  if (!CHECKBOX_SHOW_DONE.checked) return;

  const show_row = show_row_wrap();
  MAIN_TABLE_FOOT.querySelectorAll("tr").forEach(tr => {
    toogle_display(tr, show_row(tr));
  });
}
function time_to_text(t) {
  const minutes = `${Math.floor(t/60)}`.padStart(2, '0');
  const seconds = `${Math.floor(t%60)}`.padStart(2, '0');
  return `${minutes}:${seconds}`;
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

function get_guild_index(data) {
  const _guilds_list = data[KEYS.player_guilds];
  const _player_guilds = data[KEYS.guild_names];
  
  let majority;
  const counts = {};
  const half = _guilds_list.length / 2 + .1;
  const third = _guilds_list.length / 3 + .1;
  const no_guild_index = _player_guilds.indexOf("");
  for (const value of _guilds_list) {
    if (value == no_guild_index) continue;
    counts[value] = (counts[value] || 0) + 1;
    if (counts[value] > half) return _player_guilds[value];
    if (counts[value] > third) majority = value;
  }
  return majority == undefined ? "Pug" : `Pug (${_player_guilds[majority]})`;
}

function to_title(s) {
  s = s.toLowerCase();
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

function make_players_table(data) {
  const server = to_title(data[KEYS.server]);
  const players = data[KEYS.player_names];
  const guilds = data[KEYS.guild_names];
  const pguilds = data[KEYS.player_guilds];
  const pspecs = data[KEYS.player_specs];
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
  
  return body;
}

function auto_hide(row) {
  delete IN_PROGRESS[row.id];
  setTimeout(() => {
    MAIN_TABLE_FOOT.appendChild(row);
  }, CONFIG.timeout);
}
function row_on_enter(event) {
  const row = event.target;
  PLAYERS_TABLE_LABEL.textContent = row.classList.contains("live") ? "Started" : "Ended";
  
  const _started = row.getAttribute("data-timestamp");
  PLAYERS_TABLE.setAttribute("data-timestamp", _started);
  
  if (FRAGMENTS[row.id].tagName != "TBODY") {
    FRAGMENTS[row.id] = make_players_table(FRAGMENTS[row.id]);
  }
  const _tbody = PLAYERS_TABLE.querySelector("tbody");
  PLAYERS_TABLE.replaceChild(FRAGMENTS[row.id], _tbody);
  
  set_finish_time();
}
function add_row(data) {
  const _id = data[KEYS.id];
  const duration = data[KEYS.duration];
  const _type = data[KEYS.type];
  const _wipes = data[KEYS.wipes];
  const attempts = _type == "kill" ? _wipes + 1 : _wipes;
  
  const prev_row = document.getElementById(_id);

  if (prev_row) {
    if (prev_row.classList.contains(_type)) return;
    
    auto_hide(prev_row);

    prev_row.className = _type;

    prev_row.querySelector(".cell-time").textContent = time_to_text(duration);
    prev_row.querySelector(".cell-attempts").textContent = attempts;

    return;
  }

  const row = document.createElement("tr");
  row.classList.add(_type);
  row.id = _id;

  add_cell(row, _id, "id");
  
  const server = data[KEYS.server].toLowerCase();
  const img_server = document.createElement("img");
  img_server.src = `/static/${server}.png`;
  add_cell(row, img_server, "server");

  const timestamp = new Date(data[KEYS.timestamp] * 1000);
  let time_text = "";
  if (duration == 0 && _type == "live") {
    IN_PROGRESS[row.id] = timestamp;
  } else {
    time_text = time_to_text(duration);
    auto_hide(row);
  }
  add_cell(row, time_text, "time");

  add_cell(row, attempts, "attempts");
  
  const _fight_name = data[KEYS.fight_name];
  const fight_name = _fight_name != "" ? _fight_name : "Sister Svalna";
  add_cell(row, fight_name, "boss");
  
  add_cell(row, data[KEYS.size], "size");
  
  const mode = data[KEYS.difficulty] == 1 ? "Heroic" : "Normal";
  add_cell(row, mode, "mode");

  const faction = data[KEYS.player_factions][0] == 1 ? "horde" : "alliance";
  const img = document.createElement("img");
  img.src = `/static/${faction}.png`;
  const guild = get_guild_index(data);
  add_cell(row, guild, "guild", img);

  row.setAttribute("data-server", server);
  row.setAttribute("data-size", data[KEYS.size]);
  row.setAttribute("data-mode", mode);
  row.setAttribute("data-faction", faction);
  row.setAttribute("data-timestamp", timestamp.valueOf());

  const show_row = show_row_wrap();
  toogle_display(row, show_row(row));
  MAIN_TABLE_BODY.appendChild(row);

  FRAGMENTS[_id] = data;
  row.addEventListener("mouseenter", row_on_enter);
}

const plular = (v, n) => v == 0 ? "" : v == 1 ? `${v} ${n} ` : `${v} ${n}s `;
function set_finish_time() {
  const _started = PLAYERS_TABLE.getAttribute("data-timestamp");
  const diff = Date.now() - _started;
  const t = diff / 1000 + 60;
  const minutes = Math.floor(t / 60);
  const minutes_str = plular(minutes % 60, "minute");
  const hours = Math.floor(minutes / 60);
  const hours_str = plular(hours, "hour");
  PLAYERS_TABLE_TIME.textContent = `${hours_str}${minutes_str} ago`;
}

function socket_on_message(event) {
  const data = JSON.parse(event.data);
  if (!Array.isArray(data)) {
    add_row(data);
    return
  }
  for (const _data of data) {
    add_row(_data);
  }
}

function set_ongoing_time() {
  const now = Date.now();
  for (const _id in IN_PROGRESS) {
    const td = document.getElementById(_id).querySelector(".cell-time");
    const diff = now - IN_PROGRESS[_id];
    const v = Math.max(diff/1000, 0);
    td.textContent = time_to_text(v);
  }
}
function init_websocket() {
  if (WEBSOCKET.websocket != null) return;
  
  // const ws_host = `wss://${window.location.hostname}:8765`;
  // const ws_host = `ws://127.0.0.1:8765`;
  const socket = new WebSocket(ws_host);
  WEBSOCKET.websocket = socket;

  socket.onmessage = event => {
    socket.onmessage = socket_on_message;
    socket_on_message(event);
    setTimeout(() => {
      MAIN_TABLE_WRAP.style.removeProperty("display");
    });
    
    CONFIG.timeout = (SELECT_TIMEOUT.value ?? 30) * 1000;
    SPAN_STATUS.textContent = "Connected";
    SPAN_STATUS.className = "status-connected";
    console.log("WebSocket connected");
  };
  
  socket.onclose = () => {
    WEBSOCKET.websocket = null;
    SPAN_STATUS.textContent = "Disconnected";
    SPAN_STATUS.className = "status-disconnected";
  };
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
  });
  
  for (const select of [SELECT_SERVER, SELECT_SIZE, SELECT_MODE, SELECT_FACTION]) {
    select.addEventListener("change", filter_table);
  }
  
  init_websocket();
  setInterval(init_websocket, WEBSOCKET.reconnect_interval);
  setInterval(set_ongoing_time, 1000);
  setInterval(set_finish_time, 10000);
  
  toogle_display_checkbox(PLAYERS_TABLE_WRAP, CHECKBOX_PLAYERS);
  toogle_display_checkbox(MAIN_TABLE_FOOT, CHECKBOX_SHOW_DONE);
  toogle_display_checkbox(MAIN_TABLE_BODY, CHECKBOX_SHOW_LIVE);
}

document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
