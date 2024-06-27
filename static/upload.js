const POST_URL = "/upload";
const CHUNK_SIZE = 256*1024;
const ALLOWED_EXTENSIONS = ["7z", "zip", "rar", "xz", "tar", "lzma", "bzip2", "gzip"];

const SECTION_INFO = document.getElementById('upload-info');
const SECTION_FILE = document.getElementById("upload-section");
const FILE_SELECT = document.getElementById("upload-form-select");
const FILE_SUBMIT = document.getElementById("upload-form-submit");
const INPUT_SERVER = document.getElementById("server-input");

const SECTION_PROCESSING = document.getElementById("upload-progress-section");
const PROGRESS_BAR_WRAP = document.getElementById('upload-progress-bar-wrapper');
const PROGRESS_BAR = document.getElementById('upload-progress-bar');
const PROGRESS_BAR_PERCENTAGE = document.getElementById('upload-progress-bar-percentage');
const UPLOAD_STATUS = document.getElementById("upload-status");
const UPLOAD_TABLE = document.getElementById("upload-table");
const UPLOAD_TABLE_TBODY = document.getElementById("upload-table-tbody");

const SERVER_ERRORS = [400, 500, 507];

function new_status_msg(msg) {
  UPLOAD_STATUS.innerHTML = "";
  for (const line of msg.split("  ")) {
    const p = document.createElement("p");
    p.textContent = line;
    UPLOAD_STATUS.appendChild(p);
  }
}
function add_parsed_slices(slices) {
  if (!slices) return;
  UPLOAD_TABLE_TBODY.innerHTML = "";
  for (const raid_id in slices) {
    const raid_data = slices[raid_id];
    const row = new_row(raid_id, raid_data);
    UPLOAD_TABLE_TBODY.appendChild(row);
  }
}

function new_row(report_name, report_data) {
  const tr = document.createElement("tr");
  const report_link_cell = document.createElement("td");
  if (report_data.done == 1) {
    const report_link = document.createElement("a");
    report_link.href = `/reports/${report_name}`;
    report_link.target = "_blank";
    report_link.textContent = report_name;
    report_link_cell.appendChild(report_link);
  } else {
    report_link_cell.textContent = report_name;
  }
  tr.appendChild(report_link_cell);
  
  const status_cell = document.createElement("td");
  status_cell.textContent = report_data.status;
  tr.appendChild(status_cell);
  return tr;
}

class UploadProgress extends XMLHttpRequest {
  constructor() {
    super();
    
    this.timeout = 5000;
    this.onload = this.upload_progress;
    this.ontimeout = this.retry;

    this.retries = 0;
    this.shown = false;
  }
  get_progress() {
    this.open("GET", "/upload_progress");
    this.send();
  }
  show() {
    if (this.shown) return;

    SECTION_FILE.style.display = "none";
    SECTION_INFO.style.display = "none";
    SECTION_PROCESSING.style.removeProperty("display");
    PROGRESS_BAR_WRAP.style.display = "none";
    UPLOAD_TABLE.style.removeProperty("display");
    new_status_msg("Preparing...");

    this.shown = true;
  }
  retry() {
    if (this.retries > 5) {
      PROGRESS_BAR.classList.add("error");
      PROGRESS_BAR_PERCENTAGE.textContent = "Server error!";
      return;
    }
    this.retries = this.retries + 1;
    console.log(`retry: ${this.retries}`);
    this.get_progress();
  }

  upload_progress() {
    if (this.status === 404) {
      console.log("upload_progress reset");
      return;
    }
    
    this.show();

    if (this.status == 502) {
      new_status_msg("Upload server is offline");
      return;
    }
    if (SERVER_ERRORS.includes(this.status)) {
      new_status_msg("Server error!");
      return;
    }
    if (this.status !== 200) return this.retry();
  
    this.retries = 0;
    
    const response_json = JSON.parse(this.response);
    if (response_json.done != 1) {
      setTimeout(() => this.get_progress(), 250);
    }
    new_status_msg(response_json.status);
    add_parsed_slices(response_json.slices);
  }
}

class Upload extends XMLHttpRequest {
  constructor(callback_on_finish) {
    super();
    this.timeout = 2500;
    this.ontimeout = this.retry;
    this.onload = this.on_upload_reponse;
    
    this.STARTED_TIMESTAMP = Date.now();
    this.FILE = FILE_SELECT.files[0];
    this.SIZE = this.FILE.size;
    this.TOTAL_CHUNKS = Math.ceil(this.SIZE / CHUNK_SIZE);
    this.FILE_DATA = JSON.stringify({
      filename: this.FILE.name,
      server: INPUT_SERVER.value,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      chunks: this.TOTAL_CHUNKS,
    });
    
    this.retries = 0;
    this.current_chunk = 0;

    this.callback_on_finish = callback_on_finish;
  }
  start() {
    console.log("New file");
    console.log(this.FILE);
    console.log(this.FILE_DATA);
  
    UPLOAD_STATUS.textContent = "Uploading...";
    SECTION_PROCESSING.style.display = "";
    SECTION_FILE.style.display = "none";
    SECTION_INFO.style.display = "none";

    this.send_new_chunk();
  }
  on_upload_reponse() {
    if (SERVER_ERRORS.includes(this.status)) return this.upload_error();
    if (this.status === 201) return this.callback_on_finish();
    if (this.status !== 200) return this.retry();
    
    this.update_upload_bar();
    this.send_new_chunk_wrap();
  }
  async new_file_chunk() {
    const start = (this.current_chunk - 1) * CHUNK_SIZE;
    const end = this.current_chunk * CHUNK_SIZE;
    const chunk = this.FILE.slice(start, end);
    const arrayBuffer = await chunk.arrayBuffer();
    return new Uint8Array(arrayBuffer);
  }
  async send_new_chunk() {
    this.sent_timestamp = Date.now();
    const bytes = await this.new_file_chunk();
    this.open("POST", POST_URL);
    this.setRequestHeader("X-Chunk", this.current_chunk);
    this.setRequestHeader("X-Upload-ID", this.STARTED_TIMESTAMP);
    this.send(bytes);
  }
  async send_new_chunk_wrap(is_retry) {
    if (!is_retry) {
      this.retries = 0;
      this.current_chunk = this.current_chunk + 1;
    }
    
    if (this.current_chunk > this.TOTAL_CHUNKS) {
      return this.send_file_data_to_finish();
    }

    this.send_new_chunk();
  }
  send_file_data_to_finish() {
    console.log(`Done. Total uploaded chunks: ${this.current_chunk}`);
    this.open("POST", POST_URL);
    this.setRequestHeader("Content-Type", "application/json");
    this.send(this.FILE_DATA);
  }
  retry(e) {
    if (this.retries >= 5) {
      PROGRESS_BAR.classList.add("error");
      new_status_msg(`Server error!  Aborted after ${this.retries} tries.`)
      PROGRESS_BAR_PERCENTAGE.textContent = "Server error!";
      return;
    }
    this.retries = this.retries + 1;
    const t = e ? "timeout" : "error";
    PROGRESS_BAR_PERCENTAGE.textContent = `Server ${t} ${this.retries} / 5`;
    console.log(`retry: ${this.retries}`);
    setTimeout(() => {
      this.send_new_chunk_wrap(true);
    }, 1000);
  }
  upload_error() {
    console.log('upload_error');
    const response_json = JSON.parse(this.response);
    console.log(response_json);
    PROGRESS_BAR.classList.add("error");
    PROGRESS_BAR_PERCENTAGE.textContent = "Server error!";
    new_status_msg(response_json.detail);
  }
  uploaded_bytes() {
    const t = this.current_chunk * CHUNK_SIZE;
    return Math.min(this.SIZE, t)
  }
  upload_speed() {
    const time_passed_ms = Date.now() - this.sent_timestamp;
    const time_passed = time_passed_ms / 1000;
    return CHUNK_SIZE / 1024 / time_passed;
    // const timepassed = (Date.now() - this.STARTED_TIMESTAMP) / 1000;
    // return this.uploaded_bytes() / 1024 / timepassed;
  }
  update_upload_bar() {
    const uploaded_bytes = this.uploaded_bytes();
    const uploaded_megabytes = (uploaded_bytes / 1024 / 1024).toFixed(1);
    const percent = (uploaded_bytes / this.SIZE * 100).toFixed(1);
    const speed = this.upload_speed().toFixed(1);
    PROGRESS_BAR.style.width = `${percent}%`;
    PROGRESS_BAR_PERCENTAGE.textContent = `${uploaded_megabytes}MB (${speed}KB/s | ${percent}%)`;
  }
}

FILE_SELECT.value = "";
FILE_SELECT.accept = ALLOWED_EXTENSIONS.map(e => `.${e}`);
FILE_SELECT.onchange = () => {
  const file = FILE_SELECT.files[0];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext) || file.type == "text/plain") {
    alert('File is not an archive.\nPlease archive the file first.');
    FILE_SELECT.value = "";
  } else if (file.size < 16*1024) {
    alert('Archive is too small, did you archive correct file?');
    FILE_SELECT.value = "";
  } else if (file.size > 1024**4) {
    alert("Archive is too big.\nAre you sure it's the correct file?\nAre you sure you compressed it?");
    FILE_SELECT.value = "";
  }
}

const UPLOAD_PROGRESS = new UploadProgress();
UPLOAD_PROGRESS.get_progress();

FILE_SUBMIT.onclick = () => {
  const _callback_on_finish = () => UPLOAD_PROGRESS.get_progress();
  const u = new Upload(_callback_on_finish)
  u.start();
}
