import logs_core
from h_debug import running_time

class Timestamps(logs_core.Logs):
    @property
    def TIMESTAMPS(self):
        try:
            return self.__TIMESTAMPS
        except AttributeError:
            self.__TIMESTAMPS = self._get_timestamps()
            return self.__TIMESTAMPS
    
    def _get_timestamps(self):
        try:
            return self._read_timestamps()
        except Exception:
            return self._redo_timestamps()
    
    # @running_time
    def _read_timestamps(self):
        timestamp_data_file_name = self.relative_path("TIMESTAMP_DATA.json")
        return timestamp_data_file_name.json()
    
    @running_time
    def _redo_timestamps(self):
        timestamps = self._new_timestamps()
        timestamp_data_file_name = self.relative_path("TIMESTAMP_DATA.json")
        timestamp_data_file_name.json_write(timestamps)
        return timestamps
    
    def _new_timestamps(self):
        times: list[int] = []
        first_line = self.LOGS[0]
        i = first_line.index('.')
        last_minutes, last_seconds = int(first_line[i-5:i-3]), int(first_line[i-2:i])
        for n, line in enumerate(self.LOGS):
            try:
                minutes, seconds = int(line[i-5:i-3]), int(line[i-2:i])
            except ValueError:
                # date change or bugged line 
                i = line.index('.')
                try:
                    minutes, seconds = int(line[i-5:i-3]), int(line[i-2:i])
                except ValueError:
                    continue
            
            sec_diff = seconds - last_seconds
            min_diff = minutes - last_minutes

            if min_diff:
                if min_diff < 0:
                    min_diff += 60
                sec_diff += min_diff * 60
                last_minutes = minutes
            
            if sec_diff:
                times.extend([n]*sec_diff)
                last_seconds = seconds
            
        return times
