const main = document.querySelector("main");
// const REPORT_ID = main.getAttribute("data-report-id");
const SOURCE_NAME = main.getAttribute("data-source-name");
const TOGGLE_GRAPH = document.getElementById('toggle-graph');
const CHART_ELEMENT_WRAP = document.getElementById('chart-wrap');
const SELECT_SLICE_SECONDS = document.getElementById("sliced-sec");
const SLICED_CONTROL = document.querySelector(".sliced-control");
const MIN_MAX_SLIDER = document.querySelector(".min-max-slider");

const REPORT_ID = window.location.pathname.split('/')[2];

const GET_DPS_REQUEST = new XMLHttpRequest();
const QUERY_PARAMS = new URLSearchParams(window.location.search);
const CACHED_GRAPHS = {};

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
  if (!TOGGLE_GRAPH.checked) {
    CHART_ELEMENT_WRAP.style.display = "none";
    SLICED_CONTROL.style.display = "none";
    if (MIN_MAX_SLIDER) MIN_MAX_SLIDER.style.display = "none";
    return;
  }
  CHART_ELEMENT_WRAP.style.removeProperty("display");
  SLICED_CONTROL.style.removeProperty("display");
  if (MIN_MAX_SLIDER) MIN_MAX_SLIDER.style.removeProperty("display");
  const data = CACHED_GRAPHS[SELECT_SLICE_SECONDS.value];
  data ? chartSetData(data) : send_post();
}

toggle_graph();
TOGGLE_GRAPH.addEventListener("change", toggle_graph);
SELECT_SLICE_SECONDS.addEventListener("change", toggle_graph);
