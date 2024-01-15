# Parses stats of enchants and gems.
# BeautifulSoup is like document.querySelector() in js


import json
import re
import time
from pathlib import Path
from threading import Thread

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

PATH = Path(__file__).parent
HEADERS = {'User-Agent': "EnchParser/1.1; +uwu-logs.xyz"}
BASE_STATS = {'stamina', 'intellect', 'spirit', 'strength', 'agility'}
SHORT_STATS = {
    'armorpenrtng': 'armor penetration rating',
    'resirtng': 'resilience rating',
    'hitrtng': 'hit rating',
    'splpwr': 'spell power',
    'atkpwr': 'attack power',
    'hastertng': 'haste rating',
    'critstrkrtng': 'critical strike rating',
    'exprtng': 'expertise rating',
    'defrtng': 'defense rating',
    'dodgertng': 'dodge rating',
    'parryrtng': 'parry rating',
    'manargn': 'mp5',
    'healthrgn': 'hp5',
    'sta': 'stamina',
    'int': 'intellect',
    'spi': 'spirit',
    'str': 'strength',
    'agi': 'agility',
}

def requests_get(page_url, headers, timeout=2, attempts=3):
    for _ in range(attempts):
        print(timeout)
        try:
            page = requests.get(page_url, headers=headers, timeout=timeout, allow_redirects=False)
            if page.status_code == 200:
                return page
        except requests.exceptions.ReadTimeout:
            timeout = timeout + 2
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    
    # LOGGER.error(f"Failed to load page: {page_url}")
    return None

def get_value(text: str):
    try:
        if text and "%" not in text:
            s: str = re.findall("(\d{1,3})", text)[0]
            return s
    except IndexError:
        pass
    return None

def parse_each(td: Tag):
    small_tag = td.find("small")
    if small_tag is None:
        return None

    stats: list[str]
    value = small_tag.text
    stat_tag = small_tag.find_next_sibling()
    if stat_tag is None:
        if not td.text or "Defense: (Physical)" not in td.text:
            return None
        stats = ["Armor"]
    elif not stat_tag.get("type"):
        value = td.find('a').text
        stats = re.findall("[A-z ]+", value)
    else:
        stats = re.findall("\['([a-z]+)", stat_tag.text)
    
    value = get_value(value)
    if value is not None and len(stats) > 0:
        stat = stats[0].lower().replace('increased', '').strip()
        return SHORT_STATS.get(stat, stat), int(value)

    return None

def get_enchant_names(soup: BeautifulSoup) -> tuple[str, str]:
    n0 = soup.find("title").text.split(' - ')[0]
    n1 = soup.find(id="topbar").find_next_sibling().text
    n1 = re.findall('name_enus":"([^"]+)', n1)[1]
    return n0, n1
    
def get_ench(id):
    url = f"https://wotlk.evowow.com/?enchantment={id}"
    ench_raw = requests_get(url, HEADERS).text
    # print(ench_raw)
    soup = BeautifulSoup(ench_raw, features="html.parser")
    stats_table = soup.find(id="spelldetails")
    # print(stats_table)
    stats = [
        parse_each(td)
        for td in stats_table.find_all("td")
    ]
    stats = [x for x in stats if x is not None]
    names = get_enchant_names(soup)
    for x in names:
        if "all stats" in x.lower():
            stats.extend((s, int(get_value(x))) for s in BASE_STATS)
    return {
        "names": names,
        "stats": stats
    }


### Used to assure single instance of parser

def wait_for_thread(t: Thread):
    try:
        t.start()
    except RuntimeError:
        pass

    t.join()

done: set[str] = set()
def ensure_single_instance(f):
    threads: dict[str, Thread] = {}
    
    def parse_and_save_inner(id):
        try:
            id = str(id)
        except Exception:
            return 400

        if id in done:
            return 200
        
        if id not in threads:
            threads[id] = Thread(target=f, args=(id, ))
        
        wait_for_thread(threads[id])
        if id in done:
            return 201

        return 500
    
    return parse_and_save_inner

@ensure_single_instance
def parse_and_save(id: str):
    p = (PATH / "cache" / "enchant" / id).with_suffix(".json")
    if p.is_file():
        done.add(id)
        return True
    
    try:
        data = get_ench(id)
    except Exception:
        return False
    
    try:
        p.write_text(json.dumps(data))
    except Exception:
        return False
    
    done.add(id)
    return True


def __test():
    from concurrent.futures import ThreadPoolExecutor
    
    g = [
        3633, 3628, 3605, 2933, 2938, 3294, 2679, 3789, 3623, 3548, 3590, 3820, 3859,
        3520, 3810, 3832, 3758, 3604, 3520, 3719, 3606, 3560, 3520, 3834, 3520, 3563,
        3545, 3859, 3232, 3747, 3243, 3247, 3722, 2673, 2381, 3546, 3819, 3627, 3244,
    ]
    q = parse_and_save(g[0])
    print(q)
    with ThreadPoolExecutor(4) as tpe:
        tpe.map(parse_and_save, g)

if __name__ == "__main__":
    __test()
