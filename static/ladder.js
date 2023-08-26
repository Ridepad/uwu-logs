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

const ws_host = `ws://${window.location.hostname}:8765`
console.log(ws_host);
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

// function time_to_text(t) {
//   let miliseconds = t % 10;
//   let seconds = Math.floor(t / 10);
//   const minutes = `${Math.floor(seconds/60)}`.padStart(2, '0');
//   seconds = `${seconds%60}`.padStart(2, '0');
//   return `${minutes}:${seconds}.${miliseconds}`
// }

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
    const start = Math.floor((Date.now() - mtime) / 1000);
    console.log(mtime, start);
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


// Listen for messages
socket.addEventListener("message", event => {
  const data = JSON.parse(event.data);
  console.log(data);
  if (!Array.isArray(data)) {
    add_row(data);
    return
  }
  for (const _data of data) {
    add_row(_data);
  }
});


function init() {
  const t1 =  {
    "parent": "wipe",
    "id": "4477211",
    "server": "Lordaeron",
    "b": "Blood Prince Council",
    "s": 25,
    "m": 1,
    "t": 186,
    "w": 1,
    "a": [],
    "g": ["BURST DRAGON", "M E N T A L L Y"],
    "pn": ["Hanzels", "Bluedog", "Shalmah", "Indraz", "Azretul", "Isowar", "Boluda", "Andolokazo", "Kennypat", "Azuredragon", "Sandroo", "Santarroza", "Keroppi", "Preyade", "Gustafox", "Clintonn", "Lexicus", "Vegel", "Akaya", "Whitejean", "Jhoselyn", "Nenytaa", "Nelielle", "Josephcum", "Poplolito"],
    "pg": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "pf": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "pr": [4, 4, 5, 4, 1, 4, 4, 4, 4, 5, 5, 4, 4, 1, 3, 5, 2, 1, 5, 5, 1, 1, 1, 4, 3],
    "pc": [8, 0, 1, 9, 4, 9, 3, 6, 4, 2, 1, 4, 4, 3, 3, 1, 2, 7, 0, 5, 9, 3, 7, 5, 3],
    "ps": [34, 3, 6, 38, 18, 38, 14, 26, 17, 10, 5, 19, 17, 14, 14, 5, 10, 31, 1, 21, 38, 14, 31, 23, 14]
  };
  add_row(t1);

  const t2 = {
    "parent": "wipe",
    "id": "4477281",
    "server": "Lordaeron",
    "b": "Deathbringer Saurfang",
    "s": 10,
    "m": 1,
    "t": 1,
    "w": 2,
    "a": [],
    "g": [
      "",
      "Circulo de Titanes",
      "LAtinoSEXaltados",
      "Poor Decisions",
      "WetDreams",
      "this not kirchoff"
    ],
    "pn": [
      "Tedioso",
      "Elgeimanco",
      "Ahrimanx",
      "Jhonnyg",
      "Plagahot",
      "Elpolinomio",
      "Coronelbrant",
      "Vascotron",
      "Arwenx",
      "Ccofi"
    ],
    "pg": [2, 3, 2, 2, 2, 5, 2, 0, 4, 1],
    "pf": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "pr": [7, 8, 0, 0, 0, 9, 0, 8, 0, 0],
    "pc": [1, 2, 6, 4, 4, 5, 0, 7, 3, 0],
    "ps": [5, 10, 26, 17, 18, 23, 1, 31, 14, 2],
  };
  add_row(t2);

  const t3 = {
    "parent": "wipe",
    "server": "Lordaeron",
    "id": "4477468",
    "mtime": 1693031582.790271,
    "b": "The Lich King",
    "s": 10,
    "m": 0,
    "t": 1,
    "w": 7,
    "a": [],
    "g": [
      "Butterfly Effect"
    ],
    "pn": [
      "Balrogmq",
      "Baqi",
      "Buidekuai",
      "Danbshaman",
      "Fvzsq",
      "Guangedaf",
      "Guguda",
      "Lddldd",
      "Pantyhose",
      "Wan"
    ],
    "pg": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "pf": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "pr": [9, 7, 8, 8, 0, 0, 0, 7, 6, 6],
    "pc": [5, 7, 3, 2, 4, 4, 4, 1, 9, 0],
    "ps": [21, 31, 14, 10, 18, 19, 17, 5, 38, 1],
  };
  add_row(t3);

  const t4 = {
    "parent": "kill",
    "server": "Icecrown",
    "id": "15217285",
    "mtime": 1693032537.6815186,
    "b": "Flame Leviathan",
    "s": 10,
    "m": 0,
    "t": 119,
    "w": 1,
    "a": [],
    "g": [
      "",
      "P L A"
    ],
    "pn": ["Glodfs","Nairobe"],
    "pg": [1,0],
    "pf": [0,0],
    "pr": [4,3],
    "pc": [3,3],
    "ps": [14,14],
  }
  add_row(t4);

  const t5 = {
    "parent": "wipe",
    "server": "Icecrown",
    "id": "15217306",
    "mtime": 1693032757.8561149,
    "b": "Blood Prince Council",
    "s": 10,
    "m": 0,
    "t": 1,
    "w": 1,
    "a": [],
    "g": [
      "",
      "I N F I D E L S",
      "JAKOS TO BEDZIE",
      "SayNoToTryhard",
      "Unpossibles"
    ],
    "pn": [
      "Baankaai",
      "Bnator",
      "Brooks",
      "Curb",
      "Drsick",
      "Ebyr",
      "Galvayra",
      "Kahynn",
      "Palyz"
    ],
    "pg": [0, 3, 4, 1, 0, 0, 0, 0, 2],
    "pf": [1, 1, 1, 1, 1, 1, 1, 1, 1],
    "pr": [0, 8, 6, 0, 8, 0, 0, 8, 6],
    "pc": [0, 2, 6, 4, 3, 3, 4, 5, 7],
    "ps": [1, 10, 26, 19, 14, 14, 19, 23, 31],
  }
  add_row(t5);
}
// init()