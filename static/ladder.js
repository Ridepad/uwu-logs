const BOSSES = {
  'Icecrown Citadel': [
    'The Lich King',
    'Lord Marrowgar', 'Lady Deathwhisper', 'Gunship Battle', 'Deathbringer Saurfang',
    'Festergut', 'Rotface', 'Professor Putricide',
    'Blood Prince Council', "Blood-Queen Lana'thel",
    'Valithria Dreamwalker', 'Sindragosa'
  ],
  'The Ruby Sanctum': ['Halion', 'Baltharus the Warborn', 'General Zarithrian', 'Saviana Ragefire'],
  'Trial of the Crusader': ["Anub'arak", 'Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions', "Twin Val'kyr"],
  'Vault of Archavon': ['Toravon the Ice Watcher', 'Archavon the Stone Watcher', 'Emalon the Storm Watcher', 'Koralon the Flame Watcher'],
  "Onyxia's Lair": ['Onyxia',],
  'The Eye of Eternity': ['Malygos',],
  'The Obsidian Sanctum': ['Sartharion',],
  'Naxxramas': [
    "Anub'Rekhan", 'Grand Widow Faerlina', 'Maexxna', 'Noth the Plaguebringer', 'Heigan the Unclean',
    'Loatheb', 'Patchwerk', 'Grobbulus', 'Gluth', 'Thaddius', 'Instructor Razuvious', 'Gothik the Harvester',
    'The Four Horsemen', 'Sapphiron', "Kel'Thuzad",
  ],
  'Ulduar': [
    'Flame Leviathan', 'Ignis the Furnace Master', 'Razorscale', 'XT-002 Deconstructor',
    'Assembly of Iron', 'Kologarn', 'Auriaya', 'Hodir', 'Thorim', 'Freya', 'Mimiron',
    'General Vezax', 'Yogg-Saron', 'Algalon the Observer',
  ],
}

const loc = window.location;
const instance = document.getElementById('instance');
const boss = document.getElementById('boss');
const size = document.getElementById('size');
const difficulty = document.getElementById('difficulty');
const combine_guilds = document.getElementById('combine-guilds');
const submit = document.getElementById("submit");

const new_option = (v) => {
  const _option = document.createElement('option');
  _option.setAttribute("value", v);
  _option.innerHTML = v;
  return _option;
}

const add_bosses = () => BOSSES[instance.value].forEach(boss_name => boss.appendChild(new_option(boss_name)));

Object.keys(BOSSES).forEach(raid => instance.appendChild(new_option(raid)));

const params = new URLSearchParams(loc.search);
const selects = ['instance', 'boss', 'size'];
selects.forEach(t => {
  const i = params.get(t);
  const h = document.getElementById(t);
  i ? h.value = i : h.selectedIndex = 0;
  if (t == 'instance') add_bosses();
});
difficulty.checked = params.get('difficulty') == 1;
combine_guilds.checked = params.get('combine_guilds') == 1;

instance.addEventListener('change', () => {
  boss.innerHTML = "";
  add_bosses();
});
function searchChanged(params) {
  const parsed = {
    instance: instance.value,
    boss: boss.value,
    size: size.value,
    difficulty: difficulty.checked ? 1 : 0,
    combine_guilds: combine_guilds.checked ? 1 : 0,
  };
  const new_params = new URLSearchParams(parsed).toString();
  loc.replace(`${loc.origin}${loc.pathname}?${new_params}`);
}
// submit.addEventListener('click', searchChanged);
[instance, boss, size, difficulty, combine_guilds].forEach(e => e.addEventListener('change', searchChanged))
