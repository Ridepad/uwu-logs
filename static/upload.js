const POST_URL = "/upload";
const CHUNK_SIZE = 256*1024;
const ALLOWED_EXTENSIONS = ["7z", "zip"]

const infoSection = document.getElementById('upload-info');
const fileSection = document.getElementById("upload-section");
const fileSelect = document.getElementById("upload-form-select");
const fileSubmit = document.getElementById("upload-form-submit");
const serverInput = document.getElementById("server-input");

const processingSection = document.getElementById("upload-progress-section");
const progressBarWrapper = document.getElementById('upload-progress-bar-wrapper');
const progressBar = document.getElementById('upload-progress-bar');
const progressBarPercentage = document.getElementById('upload-progress-bar-percentage');
const processingStatus = document.getElementById("upload-status");
const processingTable = document.getElementById("upload-table");
const processingTableBody = document.getElementById("upload-table-tbody");

function newRow(report_name, report_data, done) {
  const tr = document.createElement("tr");
  const report_link_cell = document.createElement("td");
  if (done) {
    const report_link = document.createElement("a");
    report_link.href = `/reports/${report_name}`;
    report_link.target = "_blank";
    report_link.innerText = report_name;
    report_link_cell.appendChild(report_link);
  } else {
    report_link_cell.innerText = report_name;
  }
  tr.appendChild(report_link_cell);
  
  const status_cell = document.createElement("td");
  status_cell.innerText = report_data.status;
  tr.appendChild(status_cell);
  return tr
}

const requestLogsProcessingInfo = new XMLHttpRequest();

let timeout;

function logsProcessingCheck() {
  console.log('logsProcessingCheck');
  requestLogsProcessingInfo.open("GET", "/upload_progress");
  requestLogsProcessingInfo.send();
}

function upload_progress() {
  console.log('upload_progress', requestLogsProcessingInfo.readyState, requestLogsProcessingInfo.status);
  if (requestLogsProcessingInfo.readyState !== 4) return;
  if (requestLogsProcessingInfo.status === 500) {
    processingStatus.innerText = "Server error...";
    return;
  }
  if (requestLogsProcessingInfo.status !== 200) {
    processingStatus.innerText = "Aborted!";
    return;
  }
  console.log('upload_progress 200');

  timeout = setTimeout(logsProcessingCheck, 250);

  const res = JSON.parse(requestLogsProcessingInfo.response);
  const done = res.done == 1
  if (done) clearTimeout(timeout);
  if (!res.slices) return;

  fileSection.style.display = "none";
  infoSection.style.display = "none";
  processingSection.style.display = "";
  progressBarWrapper.style.display = "none";
  processingTable.style.display = "";
  processingTableBody.innerHTML = "";
  processingStatus.innerText = res.status || "Preparing...";

  for (let slice_name in res.slices) {
    const slice = res.slices[slice_name];
    processingTableBody.appendChild(newRow(slice_name, slice, done));
  }
}

fileSelect.onchange = () => {
  const file = fileSelect.files[0];
  const ext = file.name.split('.').pop();
  if (!ALLOWED_EXTENSIONS.includes(ext) || file.type == "text/plain") {
    alert('File is not an archive.\nPlease archive the file first.');
    fileSelect.value = "";
  } else if (file.size < 16384) {
    alert('Archive is too small, did you archive correct file?');
    fileSelect.value = "";
  }
}

fileSubmit.onclick = () => {
  if (fileSelect.files.length == 0) {
    alert('File was not selected');
    return;
  }

  processingStatus.innerText = "Uploading...";
  const request = new XMLHttpRequest();
  const started = Date.now();
  let current = 0;
  let retries = 0;
  let chunkN = 0;
  const file = fileSelect.files[0];
  const filedata = JSON.stringify({
    filename: file.name,
    server: serverInput.value,
    timezone:  Intl.DateTimeFormat().resolvedOptions().timeZone,
  })
  
  async function sendnewchunk(retry) {
    console.log('sendnewchunk', retry);
    if (!retry) {
      chunkN = chunkN + 1;
    }
    const chunk = file.slice(current, current + CHUNK_SIZE);
    const arrayBuffer = await chunk.arrayBuffer();
    const byteArray = new Uint8Array(arrayBuffer);
    request.open("POST", POST_URL);
    request.setRequestHeader("X-Chunk", chunkN);
    request.setRequestHeader("X-Date", started);
    request.timeout = 10000;
    request.send(byteArray);
  }

  function retry() {
    if (retries > 5) {
      progressBar.style.backgroundColor = "red";
      progressBarPercentage.innerHTML = "Server error!";
      return;
    }
    retries = retries + 1;
    sendnewchunk(true);
  }

  function upload_on_ready () {
    console.log('upload_on_ready');
    if (request.readyState !== 4) return;
    if (request.status === 201) return logsProcessingCheck();
    if (request.status !== 200) return retry();
    console.log('upload_on_ready 200');
    
    retries = 0;
    current = current + CHUNK_SIZE;
    const fsize = Math.min(file.size, current);
    const percent = Math.round(fsize / file.size * 100);
    const done = fsize / 1024 / 1024;
    progressBar.style.width = `${percent}%`;
    const timepassed = Date.now() - started;
    const speed = current / timepassed;
    progressBarPercentage.innerHTML = `${done.toFixed(1)}MB (${speed.toFixed(1)}KB/s | ${percent}%)`;

    if (current < file.size) return sendnewchunk();

    request.open("POST", POST_URL);
    request.setRequestHeader("Content-Type", "application/json");
    request.send(filedata);
  }

  request.ontimeout = retry;
  request.onreadystatechange = upload_on_ready;

  processingSection.style.display = "";
  fileSection.style.display = "none";
  infoSection.style.display = "none";
  sendnewchunk();
}

requestLogsProcessingInfo.timeout = 2500;
requestLogsProcessingInfo.ontimeout = logsProcessingCheck;
requestLogsProcessingInfo.onreadystatechange = upload_progress;
logsProcessingCheck();
