const main = document.querySelector("main");
// const REPORT_ID = main.getAttribute("data-report-id");
const SOURCE_NAME = main.getAttribute("data-source-name");
const TOGGLE_GRAPH = document.getElementById('toggle-graph');
const SELECT_SLICE_SECONDS = document.getElementById("sliced-sec");
const CHART_ELEMENT_WRAP = document.getElementById("chart-wrap");
const CONTROLS_WRAP = document.getElementById("controls-wrap");
const CHART_OVERLAY = document.getElementById('overlay');
const MAIN_CANVAS = document.getElementById('chart');
const RANGE_MIN = document.querySelector(".range-values .min-value");
const RANGE_MAX = document.querySelector(".range-values .max-value");
const RANGE_TOTAL = document.querySelector(".range-values .total-value");
const selectionContext = CHART_OVERLAY.getContext('2d');
const SUMBIT = document.querySelector(".min-max-slider-submit");

const REPORT_ID = window.location.pathname.split('/')[2];
const SELECTION_COLOR = "#8320DF";
const SELECTION_ALPHA = 0.1;

const CACHED_GRAPHS = {};
const GET_DPS_REQUEST = new XMLHttpRequest();
const QUERY_PARAMS = new URLSearchParams(window.location.search);
const start = QUERY_PARAMS.get("s");
const end = QUERY_PARAMS.get("f");
const start_custom = QUERY_PARAMS.get("sc") ?? 0;
const end_custom = QUERY_PARAMS.get("fc") ?? 0;
const DURATION = parseFloat(document.getElementById("report-main").getAttribute("data-duration"));
const selection = {
  w: 0,
  startX: 0,
  startIndex: start_custom,
  lastIndex: end_custom,
  drag: false,
};
console.log(selection);
const CHART_OPTIONS = {
  maintainAspectRatio: false,
  responsive: true,
  animation: false,
  interaction: {
    mode: 'index',
  },
  plugins: {
    tooltip: {
      intersect: false,
    },
    legend: {
      display: false,
    },
  },
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
};
const CHART = new Chart(MAIN_CANVAS, {
  type: 'line',
  options: CHART_OPTIONS,
});

function make_new_dataset(datapoints) {
  return {
    data: datapoints,
    cubicInterpolationMode: 'monotone',
    borderColor: '#6900cc',
    pointBorderWidth: 0,
  }
}

function chartSetData(datapoints) {
  if (Object.keys(datapoints).length === 0) return;

  const datapoints_values = Object.values(datapoints);
  const datapoints_min = Math.min(...datapoints_values);
  const datapoints_max = Math.max(...datapoints_values);
  CHART.options.scales.y.min = Math.floor(datapoints_min);
  CHART.options.scales.y.max = Math.ceil(datapoints_max);
  CHART.data.datasets[0] = make_new_dataset(datapoints);
  CHART.update();
  setTimeout(() => {
    CHART_OVERLAY.width = MAIN_CANVAS.width;
    CHART_OVERLAY.height = MAIN_CANVAS.height;
    selectionContext.fillStyle = SELECTION_COLOR;
    selectionContext.globalAlpha = SELECTION_ALPHA;
    selection.w = (end_custom - start_custom) / (end - start) * (MAIN_CANVAS.width - 50);
    selection.startX = start_custom / (end - start) * MAIN_CANVAS.width + 50;
    console.log(selection);
    selectionContext.fillRect(
      selection.startX,
      0,
      selection.w,
      CHART.chartArea.bottom - CHART.chartArea.top
    );
  });
}

GET_DPS_REQUEST.onreadystatechange = () => {
  if (GET_DPS_REQUEST.readyState != 4) return;
  if (GET_DPS_REQUEST.status != 200) return;
  
  const datapoints = JSON.parse(GET_DPS_REQUEST.response);
  CACHED_GRAPHS[SELECT_SLICE_SECONDS.value] = datapoints;
  chartSetData(datapoints);
}

function send_post() {
  const params_obj = Object.fromEntries(QUERY_PARAMS);
  params_obj["player_name"] = SOURCE_NAME;
  params_obj["sec"] = SELECT_SLICE_SECONDS.value;
  const END_POINT = `/reports/${REPORT_ID}/get_dps`;
  GET_DPS_REQUEST.open("POST", END_POINT);
  GET_DPS_REQUEST.send(JSON.stringify(params_obj));
}

function toggle_graph() {
  if (!TOGGLE_GRAPH.checked) return;

  const data = CACHED_GRAPHS[SELECT_SLICE_SECONDS.value];
  data ? chartSetData(data) : send_post();
}

function time_to_text(t) {
  const minutes = `${Math.floor(t/60)}`.padStart(2, '0');
  const seconds = `${t%60}`.padStart(2, '0');
  return `${minutes}:${seconds}`
}
function set_text_range() {
  const mult = Math.max(SELECT_SLICE_SECONDS.value, 1);
  const _min = Math.min(selection.startIndex, selection.lastIndex) * mult;
  const _max = Math.max(selection.startIndex, selection.lastIndex) * mult;
  RANGE_MIN.textContent = time_to_text(_min);
  RANGE_MAX.textContent = time_to_text(_max);
  RANGE_TOTAL.textContent = `(${time_to_text(_max-_min)})`;
}

function chart_getElementsAtEventForMode(e) {
  return CHART.getElementsAtEventForMode(e, 'index', {intersect: false});
}
function get_index(e) {
  const points = chart_getElementsAtEventForMode(e);
  if (points[0]) return points[0].index;
  if (e.clientX < CHART.chartArea.left) return 0;
  if (e.clientX > CHART.chartArea.right) return Object.keys(CHART.data.datasets[0].data).length;
  return selection.lastIndex;
}

MAIN_CANVAS.addEventListener('pointerdown', e => {
  const rect = MAIN_CANVAS.getBoundingClientRect();
  selection.startX = e.clientX - rect.left;
  selection.startIndex = get_index(e);
  selection.drag = true;
  selectionContext.clearRect(0, 0, MAIN_CANVAS.width, MAIN_CANVAS.height);
});

function redraw(e) {
  const _left = MAIN_CANVAS.getBoundingClientRect().left;
  const x = e.clientX - _left;
  selection.w = x - selection.startX;
  selectionContext.clearRect(0, 0, MAIN_CANVAS.width, MAIN_CANVAS.height);
  selectionContext.fillRect(
    selection.startX,
    0,
    selection.w,
    CHART.chartArea.bottom - CHART.chartArea.top
  );
}
function draw_stop(e) {
  if (!selection.drag) return;
  selection.drag = false;
  const index = get_index(e);
  selection.lastIndex = index;
  set_text_range();
}
MAIN_CANVAS.addEventListener("mouseleave", e => {
  if (!selection.drag) return;
  selection.drag = false;
  set_text_range();
});
MAIN_CANVAS.addEventListener('pointermove', e => {
  if (!selection.drag) return;
  const index = get_index(e);
  selection.lastIndex = index;
  redraw(e);
  set_text_range();
});
MAIN_CANVAS.addEventListener('pointerup', draw_stop);

SUMBIT.addEventListener("click", () => {
  QUERY_PARAMS.set("sc", selection.startIndex);
  QUERY_PARAMS.set("fc", selection.lastIndex);
  window.location.replace(`?${QUERY_PARAMS.toString()}`);
});

set_text_range();
toggle_graph();
TOGGLE_GRAPH.addEventListener("change", toggle_graph);
SELECT_SLICE_SECONDS.addEventListener("change", toggle_graph);
// document.readyState !== "loading" ? init() : document.addEventListener("DOMContentLoaded", init);
