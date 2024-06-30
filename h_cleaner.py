import threading
from datetime import datetime, timedelta

import psutil

from h_debug import Loggers

LOGGER_MEMORY = Loggers.memory

MAX_SURVIVE_LOGS = timedelta(minutes=30)

def add_log_entry_memory(msg):
    _m = psutil.virtual_memory()
    available = _m.available / 1024 / 1024 / 1024
    percent = _m.percent
    LOGGER_MEMORY.info(f"{available:>5.2f} | {percent:>4.1f} | {msg}")

class MemoryCleaner:
    def __init__(self, OPENED_LOGS: dict) -> None:
        self.OPENED_LOGS = OPENED_LOGS
        self.cleaner_thread: threading.Thread = None

    def cleaner(self):
        add_log_entry_memory("STARTED")
        now = datetime.now()
        for report_id, report in dict(self.OPENED_LOGS).items():
            if now - report.last_access > MAX_SURVIVE_LOGS:
                del self.OPENED_LOGS[report_id]
                add_log_entry_memory(f"NUKED OLD | {report_id}")
        
        a = sorted(
            (report.last_access, report_id)
            for report_id, report in self.OPENED_LOGS.items()
        )
        while a and psutil.virtual_memory().percent > 75:
            _, report_id = a.pop(0)
            del self.OPENED_LOGS[report_id]
            add_log_entry_memory(f"NUKED MEM | {report_id}")
        
    def run(self):
        if self.cleaner_thread is not None and self.cleaner_thread.is_alive():
            return
        self.cleaner_thread = threading.Thread(target=self.cleaner)
        self.cleaner_thread.start()
