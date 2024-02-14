const getCellValue = (tr, className) => tr.querySelector(className).textContent.replace(/ /g, "");
const comparer = className => (a, b) => getCellValue(b, className) - getCellValue(a, className);
function table_sort_by_th(th) {
  const tbody = document.querySelector("tbody");
  Array.from(tbody.querySelectorAll("tr"))
       .splice(1)
       .sort(comparer(`.total-cell.${th.classList[0]}`))
       .forEach(tr => tbody.appendChild(tr));
}

const POINTS = [100, 99, 95, 75, 50, 25, 0];

const CHART_OPTIONS = {
  maintainAspectRatio: false,
  responsive: true,
  animation: false,
  scales: {
    x: {
      grid: {
        color: '#141414',
        tickLength: 1,
      },
    },
    y: {
      grid: {
        color: '#141414',
        tickLength: 1,
      },
      title: {
        display: true,
        text: 'DPS',
      },
      ticks: {
        padding: 0,
      },
    },
  },
  plugins: {
    tooltip: {
      intersect: false,
    },
    legend: {
      display: false,
    },
  },
  interaction: {
    mode: 'index',
  }
};
const CHART = new Chart(document.getElementById('chart'), {
  type: 'line',
  options: CHART_OPTIONS,
});

function make_new_dataset(datapoints) {
  return {
    data: datapoints,
    cubicInterpolationMode: 'monotone',
    borderColor: '#6900cc',
    pointBorderWidth: 0,
  };
}

function chartSetData(datapoints) {
  if (
    Object.keys(datapoints).length === 0
  && CHART.data.datasets.length === 0
  ) {
    return;
  }
  const datapoints_values = Object.values(datapoints);
  const datapoints_min = Math.min(...datapoints_values);
  const datapoints_max = Math.max(...datapoints_values);
  CHART.options.scales.y.min = Math.floor(datapoints_min);
  CHART.options.scales.y.max = Math.ceil(datapoints_max);
  CHART.data.datasets[0] = make_new_dataset(datapoints);
  CHART.update();
  document.getElementById('chart-wrap').style.removeProperty("display");
}

function get_dps() {
  const reportID = window.location.pathname.split('/')[2];
  const END_POINT = `/reports/${reportID}/get_dps`;
  const params = new URLSearchParams(window.location.search);
  const params_obj = Object.fromEntries(params);
  const request = {
    method: "POST",
    body: JSON.stringify(params_obj),
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  };
  fetch(END_POINT, request).then(r => r.json()).then(datapoints => chartSetData(datapoints));
}

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
      if (td.textContent - i >= 0) {
        td.classList.add(`top${i}`);
        break;
      }
    }
  }
}
(() => {
  get_dps();

  add_style("heal", "heal_total");
  if (!document.querySelector(".useful.total-cell").textContent.length) {
    add_style(TOTAL["useful"], "useful");
    table_sort_by_th(document.querySelector(`.${TOTAL["useful"]}.sortable`));
  }

  add_points_color();

  document.querySelectorAll(".swap-damage").forEach(button => button.addEventListener("click", swap_click_wrap("useful")));
  document.querySelectorAll(".swap-heal").forEach(button => button.addEventListener("click", swap_click_wrap("heal")));
  document.querySelectorAll("th.sortable").forEach(th => th.addEventListener("click", e => table_sort_by_th(e.target)));
})();
