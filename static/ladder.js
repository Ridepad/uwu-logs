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

const button = document.getElementById("sendshit");
const mainshitbody = document.getElementById("mainshit-body");
const mainshitfoot = document.getElementById("mainshit-foot");
const FIGHTS_PLAYERS_TABLE = document.getElementById("fights-players-table");

const ws_host = `wss://${window.location.hostname}:8765`
const socket = new WebSocket(ws_host);

const intervals = {};
const fragments = {};

function time_to_text(t) {
  const minutes = `${Math.floor(t/60)}`.padStart(2, '0');
  const seconds = `${t%60}`.padStart(2, '0');
  return `${minutes}:${seconds}`
}
function interval_wrap(e, start) {
  let v = start;
  e.textContent = time_to_text(start);
  const t = setInterval(() => {
    v = v + 1;
    e.textContent = time_to_text(v);
  }, 1000);
  return t;
}
function add_stopwatch_cell(row, start) {
  const td = document.createElement("td");
  td.classList.add(`cell-time`);
  intervals[row.id] = interval_wrap(td, start);
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

function players_span(players, guilds, pguilds, pspecs) {
  const body = document.createElement("tbody");
  players.sort();
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
  return body;
}

function auto_hide(row) {
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

    clearInterval(intervals[_id]);
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

  if (time == 0 && _type == "live") {
    const mtime = new Date(data["mtime"] * 1000);
    const diff = (Date.now() - mtime) / 1000
    const start = Math.max(Math.floor(diff), 0);
    add_stopwatch_cell(row, start);
  } else {
    clearInterval(intervals[row.id]);
    add_cell(row, time_to_text(time), "time");
    auto_hide(row);
  }

  add_cell(row, data["w"], "attempts");
  
  const boss_name = data["b"] != "" ? data["b"] : "Sister Svalna";
  add_cell(row, boss_name, "boss");
  
  add_cell(row, data["s"], "size");
  
  const mode = data["m"] == 1 ? "Heroic" : "Normal"
  add_cell(row, mode, "mode");

  const faction = data["pf"][0] == 1 ? "horde" : "alliance"
  const img = document.createElement("img");
  img.src = `/static/${faction}.png`;
  const guild = get_guild_index(data["pg"], data["g"]);
  add_cell(row, guild, "guild", img)

  if (prev_row) {
    mainshitbody.replaceChild(row, prev_row);
  } else {
    mainshitbody.appendChild(row);
  }

  fragments[_id] = players_span(data["pn"], data["g"], data["pg"], data["ps"]);

  row.addEventListener("mouseenter", () => {
    FIGHTS_PLAYERS_TABLE.replaceChild(fragments[row.id], FIGHTS_PLAYERS_TABLE.lastChild);
  });
}


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
