const getCellValue = (tr, className) => tr.querySelector(className).textContent.replace(/ /g, "");
const comparer = className => (a, b) => getCellValue(b, className) - getCellValue(a, className);
function table_sort_by_th(th) {
  const class_name = `.total-cell.${th.classList[0]}`;
  const tbody = document.querySelector("tbody");
  let rows = Array.from(tbody.querySelectorAll("tr")).splice(1).sort(comparer(class_name));
  if (th.classList.contains("points-rank")) {
    rows.reverse();
  }
  rows.forEach(tr => tbody.appendChild(tr));
  rows.forEach(tr => !getCellValue(tr, class_name) && tbody.appendChild(tr));
}

const POINTS = [100, 99, 95, 75, 50, 25, 0];
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
    const to_hide = useful_shown ? useful_class_name : TOTAL[useful_class_name];
    const to_show = useful_shown ? TOTAL[useful_class_name] : useful_class_name;
    add_style(to_show, to_hide);
    table_sort_by_th(document.querySelector(`.${to_show}.sortable`));
    e.stopPropagation();
  }
}
function add_points_color() {
  for (const td of document.querySelectorAll(".points")) {
    for (const i of POINTS) {
      const percentile = parseFloat(td.getAttribute("data-percentile") || 0);
      if (percentile >= i) {
        td.classList.add(`top${i}`);
        break;
      }
    }
  }
}
function init() {
  add_style("heal", "heal_total");
  if (!document.querySelector(".useful.total-cell").textContent.length) {
    add_style(TOTAL["useful"], "useful");
    table_sort_by_th(document.querySelector(`.${TOTAL["useful"]}.sortable`));
  }

  add_points_color();

  document.querySelectorAll(".swap-damage").forEach(button => button.addEventListener("click", swap_click_wrap("useful")));
  document.querySelectorAll(".swap-heal").forEach(button => button.addEventListener("click", swap_click_wrap("heal")));
  document.querySelectorAll("th.sortable").forEach(th => th.addEventListener("click", e => table_sort_by_th(e.target)));
}
document.readyState !== 'loading' ? init() : document.addEventListener('DOMContentLoaded', init);
