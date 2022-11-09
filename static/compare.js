const selectClass = document.getElementById("select-class");
const selectSpell = document.getElementById("select-spell");
const compareTable = document.getElementById("compare-field-table");
const compareTableBody = document.getElementById("compare-field-table-tbody");
const POST_ENDPOINT = `${window.location.pathname}${window.location.search}`;

const SPELLS = {
  "Mage": {
    42833: "Fireball",
    42891: "Pyroblast",
    55362: "Living Bomb",
    55360: "Living Bomb (DoT)",
    12654: "Ignite",
    42859: "Scorch",
    42873: "Fire Blast",
    42926: "Flamestrike",
    42925: "Flamestrike (Rank 8)",
    42938: "Blizzard",
    42931: "Cone of Cold",
    47610: "Frostfire Bolt",

    42897: "Arcane Blast",
    42845: "Arcane Missiles",
    42921: "Arcane Explosion",

    42842: "Frostbolt",
    71757: "Deep Freeze",
  },
  "Warrior": {
    47520: "Cleave",
    23881: "Bloodthirst",
    12721: "Deep Wounds",
    47450: "Heroic Strike",
    1680: "Whirlwind",
    44949: "Whirlwind",
    50783: "Slam",
  },
  "Priest": {
    58381: "Mind Flay",
    53022: "Mind Sear",
    48160: "Vampiric Touch",
    48300: "Devouring Plague",
    48125: "Shadow Word: Pain",
    63675: "Improved Devouring Plague",
    48127: "Mind Blast",
    48158: "Shadow Word: Death",
  },
  "Hunter": {
    75: "Auto Shot",
    53209: "Chimera Shot",
    53352: "Explosive Shot",
    49045: "Arcane Shot",
    49052: "Steady Shot",
    63468: "Piercing Shots",
    61006: "Kill Shot",
    49050: "Aimed Shot",
    53353: "Chimera Shot - Serpent",
    49001: "Serpent Sting",
    49048: "Multi-Shot",
    58433: "Volley",
    49065: "Explosive Trap Effect",
  },
  "Paladin": {
    53385: "Divine Storm",
    53739: "Seal of Corruption",
    53733: "Judgement of Corruption",
    61840: "Righteous Vengeance",
    20424: "Seal of Command",
    35395: "Crusader Strike",
    48819: "Consecration",
    53742: "Blood Corruption",
    69403: "Seal of Command",
    20467: "Judgement of Command",
    71433: "Manifest Anger",
    48801: "Exorcism",
  },
  "Druid": {
    48465: "Starfire",
    48461: "Wrath",
    53195: "Starfall",
    53190: "Starfall (AoE)",
    48466: "Hurricane",
    48463: "Moonfire",
    48468: "Insect Swarm",
    53227: "Typhoon",
    71023: "Languish",

    62078: "Swipe (Cat)",
    48572: "Shred",
    49800: "Rip",
    48574: "Rake",
    48577: "Ferocious Bite",
    48566: "Mangle (Cat)",

  },
  "Rogue": {
    48638: "Sinister Strike",
    22482: "Blade Flurry",
    51723: "Fan of Knives",
    48672: "Rupture",
    57841: "Killing Spree",
    57965: "Instant Poison IX",
    57970: "Deadly Poison IX",

    57993: "Envenom",
    48665: "Mutilate",
    48664: "Mutilate",
  },
  "Warlock": {
    47825: "Soul Fire",
    47834: "Seed of Corruption",
    47809: "Shadow Bolt",
    47811: "Immolate",
    50590: "Immolation",
    47813: "Corruption",
    47838: "Incinerate",
    47867: "Curse of Doom",
    61290: "Shadowflame",
    47818: "Rain of Fire",

    47855: "Drain Soul",
    47843: "Unstable Affliction",
    47864: "Curse of Agony",
    59164: "Haunt",

    17962: "Conflagrate",
    59172: "Chaos Bolt",
    47847: "Shadowfury",
  }
}
const CLASSES_TO_LOW = {
  "Death Knight": "death-knight",
  "Druid": "druid",
  "Hunter": "hunter",
  "Mage": "mage",
  "Paladin": "paladin",
  "Priest": "priest",
  "Rogue": "rogue",
  "Shaman": "shaman",
  "Warlock": "warlock",
  "Warrior": "warrior"
}

const CACHE_COMP = {}

function newTableCell(value, class_name) {
  const td = document.createElement("td");
  td.className = class_name;
  td.innerText = value || "";
  return td;
}

function player_name_cell(player_name) {
  const name_cell = newTableCell("", "player-cell");
  const pathname = window.location.pathname.replace("compare", `player/${player_name}`);
  
  const a = document.createElement("a");
  a.className = CLASSES_TO_LOW[selectClass.value];
  a.href = `${pathname}/${window.location.search}`;
  a.target = "_blank";
  a.innerText = player_name;
  name_cell.appendChild(a);

  return name_cell;
}

function addDamageCells(hits, row) {
  if (hits === undefined) {
    for (let i = 0; i < 12; i++)
      row.appendChild(newTableCell("", "count"));
    return;
  }
  
  for (let q = 0; q < 2; q++) {
    let ttl = 0;
    const [hits2, perc] = hits[q];
    for (let i = 0; i < 2; i++) {
      const [_count, _avg] = hits2[i];
      ttl = ttl + Number(_count.replace(/ /g, ""));
      row.appendChild(newTableCell(_count, "count"));
      row.appendChild(newTableCell(_avg[0], "count"));
    }
    row.appendChild(newTableCell(perc, "count"));
    row.appendChild(newTableCell(ttl, "count"));
  }
}

function addTableRow(data) {
  const row = document.createElement("tr");
  const spell_data = data["data"];
  const spell_id = selectSpell.value;

  row.appendChild(player_name_cell(data["name"]));
  row.appendChild(newTableCell(spell_data["ACTUAL"][spell_id], "total-cell"));
  row.appendChild(newTableCell(spell_data["REDUCED"][spell_id], "total-cell"));
  const hits = spell_data["HITS"][spell_id];
  addDamageCells(hits, row);

  compareTableBody.append(row);
}

const xhttp_compare = new XMLHttpRequest();
xhttp_compare.onreadystatechange = () => {
  if (xhttp_compare.status != 200 || xhttp_compare.readyState != 4) return;
  const parsed_json = JSON.parse(xhttp_compare.response);
  const spellCache = CACHE_COMP[selectClass.value];
  for (let i = 0; i<parsed_json.length; i++) {
    addTableRow(parsed_json[i]);
    spellCache.push(parsed_json[i]);
  }
}

function empty_table() {
  document.querySelectorAll("tbody tr").forEach(tr => {
    if (tr.firstChild.tagName == "TD")
      compareTableBody.removeChild(tr);
  })
}

function onSelectSpell() {
  empty_table();
  const data = CACHE_COMP[selectClass.value];
  for (let i=0; i<data.length; i++)
    addTableRow(data[i]);
}

function newOption(spellID, spellsName) {
  const option = document.createElement("option");
  option.value = spellID;
  option.innerHTML = spellsName;
  return option;
}

function onSelectClass() {
  const spells = SPELLS[selectClass.value]
  if (!spells) {
    compareTable.style.display = "none";
    return;
  }

  empty_table();
  compareTable.style.display = "";
  selectSpell.innerHTML = "";
  for (let spell_id in spells) {
    selectSpell.appendChild(newOption(spell_id, spells[spell_id]));
  }
  selectSpell.appendChild(newOption(1, "Melee"));

  if (CACHE_COMP[selectClass.value]) {
    onSelectSpell();
    return;
  }

  CACHE_COMP[selectClass.value] = [];

  xhttp_compare.open("POST", POST_ENDPOINT);
  xhttp_compare.send(JSON.stringify({"class": selectClass.value}));
}

function init() {
  const getCellValue = (tr, idx) => tr.children[idx].innerText.replace(/[% ]/g, "");
  const comparer = (idx) => (a, b) => getCellValue(b, idx) - getCellValue(a, idx);
  document.querySelectorAll("th").forEach(th => th.addEventListener("click", () => {
    const tbody = th.closest("tbody");
    Array.from(tbody.querySelectorAll("tr:nth-child(n+3)"))
         .sort(comparer(th.cellIndex))
         .forEach(tr => tbody.appendChild(tr));
  }));
  
  selectClass.addEventListener("change", onSelectClass);
  selectSpell.addEventListener("change", onSelectSpell);

  onSelectClass();
}


document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
