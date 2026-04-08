import threading
from datetime import datetime, timedelta
from time import perf_counter, sleep

import psutil

from h_debug import Loggers

LOGGER_MEMORY = Loggers.memory

MAX_SURVIVE_LOGS = timedelta(minutes=30)

def add_log_entry_memory(msg):
    _m = psutil.virtual_memory()
    available = _m.available / 1024 / 1024 / 1024
    percent = _m.percent
    LOGGER_MEMORY.info(f"{available:>5.2f}GB | {percent:>4.1f}% | {msg}")


class MemoryCleaner(threading.Thread):
    def __init__(self, OPENED_LOGS):
        super().__init__(daemon=True)
        self.OPENED_LOGS = OPENED_LOGS
        
    def cleaner(self):
        pc1 = perf_counter()

        now = datetime.now()
        reports = list(self.OPENED_LOGS)
        for report_id in reports:
            report = self.OPENED_LOGS[report_id]
            if now - report.last_access > MAX_SURVIVE_LOGS:
                del self.OPENED_LOGS[report_id]
                add_log_entry_memory(f"NUKED OLD | {report_id}")

        try:
            reports = sorted(self.OPENED_LOGS, key=lambda x: self.OPENED_LOGS[x].last_access)
        except Exception:
            reports = list(self.OPENED_LOGS)
            LOGGER_MEMORY.exception("sorted")

        for report_id in reports:
            if psutil.virtual_memory().percent < 90:
                break
            del self.OPENED_LOGS[report_id]
        
        add_log_entry_memory(f'{(perf_counter() - pc1)*1000:>10,.3f}ms | Openned reports: {len(self.OPENED_LOGS):>3} | MemoryCleaner done')

    def start(self):
        if self.is_alive():
            return
        try:
            return super().start()
        except Exception:
            LOGGER_MEMORY.exception("start")

    def run(self):
        while True:
            sleep(10)
            try:
                self.cleaner()
            except Exception:
                LOGGER_MEMORY.exception("main")
