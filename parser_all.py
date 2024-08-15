import json
from pathlib import Path
from threading import Thread

import logs_item_parser
import logs_ench_parser
from h_debug import Loggers
from h_other import requests_get

LOGGER = Loggers.missing

CACHE_DIRECTORY_NAME = "cache"
PATH = Path(__file__).resolve().parent
HEADERS = {"User-Agent": "ItemParser/1.1; +uwu-logs.xyz"}
ICON_URL_PREFIX = "https://wotlk.evowow.com/static/images/wow/icons/large"


DEBUG = True
DEBUG = False

class Loader:
    path: Path
    threads: dict[str, Thread] = {}

    type: str
    extension: str
    
    def __init__(self, id) -> None:
        self.id = id
    
    @property
    def path(self):
        try:
            return self.__path
        except AttributeError:
            self.__path = PATH / CACHE_DIRECTORY_NAME / self.type / f"{self.id}.{self.extension}"
            return self.__path
    
    def wait_for_thread(self):
        try:
            t = self.threads[self.id]
        except KeyError:
            return

        try:
            t.start()
        except RuntimeError:
            pass

        t.join()
        
        try:
            del self.threads[self.id]
        except KeyError:
            pass

    def download(self):
        ...
    def save(self, data):
        ...
    def save_wrap(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.save(data)
    
    def load(self):
        if self.path.is_file():
            LOGGER.debug(f"409 get is_file | {self.path}")
            return 409

        if self._can_create_new():
            t = self.threads[self.id] = Thread(target=self._parse_and_save)
            t.start()
        
        self.wait_for_thread()
        
        if self.path.is_file():
            LOGGER.debug(f"201 get created")
            return 201

        LOGGER.debug(f"500 get file missing")
        return 500

    def _parse_and_save(self):
        LOGGER.debug(f"parse_and_save | {self.path}")

        try:
            data = self.download()
        except Exception:
            LOGGER.exception("")
            return
        
        try:
            self.save_wrap(data)
        except Exception:
            LOGGER.exception("")
    
    def _can_create_new(self):
        return self.id not in self.threads or not self.threads[self.id].is_alive()


class Icon(Loader):
    type: str = "icon"
    extension: str = "jpg"
    
    def download(self):
        if DEBUG:
            p = PATH / CACHE_DIRECTORY_NAME / f"{self.type}_test" / f"{self.id}.{self.extension}"
            return p.read_bytes()
        url = f"{ICON_URL_PREFIX}/{self.id}.jpg"
        return requests_get(url, HEADERS).content

    def save(self, data):
        self.path.write_bytes(data)


class Item(Loader):
    type: str = "item"
    extension: str = "json"
    
    def download(self):
        if DEBUG:
            p = PATH / CACHE_DIRECTORY_NAME / f"{self.type}_test" / f"{self.id}.{self.extension}"
            return json.loads(p.read_text())
        return logs_item_parser.parse_item(self.id)

    def save(self, data):
        self.path.write_text(json.dumps(data))


class Ench(Loader):
    type: str = "enchant"
    extension: str = "json"
    
    def download(self):
        if DEBUG:
            p = PATH / CACHE_DIRECTORY_NAME / f"{self.type}_test" / f"{self.id}.{self.extension}"
            return json.loads(p.read_text())
        return logs_ench_parser.get_ench(self.id)

    def save(self, data):
        self.path.write_text(json.dumps(data))



def _test_1():
    from concurrent.futures import ThreadPoolExecutor
    
    items = ['17723', '17755', '17772', '1787']
    with ThreadPoolExecutor(4) as tpe:
        for x in items:
            tpe.submit(Item(x).load)
    
def _test_2():
    from concurrent.futures import ThreadPoolExecutor
    icons = [
        "inv_jewelry_trinket_03",
        "inv_jewelry_ring_83",
        "inv_kilt_cloth_02",
        "inv_misc_head_dragon_green",
        "inv_ore_feliron_01",
        "inv_staff_106",
        "inv_weapon_shortblade_101",
        "item_icecrownringa",
        "item_icecrownnecklaced",
        "spell_holy_summonlightwell",
    ]
    with ThreadPoolExecutor(4) as tpe:
        for x in icons:
            tpe.submit(Icon(x).load)
    
def _test_3():
    from concurrent.futures import ThreadPoolExecutor
    enchants = [
        3633, 3628, 3605, 2933, 2938, 3294, 2679, 3789, 3623, 3548, 3590, 3820, 3859,
        3520, 3810, 3832, 3758, 3604, 3520, 3719, 3606, 3560, 3520, 3834, 3520, 3563,
        3545, 3859, 3232, 3747, 3243, 3247, 3722, 2673, 2381, 3546, 3819, 3627, 3244,
    ]
    with ThreadPoolExecutor(4) as tpe:
        for x in enchants:
            tpe.submit(Ench(x).load)

if __name__ == "__main__":
    _test_1()
    _test_2()
    _test_3()
