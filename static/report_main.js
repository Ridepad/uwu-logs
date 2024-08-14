const getCellValue = (tr, className) => tr.querySelector(className).textContent.replace(/ /g, "");
const comparer = className => (a, b) => getCellValue(b, className) - getCellValue(a, className);
const getCellValueRank = (tr, className) => tr.querySelector(className).getAttribute("data-percentile");
const comparerRank = className => (a, b) => getCellValueRank(b, className) - getCellValueRank(a, className);
function table_sort_by_th(th) {
  const class_name = `.total-cell.${th.classList[0]}`;
  const tbody = document.querySelector("tbody");
  let rows = Array.from(tbody.querySelectorAll("tr")).splice(1)
  if (th.classList.contains("points-rank")) {
    rows.sort(comparerRank(class_name));
  } else {
    rows.sort(comparer(class_name));
  }
  rows.forEach(tr => tbody.appendChild(tr));
  rows.forEach(tr => !getCellValue(tr, class_name) && tbody.appendChild(tr));
}

const POINTS = [100, 99, 95, 90, 75, 50, 25, 0];
const TOTAL = {
  "useful": "damage",
  "heal": "heal_total",
}
function add_style(to_show, to_hide) {
  const style = document.createElement("style");
  style.append(`.${to_show} {display: revert} .${to_hide} {display: none}`);
  document.head.appendChild(style);
}
function swap_click_wrap(useful_class_name) {
  return e => {
    const useful_shown = e.target.parentElement.classList.contains(useful_class_name);
    const total_class_name = TOTAL[useful_class_name];
    const to_hide = useful_shown ? useful_class_name : total_class_name;
    const to_show = useful_shown ? total_class_name : useful_class_name;
    add_style(to_show, to_hide);
    table_sort_by_th(document.querySelector(`.${to_show}.sortable`));
    e.stopPropagation();
  }
}


function add_ranks(data) {
  Array.from(document.querySelectorAll("tbody tr")).forEach(tr => {
    const player_name = tr.querySelector(".player-cell a").textContent.trim();
    const rank_data = data[player_name];
    if (!rank_data) return;

    const points_rank_cell = tr.querySelector(".points-rank");
    points_rank_cell.textContent = rank_data.rank;
    points_rank_cell.title = `Better than ${rank_data.percentile}% of players out of ${rank_data.total_raids_for_spec}`;
    points_rank_cell.setAttribute("data-percentile", rank_data.percentile);
    
    const points_dps_cell = tr.querySelector(".points-dps");
    points_dps_cell.textContent = rank_data.from_spec_top1.toFixed(1);
    points_dps_cell.setAttribute("data-percentile", rank_data.from_spec_top1);
  });
}
function cell_add_rank_color(td, percentile) {
  if (isNaN(percentile)) return;

  for (const i of POINTS) {
    if (percentile >= i) {
      td.classList.add(`top${i}`);
      return;
    }
  }
}
function add_ranks_color() {
  for (const td of document.querySelectorAll(".points")) {
    const percentile = parseFloat(td.getAttribute("data-percentile"));
    cell_add_rank_color(td, percentile);
  }
}

const RANK_REQUEST = new XMLHttpRequest();
RANK_REQUEST.onreadystatechange = () => {
  if (RANK_REQUEST.readyState != 4) return;
  if (RANK_REQUEST.status != 200) return;

  const j = JSON.parse(RANK_REQUEST.response);
  
  add_ranks(j);
  add_ranks_color();
}

function make_rank_data() {
  const data = {
    dps: {},
    specs: {},
  }

  Array.from(document.querySelectorAll("tbody tr")).forEach(tr => {
    const player_cell = tr.querySelector(".player-cell");
    const name = player_cell.querySelector("a").textContent;
    const spec = player_cell.getAttribute("title");
    const dps = tr.querySelector("td.useful.per-sec-cell").textContent.replaceAll(" ", "");
    if (dps == "") return;
    if (name == "Total") return;
    data.dps[name] = dps;
    data.specs[name] = spec;
  });

  return data;
}
function send_ranks_request() {
  const ranks_data = make_rank_data();
  const report_id = window.location.pathname.split("/")[2];
  const server_name = report_id.split("--").at(-1);
  const fight_name = document.getElementById("slice-name").textContent;
  const fight_mode = document.getElementById("slice-tries").textContent.split(" ")[0];
  const j = JSON.stringify({
    "server": server_name,
    "boss": fight_name,
    "mode": fight_mode,
    "dps": ranks_data.dps,
    "specs": ranks_data.specs,
  });

  RANK_REQUEST.open("POST", "/rank");
  RANK_REQUEST.setRequestHeader("Content-Type", "application/json");
  RANK_REQUEST.send(j);
}

function init() {
  add_style("heal", "heal_total");
  if (!document.querySelector(".useful.total-cell").textContent.length) {
    add_style(TOTAL["useful"], "useful");
    table_sort_by_th(document.querySelector(`.${TOTAL["useful"]}.sortable`));
  }

  send_ranks_request();

  document.querySelectorAll(".swap-damage").forEach(button => button.addEventListener("click", swap_click_wrap("useful")));
  document.querySelectorAll(".swap-heal").forEach(button => button.addEventListener("click", swap_click_wrap("heal")));
  document.querySelectorAll("th.sortable").forEach(th => th.addEventListener("click", e => table_sort_by_th(e.target)));
}
document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);
