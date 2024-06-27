import json
import shutil
from enum import Enum
from pathlib import Path

import zstd

class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value
    def __repr__(self) -> str:
        return self.value

class DirNames(StrEnum):
    logs = "LogsDir"
    archives = "LogsRaw"
    top = "top"
    cache = "cache"
    static = "static"
    parsed = "parsed"
    uploads = "uploads"
    loggers = "_loggers"
    certificates = "__cert"

class FileNames(StrEnum):
    reports_allowed = "__allowed.txt"
    reports_private = "__private.txt"
    spell_icons_db = "x_spells_icons.json"

    cert_domain = "domain.cert.pem"
    cert_private = "private.key.pem"

    linux_7z_executable = "7zz"
    windows_7z_executable = "7z.exe"
    
    linux_7z_portable = "7z2301-linux-x64.tar.xz"
    windows_7z_portable = "7zr.exe"
    windows_7z_installer = "7z2301-x64.exe"


class CachePath:
    _cache = {}
    def __init__(self, path: 'PathExt', renew_callback, seconds=1) -> None:
        self.path = path
        self.renew_callback = lambda: renew_callback(path)
        self.cache_for = seconds

        self.mtime = 0.0
        self.cached_data = None

    def __call__(self):
        current_mtime = self.path.mtime
        if current_mtime > self.mtime:
            self.cached_data = self.renew_callback()
            self.mtime = current_mtime + self.cache_for
        return self.cached_data

    @classmethod
    def infrequent_changes(cls, func):
        def cache_inner(file: 'PathExt'):
            try:
                _func = cls._cache[file]
            except KeyError:
                _func = cls._cache[file] = cls(file, func)
            return _func()
        return cache_inner

    @classmethod
    def renew_after(cls, seconds):
        def cache_outer(func):
            def cache_inner(file: 'PathExt'):
                try:
                    _func = cls._cache[file]
                except KeyError:
                    _func = cls._cache[file] = cls(file, func, seconds)
                return _func()
            return cache_inner
        return cache_outer


class _PathExt(type(Path())):
    @property
    def mtime(self):
        return self.stat().st_mtime

    def backup_path(self, _main="mnt", _secondary="uwu-logs"):
        parts = list(self.parts)
        parts[1] = _main
        parts[2] = _secondary
        return PathExt(*parts)
    
    def cache_until_new_self(self, callback):
        return CachePath(self, callback)

    def copy_from_backup(self, _main="mnt", _secondary="uwu-logs"):
        backup_path = self.backup_path(_main=_main, _secondary=_secondary)
        if backup_path.is_dir():
            shutil.copytree(backup_path, self)


class _PathExtFiles(_PathExt):
    def _json(self) -> dict:
        if self.is_dir():
            raise ValueError("Can't parse directory as json.")
        
        return json.loads(self.read_text())

    @CachePath.infrequent_changes
    def json(self):
        return self._json()
    
    @CachePath.infrequent_changes
    def json_ignore_error(self):
        try:
            return self._json()
        except (FileNotFoundError, TypeError, json.decoder.JSONDecodeError):
            return {}
    
    def json_write(self, data, indent: int=None, condensed: bool=False):
        separators = (',', ':') if condensed else None
        j = json.dumps(data, ensure_ascii=False, indent=indent, separators=separators, default=sorted)
        self.write_text(j)

    @CachePath.infrequent_changes
    def text_lines(self):
        return self.read_text().splitlines()

    def zstd_write(self, data: bytes, compress_level=3):
        data = zstd.compress(data, compress_level)
        self.write_bytes(data)

    def zstd_read(self):
        data = self.read_bytes()
        data = zstd.decompress(data)
        return data.decode()


class _PathExtDirs(_PathExt):
    @property
    def files(self):
        for path in self.iterdir():
            if path.is_file():
                yield path
    
    @property
    def directories(self):
        for path in self.iterdir():
            if path.is_dir():
                yield path

    @staticmethod
    def get_names(iterable: list[_PathExt]):
        return (path.name for path in iterable)

    @staticmethod
    def get_stems(iterable: list[_PathExt]):
        return (path.stem for path in iterable)

    @CachePath.infrequent_changes
    def files_names(self):
        return sorted(self.get_names(self.files))

    @CachePath.infrequent_changes
    def files_stems(self):
        return sorted(self.get_stems(self.files))

    @CachePath.infrequent_changes
    def files_paths(self):
        return sorted(self.files)

    @CachePath.infrequent_changes
    def directories_names(self):
        return sorted(self.get_stems(self.directories))

    @CachePath.infrequent_changes
    def directories_paths(self):
        return sorted(self.directories)

    def new_child(self, name: str):
        _dir = self / name
        _dir.mkdir(exist_ok=True)
        return _dir

class PathExt(_PathExtDirs, _PathExtFiles):
    ...

class Directories(dict[str, PathExt]):
    __getattr__ = dict.__getitem__

    main = PathExt(__file__).parent
    logs = main / DirNames.logs
    archives = main / DirNames.archives
    top = main / DirNames.top
    cache = main / DirNames.cache
    static = main / DirNames.static
    parsed = main / DirNames.parsed
    loggers = main / DirNames.loggers
    certificates = main / DirNames.certificates
    
    uploads = main / DirNames.uploads
    uploaded = uploads / "uploaded"
    pending_archive = uploads / "0archive_pending"
    info_uploads = uploads / "0file_info"
    todo = uploads / "0todo"

    @classmethod
    def mkdirs(cls):
        for p in cls.__dict__.values():
            if isinstance(p, Path):
                p.mkdir(parents=True, exist_ok=True)

class Files(dict[str, PathExt]):
    __getattr__ = dict.__getitem__

    reports_allowed = Directories.main / FileNames.reports_allowed
    reports_private = Directories.main / FileNames.reports_private
    spell_icons_db = Directories.main / FileNames.spell_icons_db

    cert_domain = Directories.certificates / FileNames.cert_domain
    cert_private = Directories.certificates / FileNames.cert_private

Directories.mkdirs()


def __test1():
    # print(Files.m_time(Files.reports_private))
    # print(Directories.top)
    # print(Directories.main.json())
    # for x in Files.reports_allowed.iterdir():
    #     print(x)
    # for _ in range(3):
    #     print(DirDict.uploads.files_names()[:5])
    # print(DirDict.uploads.backup_path())
    # return
    # print(Directories.main)
    # print(Directories.main.backup_path())
    # print(Directories.main.mtime)
    # print(str(Files.reports_private))
    # print(Files.reports_private.mtime)
    # print(Files.reports_private.is_file())
    import time
    for i in range(100):
        print(Files.reports_private.text_lines()[-5:])
        time.sleep(1)
        print(i)
    # for i in range(3):
    #     print(Directories.main.directories_names())


if __name__ == "__main__":
    __test1()
