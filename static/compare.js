const selectClass = document.getElementById("select-class")
const selectSpell = document.getElementById("select-spell")
const table = document.getElementById("compare-field-table")
const tbody_id = "compare-field-table-tbody"
const tbody = document.getElementById(tbody_id)
const URL = `${window.location.pathname}${window.location.search}`

const SPELLS = {
  "Mage": [
    "Fireball",
    "Pyroblast",
    "Living Bomb",
    "Living Bomb (DoT)",
    "Ignite",
    "Scorch",
    "Fire Blast",
    "Flamestrike",
  ],
  "Warrior": [
    "Cleave",
    "Whirlwind",
    "Deep Wounds",
    "Bloodthirst",
    "Melee",
    "Heroic Strike",
    "Whirlwind",
    "Slam",
  ]
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
  const td = document.createElement('td');
  td.className = class_name;
  td.innerText = value || "";
  return td;
}

function get_current_spell_id(spell_data) {
  const spell_names = spell_data.NAMES
  for (let spell_id in spell_names)
    if (spell_names[spell_id] == selectSpell.value)
      return spell_id
}

function player_name_cell(player_name) {
  const name_cell = newTableCell('', "player-cell")
  
  const a = document.createElement('a');
  a.innerText = player_name;
  const path = window.location.pathname.replace('compare', `player/${player_name}`);
  a.href = `${path}${window.location.search}`;
  a.className = CLASSES_TO_LOW[selectClass.value];
  name_cell.appendChild(a);

  return name_cell
}

function addTableRow(data) {
  const row = document.createElement('tr');

  row.appendChild(player_name_cell(data['name']));

  const spell_data = data['data'];

  const spell_id = get_current_spell_id(spell_data);

  row.appendChild(newTableCell(spell_data["ACTUAL"][spell_id], "total-cell"))
  row.appendChild(newTableCell(spell_data["REDUCED"][spell_id], "total-cell"))
  const hits = spell_data["HITS"][spell_id];
  if (hits === undefined) {
    for (let i=0;i<12;i++)
      row.appendChild(newTableCell("", "count"));
  } else {
    for (let q=0; q<2; q++) {
      let ttl = 0;
      const [hits2, perc] = hits[q];
      for (let i=0; i<2; i++) {
        const [_count, _avg] = hits2[i];
        ttl = ttl + Number(_count.replace(/ /g, ''));
        row.appendChild(newTableCell(_count, "count"));
        row.appendChild(newTableCell(_avg[0], "count"));
      }
      row.appendChild(newTableCell(perc, "count"));
      row.appendChild(newTableCell(ttl, "count"));
    }
  }

  tbody.append(row);
}

const xhttp_compare = new XMLHttpRequest();
xhttp_compare.onreadystatechange = () => {
  if (xhttp_compare.status != 200 || xhttp_compare.readyState != 4) return;
  const resp_split = xhttp_compare.response.split("\n");

  const a = CACHE_COMP[selectClass.value]
  for (let i = 0; i<resp_split.length;i++) {
    try {
      const split_json = JSON.parse(resp_split[i]);
      addTableRow(split_json);
      a.push(split_json);
    } catch (error) {
      console.error(error);
    }
  }
}

function empty_table() {
  // while (tbody.hasChildNodes()) tbody.removeChild(tbody.lastChild);
  document.querySelectorAll('tbody tr').forEach(tr => {
    if (tr.firstChild.tagName == "TD")
      tbody.removeChild(tr)
  })
}

function onSelectSpell() {
  empty_table();
  const data = CACHE_COMP[selectClass.value];
  for (let i=0; i<data.length; i++)
    addTableRow(data[i]);
}

function newOption(value) {
  const _option = document.createElement('option');
  _option.value = value;
  _option.innerHTML = value;
  return _option;
}

const compare_endpoint = `${window.location.pathname}${window.location.search}`
function onSelectClass() {
  const spells = SPELLS[selectClass.value]
  if (!spells) {
    table.style.display = "none";
    return;
  }

  empty_table();
  table.style.display = "table";
  selectSpell.innerHTML = "";
  spells.forEach(spellsName => selectSpell.appendChild(newOption(spellsName)));

  if (CACHE_COMP[selectClass.value]) {
    onSelectSpell();
  } else {
    CACHE_COMP[selectClass.value] = []
  
    xhttp_compare.open("POST", compare_endpoint);
    xhttp_compare.send(JSON.stringify({'class': selectClass.value}));
  }
}

const getCellValue = (tr, idx) => tr.children[idx].innerText.replace(/[% ]/g, '');
const comparer = (idx) => (a, b) => getCellValue(b, idx) - getCellValue(a, idx);
document.querySelectorAll('th').forEach(th => th.addEventListener('click', () => {
  const tbody = th.closest('tbody');
  Array.from(tbody.querySelectorAll('tr:nth-child(n+3)'))
       .sort(comparer(th.cellIndex))
       .forEach(tr => tbody.appendChild(tr));
}));

selectClass.addEventListener("change", onSelectClass)
selectSpell.addEventListener("change", onSelectSpell)
