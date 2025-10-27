import re
import subprocess
from datetime import datetime
from functools import cached_property
from pathlib import Path
from sys import platform
from threading import RLock
from urllib.request import urlopen

THREAD_LOCK = RLock()
PATH = Path(__file__).resolve().parent
LINK_7Z_DL_PREFIX = "https://www.7-zip.org/a"
TABLE_BORDER = '-------------------'


class _File:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.url = f"{LINK_7Z_DL_PREFIX}/{self.file_name}"
        self.path = PATH / self.file_name

    def download(self):
        with urlopen(self.url) as response:
            self.path.write_bytes(response.read())

class _SevenZipLinux:
    executable = _File("7zz")
    portable = _File("7z2408-linux-x64.tar.xz")
    extract_command = ("tar", "-xf", portable.path, "-C", executable.path.parent, executable.file_name)
    required_downloads = [
        portable,
    ]

class _SevenZipWindows:
    executable = _File("7z.exe")
    portable = _File("7zr.exe")
    installer = _File("7z2408-x64.exe")
    extract_command = (portable.path, "e", installer.path, f"-o{executable.path.parent}", executable.file_name, "-y")
    required_downloads = [
        portable,
        installer,
    ]

class SevenZip:
    @property
    def path(self):
        self.download()
        return self.executable_path
    
    def download(self):
        if self._exists():
            return
        
        with THREAD_LOCK:
            if not self._exists():
                self._download()

    @property
    def _7z_type(self):
        try:
            return self.__7z_type
        except AttributeError:
            pass
        if platform.startswith("linux"):
            self.__7z_type = _SevenZipLinux
        elif platform == "win32":
            self.__7z_type = _SevenZipWindows
        else:
            raise NotImplementedError("Unsupported OS")
        return self.__7z_type
    
    @property
    def executable_path(self):
        return self._7z_type.executable.path

    def _exists(self):
        try:
            return self.executable_path.is_file()
        except (AttributeError, TypeError):
            return False

    def _download(self):
        try:
            self._download_required_files()
            self._extract_executable()
        finally:
            self._remove_downloaded_files()
        
        if not self._exists():
            raise RuntimeError("Somehow 7z is still missing")
        
    def _download_required_files(self):
        print("7Zip: Downloading")
        for file in self._7z_type.required_downloads:
            file.download()
    
    def _extract_executable(self):
        print("7Zip: Extracting")
        extract_command = self._7z_type.extract_command
        return_code = subprocess.call(extract_command)
        if return_code != 0:
            raise RuntimeError(f"Extraction failed | {extract_command}")
    
    def _remove_downloaded_files(self):
        for file in self._7z_type.required_downloads:
            if file.path.is_file():
                file.path.unlink()


class SevenZipLine:
    def __init__(
        self,
        time: str,
        attributes: str,
        size: str,
        compressed: str,
        path: str,
    ) -> None:
        try:
            self.datetime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.datetime = datetime(year=datetime.now().year, month=1, day=1)
            time = self.datetime.strftime("%Y-%m-%d %H:%M:%S")
        self.date_full_str = time
        self.timestamp = self.datetime.timestamp()
        self.date_str, self.time_str = time.replace(':', '-').split(' ', maxsplit=1)
 
        self.attributes = attributes
        self.size_bytes = int(size) if size else 0
        self.compressed_size_bytes = int(compressed) if compressed else 0
        self.file_name = path

    @classmethod
    def from_line(cls, line: str, column_widths: list[int]):
        columns = []
        for column_width in column_widths:
            column = line[:column_width]
            line = line[column_width:]
            columns.append(column.strip())
        
        if len(columns) != len(column_widths):
            raise ValueError
        
        columns.append(line.strip())
        return cls(*columns)

    def __repr__(self) -> str:
        self_name = self.__class__.__name__
        r = {
            "time": self.date_full_str,
            "attributes": self.attributes,
            "size": self.size_bytes,
            "compressed": self.compressed_size_bytes,
            "name": self.file_name,
        }
        r = ', '.join([f'{k}="{v}"' for k, v in r.items()])
        return f"{self_name}({r})"

    def __str__(self) -> str:
        self_name = self.__class__.__name__
        date = f"Date: {self.date_full_str}"
        size = f"Size (compressed): {self.size_bytes:,} ({self.compressed_size_bytes:,})"
        name = f"Name: {self.file_name}"
        return f"{self_name}({date}, {size}, {name})"

    def __eq__(self, other: 'SevenZipLine') -> bool:
        if not isinstance(other, SevenZipLine):
            return False
        return all((
            self.size_bytes == other.size_bytes,
            self.compressed_size_bytes == other.compressed_size_bytes,
            self.timestamp == other.timestamp,
        ))


class SevenZipArchiveInfo(SevenZip):
    def __init__(self, archive_path: Path) -> None:
        self.archive_path = archive_path

    def __eq__(self, other: 'SevenZipArchiveInfo') -> bool:
        if not isinstance(other, SevenZipArchiveInfo):
            return False
        return self.archive_id == other.archive_id

    def __bool__(self):
        try:
            return bool(self.archive_id)
        except Exception:
            return False
    
    @cached_property
    def archive_info(self):
        return list(self._to_parsed_lines())

    @cached_property
    def last_line(self):
        return self.archive_info[-1]

    @property
    def compressed_size(self):
        return self.last_line.compressed_size_bytes

    @property
    def uncompressed_size(self):
        return self.last_line.size_bytes

    @property
    def date_str(self):
        return self.last_line.date_str

    @cached_property
    def archive_id(self):
        if not self.archive_path.is_file():
            return None
        
        try:
            return '--'.join((
                self.last_line.date_str,
                self.last_line.time_str,
                f"{self.last_line.size_bytes:0>11}",
                f"{self.last_line.compressed_size_bytes:0>11}",
            ))
        except IndexError:
            return None
    
    def get_all_files_with_suffix(self, suffix):
        return [
            line
            for line in self.archive_info
            if line.file_name.endswith(suffix)
        ]

    def _get_raw_archive_info(self):
        cmd_list = [self.path, "l", self.archive_path]
        with subprocess.Popen(cmd_list, stdout=subprocess.PIPE) as p:
            try:
                return p.stdout.read().decode().splitlines()
            except Exception:
                pass
        return []
    
    @staticmethod
    def _get_column_widths(line: str):
        return [
            len(s)
            for s in re.findall("([ ]{0,2}-+)", line)
        ]
    
    def _to_parsed_lines(self):
        column_widths = None
        for line in self._get_raw_archive_info():
            if column_widths is None:
                if TABLE_BORDER in line:
                    column_widths = self._get_column_widths(line)
                    column_widths = column_widths[:4]
                continue
            
            if TABLE_BORDER in line:
                continue

            try:
                yield SevenZipLine.from_line(line, column_widths)
            except (IndexError, ValueError):
                pass


class SevenZipArchive(SevenZipArchiveInfo):
    _7z_pipe: subprocess.Popen = None

    def extract(self, extract_to: Path=None, file_name_to_extract: str=None):
        if extract_to is None:
            extract_to = self.archive_path.parent
        cmd = [self.path, 'e', self.archive_path, f'-o{extract_to}', "-y", "--"]
        if file_name_to_extract:
            cmd.append(file_name_to_extract)
        return subprocess.call(cmd)

    def append(self, file_path: Path, custom_mode: list[str]=None):
        cmd = [self.path, 'a', self.archive_path, file_path]
        if custom_mode:
            cmd.extend(custom_mode)
        return subprocess.call(cmd)
    
    def create(self, file_path: Path, custom_mode: list[str]=None):
        if self.archive_path.is_file():
            self.archive_path.unlink()
        return self.append(file_path, custom_mode)

    def read_file_into_stdout(self, file_line: SevenZipLine):
        file_name = file_line.file_name
        if "*" in file_name:
            file_name = f'"{file_name}"'
        cmd_list = [self.path, 'e', self.archive_path, "-so", "--", file_name]
        self._7z_pipe = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
        stdout = self._7z_pipe.stdout
        line = stdout.readline(5000)
        while line:
            yield line
            line = stdout.readline(5000)


def _test1():
    p = PATH.joinpath("temp", "test.7z")
    q = SevenZipArchiveInfo(p)
    print(q.path)
    for line in q.archive_info:
        print(line)

if __name__ == "__main__":
    _test1()
