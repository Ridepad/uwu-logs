// const select_otpions_all = [
//   "Boss", "Difficulty", "Size", "Char Name", "Guild Name",
//   "Duration >", "Wipes >", "Achievements", 'Guild Kill',
//   // "Specs",
// ]
const OPTION_TYPES = {
  "boss": "Boss",
  "mode": "Difficulty",
  "size": "Size",
  "spellName": "Char Name",
  "guildName": "Guild Name",
  "time": "Duration >",
  "wipe": "Wipes >",
  "achi": "Achievements",
  "isGuild": "Guild Kill",
  "specs": "Specs",
}

const select_options_all = Array.from(Object.keys(OPTION_TYPES));

const select_options = {
  "Boss": [
    'The Lich King', 'Halion','Deathbringer Saurfang', 'Festergut', 'Rotface', 'Professor Putricide', "Blood-Queen Lana'thel", 'Sindragosa',
    'Lord Marrowgar', 'Lady Deathwhisper', 'Gunship Battle', 'Blood Prince Council', 'Valithria Dreamwalker',
    'Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions', "Twin Val'kyr", "Anub'arak", 
    'Onyxia', 'Malygos', 'Sartharion', 'Baltharus the Warborn', 'General Zarithrian', 'Saviana Ragefire', 
    'Archavon the Stone Watcher', 'Emalon the Storm Watcher', 'Koralon the Flame Watcher', 'Toravon the Ice Watcher',
    "Anub'Rekhan", 'Grand Widow Faerlina', 'Maexxna', 'Noth the Plaguebringer', 'Heigan the Unclean', 'Loatheb', 'Patchwerk',
    'Grobbulus', 'Gluth', 'Thaddius', 'Instructor Razuvious', 'Gothik the Harvester', 'The Four Horsemen', 'Sapphiron', "Kel'Thuzad",
    'Flame Leviathan', 'Ignis the Furnace Master', 'Razorscale', 'XT-002 Deconstructor', 'Assembly of Iron', 'Kologarn', 'Auriaya',
    'Hodir', 'Thorim', 'Freya', 'Mimiron', 'General Vezax', 'Yogg-Saron', 'Algalon the Observer'
  ],
  "Difficulty": ["Heroic", "Normal"],
  "Size": ["25", "10"],
  "Achievements": ["Yes", "No"],
  "Guild Kill": ["Yes", "No"],
}

const select_options2 = {
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
  "achi": {
    "0": "No",
    "1": "Yes",
  },
  "isGuild": {
    "0": "No",
    "1": "Yes",
  },
}

const submitButton = document.getElementById("submitButton");
const addFilterButton = document.getElementById("addFilterButton");
const searchField = document.getElementById("db-search-field");

const deleteFilterButton = document.createElement('button');
deleteFilterButton.innerText = "X";
deleteFilterButton.setAttribute("type", "reset");



// select_options_all.forEach(option_name => {
// });

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

function newInput() {
  const inputRight = document.createElement('input');
  inputRight.setAttribute("size", "10");
  inputRight.setAttribute("type", "text");
  inputRight.setAttribute("maxlength", "30");
  return inputRight
}

function changeSeachInput(select) {
  const options = select_options2[select.value];
  console.log(options);
  const new_child = options ? newSelect(options) : newInput();
  new_child.setAttribute("class", "db-search-input");
  const article = select.closest('article');
  // const n = select.nextSibling;
  const n = article.querySelector(".db-search-input");
  n ? article.replaceChild(new_child, n) : article.appendChild(new_child);
}

const searchArg = document.createElement('select');
for (let option_value in OPTION_TYPES) {
  const _option = document.createElement('option');
  _option.setAttribute("value", option_value); 
  _option.innerText = OPTION_TYPES[option_value];
  searchArg.appendChild(_option);
}

function newSearchArgument(value_to_set) {
  const _select = selectLeft.cloneNode(true);
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

  const select = newSearchArgument(value_to_set);
  article.appendChild(select);
  
  changeSeachInput(select);
  return article
}

function add_filter() {
  const current_articles = Array.from(searchField.querySelectorAll('article')).map((article) => article.querySelector(".db-search-category").value);
  const value_to_set = select_options_all.find(v => !current_articles.includes(v));
  if (value_to_set) searchField.appendChild(newFilter(value_to_set));
}

addFilterButton.addEventListener('click', add_filter);

submitButton.addEventListener('click', () => {
  const parsed = {};
  document.querySelectorAll('article').forEach(article => {
    const select = article.querySelector('select');
    parsed[select.value] = select.nextSibling.value;
  });
  const new_params = new URLSearchParams(parsed).toString();
  window.location.replace(`${window.location.origin}${window.location.pathname}?${new_params}`);
});


document.addEventListener('DOMContentLoaded', () => {
  for (let i=0; i<3; i++)
    add_filter();
})