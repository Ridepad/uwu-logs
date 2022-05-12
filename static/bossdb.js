const SEARCH_INPUT_OPTIONS = {
  "boss": {
    "the-lich-king": "The Lich King",
    "halion": "Halion",
    "deathbringer-saurfang": "Deathbringer Saurfang",
    "festergut": "Festergut",
    "rotface": "Rotface",
    "professor-putricide": "Professor Putricide",
    "blood-queen-lanathel": "Blood-Queen Lana'thel",
    "sindragosa": "Sindragosa",
    "lord-marrowgar": "Lord Marrowgar",
    "lady-deathwhisper": "Lady Deathwhisper",
    "gunship-battle": "Gunship Battle",
    "blood-prince-council": "Blood Prince Council",
    "valithria-dreamwalker": "Valithria Dreamwalker",
    "northrend-beasts": "Northrend Beasts",
    "lord-jaraxxus": "Lord Jaraxxus",
    "faction-champions": "Faction Champions",
    "twin-valkyr": "Twin Val'kyr",
    "anubarak": "Anub'arak",
    "onyxia": "Onyxia",
    "malygos": "Malygos",
    "sartharion": "Sartharion",
    "baltharus-the-warborn": "Baltharus the Warborn",
    "general-zarithrian": "General Zarithrian",
    "saviana-ragefire": "Saviana Ragefire",
    "archavon-the-stone-watcher": "Archavon the Stone Watcher",
    "emalon-the-storm-watcher": "Emalon the Storm Watcher",
    "koralon-the-flame-watcher": "Koralon the Flame Watcher",
    "toravon-the-ice-watcher": "Toravon the Ice Watcher",
    "anubrekhan": "Anub'Rekhan",
    "grand-widow-faerlina": "Grand Widow Faerlina",
    "maexxna": "Maexxna",
    "noth-the-plaguebringer": "Noth the Plaguebringer",
    "heigan-the-unclean": "Heigan the Unclean",
    "loatheb": "Loatheb",
    "patchwerk": "Patchwerk",
    "grobbulus": "Grobbulus",
    "gluth": "Gluth",
    "thaddius": "Thaddius",
    "instructor-razuvious": "Instructor Razuvious",
    "gothik-the-harvester": "Gothik the Harvester",
    "the-four-horsemen": "The Four Horsemen",
    "sapphiron": "Sapphiron",
    "kelthuzad": "Kel'Thuzad",
    "flame-leviathan": "Flame Leviathan",
    "ignis-the-furnace-master": "Ignis the Furnace Master",
    "razorscale": "Razorscale",
    "xt-002-deconstructor": "XT-002 Deconstructor",
    "assembly-of-iron": "Assembly of Iron",
    "kologarn": "Kologarn",
    "auriaya": "Auriaya",
    "hodir": "Hodir",
    "thorim": "Thorim",
    "freya": "Freya",
    "mimiron": "Mimiron",
    "general-vezax": "General Vezax",
    "yogg-saron": "Yogg-Saron",
    "algalon-the-observer": "Algalon the Observer"
  },
  "mode": {
    "0": "Normal",
    "1": "Heroic",
  },
  "size": {
    "10": "10",
    "25": "25",
  },
  "achievs": {
    "0": "No",
    "1": "Yes",
  },
  "isPug": {
    "0": "No",
    "1": "Yes",
  },
}

const SEARCH_TYPE_OPTIONS = {
  "boss": "Boss",
  "size": "Size",
  "mode": "Difficulty",
  "names": "Char Name",
  "guilds": "Guild Name",
  "isPug": "PuG Run",
  "spec": "Specs",
  "cls": "Class",
  "achievs": "Achievements",
  "dur": "Duration >",
  "wipes": "Wipes >",
}

const SEARCH_TYPE_OPTIONS_KEYS = Array.from(Object.keys(SEARCH_TYPE_OPTIONS));


const submitButton = document.getElementById("submitButton");
const addFilterButton = document.getElementById("addFilterButton");
const searchField = document.getElementById("db-search-field");

const deleteFilterButton = document.createElement('button');
deleteFilterButton.innerText = "X";
deleteFilterButton.setAttribute("type", "reset");

const filterType = document.createElement('select');
for (let option_value in SEARCH_TYPE_OPTIONS) {
  const _option = document.createElement('option');
  _option.setAttribute("value", option_value); 
  _option.innerText = SEARCH_TYPE_OPTIONS[option_value];
  filterType.appendChild(_option);
}

function newSelect(options) {
  const _select = document.createElement('select');
  for (let option_value in options) {
    const _option = document.createElement('option');
    _option.setAttribute("value", option_value);
    _option.innerText = options[option_value];
    _select.appendChild(_option);
  }
  return _select
}

function newTextInput() {
  const inputRight = document.createElement('input');
  inputRight.setAttribute("size", "10");
  inputRight.setAttribute("type", "text");
  inputRight.setAttribute("maxlength", "30");
  return inputRight
}

function changeSeachInput(select) {
  const options = SEARCH_INPUT_OPTIONS[select.value];
  
  const new_child = options ? newSelect(options) : newTextInput();
  new_child.setAttribute("class", "db-search-input");
  
  const article = select.closest('article');
  const n = article.querySelector(".db-search-input");
  n ? article.replaceChild(new_child, n) : article.appendChild(new_child);
}


function newFilterType(value_to_set) {
  const _select = filterType.cloneNode(true);
  _select.setAttribute("class", "db-search-category");
  _select.value = value_to_set;
  _select.addEventListener("change", () => changeSeachInput(_select));
  return _select
}

function newFilter(value_to_set) {
  const article = document.createElement('article');

  const _delbutton = deleteFilterButton.cloneNode(true);
  _delbutton.addEventListener("click", () => searchField.removeChild(article));
  article.appendChild(_delbutton);

  const select = newFilterType(value_to_set);
  article.appendChild(select);
  
  changeSeachInput(select);
  return article
}

function addFilter() {
  const current_articles = Array.from(searchField.querySelectorAll('article')).map((article) => article.querySelector(".db-search-category").value);
  const value_to_set = SEARCH_TYPE_OPTIONS_KEYS.find(v => !current_articles.includes(v));
  if (value_to_set) searchField.appendChild(newFilter(value_to_set));
}

addFilterButton.addEventListener('click', addFilter);

submitButton.addEventListener('click', () => {
  const parsed = {};
  document.querySelectorAll('article').forEach(article => {
    const select = article.querySelector('select');
    const inputValue = select.nextSibling.value;
    if (inputValue)
      parsed[select.value] = inputValue;
  });
  const new_params = new URLSearchParams(parsed).toString();
  const loc = window.location;
  loc.replace(`${loc.origin}${loc.pathname}?${new_params}`);
});


document.addEventListener('DOMContentLoaded', () => {
  for (let i=0; i<3; i++)
    addFilter();
})
