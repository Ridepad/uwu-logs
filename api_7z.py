import re
import subprocess
from datetime import datetime
from pathlib import Path
from sys import platform

PATH = Path.cwd()
LINK_7Z_DL_PREFIX = "https://www.7-zip.org/a"
TABLE_BORDER = '-------------------'

class _SevenZipLinux:
    __executable = "7zz"
    __portable = "7z2301-linux-x64.tar.xz"
    executable_path = PATH / __executable
    dl_cmd = (
        ('apt', 'install', 'wget'),
        ('wget', f'{LINK_7Z_DL_PREFIX}/{__portable}'),
        ('tar', '-xf', __portable, __executable),
        ('rm', __portable),
    )

class _SevenZipWindows:
    __executable = "7z.exe"
    __portable = "7zr.exe"
    __installer = "7z2301-x64.exe"
    executable_path = PATH / __executable
    dl_cmd = (
        ('powershell', '-command', 'wget', f'{LINK_7Z_DL_PREFIX}/{__portable}', '-O', __portable),
        ('powershell', '-command', 'wget', f'{LINK_7Z_DL_PREFIX}/{__installer}', '-O', __installer),
        (__portable, 'e', __installer, __executable, '-y'),
        ('rm', __portable),
        ('rm', __installer),
    )

class SevenZip:
    @property
    def path(self):
        if not self._exists():
            self._download()
        return self.executable_path
    
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
        return self._7z_type.executable_path
    
    @property
    def dl_cmd(self):
        return self._7z_type.dl_cmd

    def _exists(self):
        try:
            return self.executable_path.is_file()
        except (AttributeError, TypeError):
            return False

    def _download(self):
        for command in self.dl_cmd:
            if command[0] == "rm":
                file = PATH / command[1]
                file.unlink()
                continue
            
            return_code = subprocess.call(command)
            if return_code != 0:
                raise RuntimeError(f"Download script ran with errors. Last command: {command}")

        if not self._exists():
            raise RuntimeError("Somehow 7z is still missing")


class SevenZipLine:
    def __init__(
        self,
        time: str,
        attributes: str,
        size: str,
        compressed: str,
        path: str,
    ) -> None:
        self.date_full_str = time
        self.date_str, self.time_str = time.replace(':', '-').split(' ', maxsplit=1)
        self.attributes = attributes
        self.datetime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        self.timestamp = self.datetime.timestamp()
        self.size_bytes = int(size)
        self.compressed_size_bytes = int(compressed)
        self.file_name = path

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
        size = f"Size (compressed): {self.size_bytes} ({self.compressed_size_bytes})"
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
    
    @property
    def archive_info(self):
        try:
            return self.__archive_info
        except AttributeError:
            pass
        
        self.__archive_info = list(self._to_parsed_lines())
        return self.__archive_info

    @property
    def compressed_size(self):
        return self.archive_info[-1].compressed_size_bytes

    @property
    def uncompressed_size(self):
        return self.archive_info[-1].size_bytes

    @property
    def date_str(self):
        return self.archive_info[-1].date_str

    @property
    def archive_id(self):
        if not self.archive_path.is_file():
            return None
        try:
            a = self.archive_info[-1]
            i = [
                a.date_str,
                a.time_str,
                f"{a.size_bytes:0>11}",
                f"{a.compressed_size_bytes:0>11}",
            ]
            return '--'.join(i)
        except IndexError:
            pass
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
        return None
    
    @staticmethod
    def _make_re_string(line: str):
        '''define regex to generate column parser'''
        columns_lengths = [
            len(s)
            for s in re.findall("(-+ +)", line)
        ]
        column_regex = "(.{{{}}})"
        columns = len(columns_lengths)
        columns_regex = column_regex * columns + "(.+)"
        # (.{{{}}})(.{{{}}})(.{{{}}})(.{{{}}})(.+)
        columns_regex = columns_regex.format(*columns_lengths)
        # (.{20})(.{6})(.{13})(.{14})(.+)
        return columns_regex
    
    def _to_parsed_lines(self):
        re_string = None
        for line in self._get_raw_archive_info():
            if not re_string:
                if TABLE_BORDER in line:
                    re_string = self._make_re_string(line)
                continue
            
            if TABLE_BORDER in line:
                continue

            z = re.findall(re_string, line)[0]
            z = [x.strip() for x in z]
            try:
                yield SevenZipLine(*z)
            except ValueError:
                pass


class SevenZipArchive(SevenZipArchiveInfo):
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



def _test1():
    # q = SevenZip()
    # print(q)
    q = SevenZipArchiveInfo(r"F:\Python\uwulogs\uploads\1\46.247.212.239--24-03-12--09-54-04--11_03_202_Marr_n_txt.zip")
    print(q.path)
    for line in q.archive_info:
        print(line)

if __name__ == "__main__":
    _test1()
