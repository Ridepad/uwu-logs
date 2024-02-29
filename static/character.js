const player_points_wrap = document.getElementById("player-points-wrap");
const main_body = document.getElementById("points-body");
const tooltip = document.getElementById("tooltip-points");
const player_name = document.getElementById("player-name");
const player_server = document.getElementById("player-server");
const player_overall_points = document.getElementById("player-overall-points");
const player_overall_rank = document.getElementById("player-overall-rank");
const BUTTON_TOGGLE_MORE_BOSSES = document.getElementById("toggle-more-bosses");
const POINTS = [100, 99, 95, 90, 75, 50, 25, 0];
const ARMORY_SERVERS = [
    "Lordaeron",
    "Icecrown",
    "Onyxia",
];
const SPEC_BUTTONS = [1,2,3].map(i => ({
    index: i,
    input: document.getElementById(`spec-${i}-input`),
    label: document.getElementById(`spec-${i}-label`),
}));
const KEY_TO_SELECTOR = {
    "data-players": ".row-players .td-player",
    "data-players-n": ".row-players .td-max",
    "data-raids": ".row-raids .td-player",
    "data-raids-n": ".row-raids .td-max",
    "data-dps": ".row-dps .td-player",
    "data-dps-r1": ".row-dps .td-max",
    "data-points-dps": ".row-dps .td-points",
    "data-points-raids": ".row-raids .td-points",
    "data-points-players": ".row-players .td-points",
};

const CACHE = {};

const char_request = new XMLHttpRequest();
char_request.onreadystatechange = () => {
    if (char_request.status != 200 || char_request.readyState != 4) return;

    const j = JSON.parse(char_request.response);
    CACHE[window.location.search] = j;
    table_add_new_data(j);
    player_points_wrap.style.removeProperty("display");
}


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
let last_class;

function add_point(v) {
    return (v / 100).toFixed(2);
}

function split_thousands(v) {
    const a = v.toString().split('');
    const insert_at = a.includes(".") ? 5 : 3;
    if (a.length <= insert_at) return v;
    a.splice(a.length-insert_at, 0, ' ');
    return a.join('');
}

function format_dps(v) {
    v = v.toFixed(1);
    return split_thousands(v);
}

function cell(v, _class) {
    const td = document.createElement("td")
    td.className = _class;
    td.append(v);
    return td;
}

function format_duration(dur) {
  const minutes = Math.floor(dur / 60);
  const seconds = Math.floor(dur % 60);
  const m_str = minutes.toString().padStart(2, '0');
  const s_str = seconds.toString().padStart(2, '0');
  return `${m_str}:${s_str}`;
}

function points_rank_class(v) {
    for (const i of POINTS) if (v - i >= 0) return `top${i}`;
}

function cell_points(v) {
    const _class = points_rank_class(v/100);
    v = add_point(v);
    const td = cell(v, "cell-points");
    td.classList.add(_class);
    return td;
}

function row_onenter(event) {
    const row = event.target;
    for (const key in KEY_TO_SELECTOR) {
        tooltip.querySelector(KEY_TO_SELECTOR[key]).textContent = row.getAttribute(key);
    }
    const trRect = row.getBoundingClientRect();
    tooltip.style.top = trRect.bottom + 'px';
    tooltip.style.left = trRect.left + 'px';
    tooltip.style.removeProperty("display");
}

function cell_date(report_ID) {
    const report_date = report_ID.toString().slice(0, 15);
    const [year, month, day, ] = report_date.split('-');
    const date_text = `${day}-${month}-${year}`;

    const search = new URLSearchParams(window.location.search);
    const server = search.get("server");
    const _a = document.createElement('a');
    _a.href = `/reports/${report_ID}--${server}`;
    _a.target = "_blank";
    _a.append(date_text);

    const cell = document.createElement('td');
    cell.appendChild(_a);
    cell.className = "cell-date";

    return cell;
}

function add_dummy_cells(tr) {
    tr.appendChild(cell("", "cell-rank"));
    tr.appendChild(cell_points(0));
    tr.appendChild(cell("", "cell-dps"));
    tr.appendChild(cell("", "cell-dur"));
    tr.appendChild(cell("", "cell-raids"));
    tr.appendChild(cell("", "cell-date"));
}

function row(boss_name, data) {
    const tr = document.createElement("tr");
    tr.appendChild(cell(boss_name, "player-cell"));
    if (!data["rank_players"]) {
        add_dummy_cells(tr);
        return tr;
    };

    tr.appendChild(cell(split_thousands(data["rank_players"]), "cell-rank"));
    tr.appendChild(cell_points(data["points"]));
    tr.appendChild(cell(format_dps(data["dps_max"]), "cell-dps"));
    tr.appendChild(cell(format_duration(data["dur_min"]), "cell-dur"));
    tr.appendChild(cell(split_thousands(data["raids"]), "cell-raids"));
    tr.appendChild(cell_date(data["report"]));

    tr.setAttribute("data-players", split_thousands(data["rank_players"]));
    tr.setAttribute("data-players-n", split_thousands(data["n_players"]));
    tr.setAttribute("data-raids", split_thousands(data["rank_raids"]));
    tr.setAttribute("data-raids-n", split_thousands(data["n_raids"]));
    tr.setAttribute("data-dps", format_dps(data["dps_max"]));
    tr.setAttribute("data-dps-r1", format_dps(data["dps_r1"]));
    tr.setAttribute("data-points-dps", add_point(data["points_dps"]));
    tr.setAttribute("data-points-raids", add_point(data["points_rank_raids"]));
    tr.setAttribute("data-points-players", add_point(data["points_rank_players"]));
    
    tr.addEventListener("mouseenter", row_onenter);
    tr.addEventListener("mouseleave", () => tooltip.style.display = "none");
    
    return tr;
}

function set_new_player_name(name, server) {
    player_server.textContent = server;
    player_name.textContent = name;
    if (ARMORY_SERVERS.includes(server)) {
        player_name.href = `https://armory.warmane.com/character/${name}/${server}`
        player_name.target = "_blank";
    } else {
        player_name.removeAttribute("href");
        player_name.removeAttribute("target");
    }
}

function table_add_new_data(data) {
    main_body.innerHTML = "";
    const boss_data = data.bosses;
    for (const boss_name in boss_data) {
        const tr = row(boss_name, boss_data[boss_name])
        main_body.appendChild(tr);
    }
    set_new_player_name(data.name, data.server);
    const _overall = add_point(data.overall_points);
    player_overall_points.textContent = _overall;
    player_overall_points.className = points_rank_class(_overall);
    player_overall_rank.textContent = `(${data.overall_rank ?? 0})`;
    
    if (last_class == data.class) return;
    
    last_class = data.class;
    const _class = data.class * 4;
    player_name.className = SPECS[_class][2];
    for (const spec_button of SPEC_BUTTONS) {
        const icon_name = SPECS[_class + spec_button.index][1];
        spec_button.label.querySelector("img").src = `static/icons/${icon_name}.jpg`;
    }
}

function query_server() {
    char_request.open("POST", window.location.search);
    char_request.send();
}
function fetch_data() {
    const search = new URLSearchParams(window.location.search);
    const spec = search.get("spec");
    for (const spec_button of SPEC_BUTTONS) {
        if (spec == spec_button.index) spec_button.input.checked = true;
    }

    const data = CACHE[window.location.search];
    data ? table_add_new_data(data) : query_server();
}

function new_spec(spec) {
    const search = new URLSearchParams(window.location.search);
    search.set("spec", spec);
    history.pushState(null, "", `?${search}`);
    fetch_data();
}
function toggle_more_bosses(e) {
    let show = window.localStorage.getItem("show-more-bosses") == "true";
    if (e) {
        show = !show;
        window.localStorage.setItem("show-more-bosses", show);
    }
    if (show) {
        main_body.classList.remove("hide-other-bosses");
    } else {
        main_body.classList.add("hide-other-bosses");
    }
    BUTTON_TOGGLE_MORE_BOSSES.textContent = show ? "Hide other bosses" : "Show other bosses";
}

function init() {
    for (const spec_button of SPEC_BUTTONS) {
        spec_button.input.addEventListener("click", () => new_spec(spec_button.index));
    }
    window.addEventListener("popstate", fetch_data);
    fetch_data();

    const searchParams = new URLSearchParams(location.search);
    const server = searchParams.get("server") ?? "Lordaeron";
    const character_name = searchParams.get("name") ?? "Safiyah";
    set_new_player_name(character_name, server);
    
    toggle_more_bosses();
    BUTTON_TOGGLE_MORE_BOSSES.addEventListener("click", toggle_more_bosses);
}

  
document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
  