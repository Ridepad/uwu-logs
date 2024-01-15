# Uses regex to parse stats from tooltip of an item from evowow
# There is better way probably involving databases idk


import json
import re
import time
from pathlib import Path
from threading import Thread

import requests


PATH = Path(__file__).parent
HEADERS = {"User-Agent": "ItemParser/1.1; +uwu-logs.xyz"}
ICON_URL_PREFIX = "https://wotlk.evowow.com/static/images/wow/icons/large"
STATS_DICT = {
    0: "armor",
    35: "resilience rating",
    45: "spell power",
    38: "attack power",
    36: "haste rating",
    32: "critical strike rating",
    31: "hit rating",
    37: "expertise rating",
    44: "armor penetration rating",
    12: "defense rating",
    13: "dodge rating",
    14: "parry rating",
    15: "shield block",
    43: "mp5",
    47: "spell penetration",
    7: "stamina",
    3: "agility",
    4: "strength",
    5: "intellect",
    6: "spirit",
}

done: dict[str, dict] = {}
threads: dict[str, Thread] = {}

def requests_get(page_url, headers, timeout=2, attempts=3):
    for _ in range(attempts):
        try:
            page = requests.get(page_url, headers=headers, timeout=timeout, allow_redirects=False)
            if page.status_code == 200:
                return page
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            time.sleep(2)
    
    # LOGGER.error(f"Failed to load page: {page_url}")
    return None


def get_raw_stats(html: str):
    i_start = html.index("tooltip_enus")
    raw_stats = html[i_start:]
    return raw_stats[:raw_stats.index("_[")]

def get_prim_stats(html: str):
    return re.findall("-stat(\d)[^\d]+(\d{1,3})", html)

def get_add_stats(html: str):
    return re.findall("Equip: [IR][a-z]+[^%\d]+(\d\d)\D+(\d{1,3})", html)

def get_armor(html: str):
    armor_value = re.findall('(\d+) Armor<', html)
    if not armor_value:
        return []
    armor_value = armor_value[0]
    if 'tooltip_armorbonus' in html:
        armor_bonus = re.findall('tooltip_armorbonus, (\d+)', html)[0]
        armor_value = int(armor_value) - int(armor_bonus)*2
    return [[0, armor_value]]

def get_stats(html: str):
    stats = get_prim_stats(html) + get_add_stats(html) + get_armor(html)
    stats = [[int(x), int(y)] for x, y in stats]
    return [
        [STATS_DICT[x], y]
        for x, y in stats if x in STATS_DICT
    ]

def get_sockets(html: str):
    colors = re.findall("socket-([a-z]{3,6})", html)
    return [
        colors.count(color)
        for color in ("red", "yellow", "blue")
    ]

def get_socket_bonus(html: str):
    ench_id = re.findall("Socket Bonus.+?enchantment=(\d+)", html)[0]
    value, stat = re.findall("Socket Bonus:.+?(\d{1,2}) (.+?)<", html)[0]
    if '5' in stat:
        stat = "mp5"
    return {
        "stats": [[stat.lower(), int(value)]],
        "id": int(ench_id),
        "string": f"+{value} {stat}",
    }

def get_additional_text(html: str):
    def format(line):
        line = re.sub("<[^>]+>", "", line)
        if '%' in line:
            line = re.sub("\(.+?\)", "", line)
        return line.replace("&nbsp;", "")
    additional_text = re.findall("(Equip: [^IR].+?)...span>", html, re.S)
    additional_text.extend(re.findall("(Use: .+?)...span>", html, re.S))
    return [
        format(line)
        for line in additional_text
    ]

def parse_item(id):
    item_url = f'https://wotlk.evowow.com/?item={id}'
    item_raw = requests_get(item_url, HEADERS).text
    item_stats = re.findall('g_items[^{]+({.+?})', item_raw)
    item: dict = json.loads(item_stats[0])
    # item = {'quality': 4, 'icon': 'inv_mace_115', 'name_enus': 'Royal Scepter of Terenas II'}
    item["name"] = item.pop('name_enus')
    # item = {'quality': 4, 'icon': 'inv_mace_115', 'name': 'Royal Scepter of Terenas II'}
    try:
        item["ilvl"] = re.findall('Level: (\d{1,3})', item_raw)[0]
    except IndexError:
        return item

    raw_stats = get_raw_stats(item_raw)

    item["heroic"] = 'Heroic' in raw_stats

    slot = re.findall('td>([A-z -]+?)<', raw_stats)[0]
    if slot == 'Head':
        item["meta"] = 'socket-meta' in raw_stats
    item["slot"] = slot

    _type = re.findall('th>([A-z -]+?)<', raw_stats)
    if not _type:
        _type = re.findall('-asc\d-->([^<]+)', raw_stats)
    if _type:
        item["type"] = _type[0]
    
    item["stats"] = get_stats(raw_stats)
    item["sockets"] = get_sockets(raw_stats)
    if sum(item["sockets"]):
        item["socketbonus"] = get_socket_bonus(raw_stats)

    additional_text = get_additional_text(raw_stats)
    if additional_text:
        item["add_text"] = additional_text
    return item

### Used to assure single instance of parser

def wait_for_thread(t: Thread):
    try:
        t.start()
    except RuntimeError:
        pass

    t.join()

done: set[str] = set()
def ensure_single_request(f):
    threads: dict[str, Thread] = {}
    
    def parse_and_save_inner(id):
        print('parse_and_save_inner', id)
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

@ensure_single_request
def parse_and_save(id: str):
    p = (PATH / "cache" / "item" / id).with_suffix(".json")
    if p.is_file():
        done.add(id)
        return True
    
    try:
        data = parse_item(id)
    except Exception:
        return False
    
    try:
        p.write_text(json.dumps(data))
    except Exception:
        return False
    
    done.add(id)
    return True

def dl_icon(icon_name):
    url = f"{ICON_URL_PREFIX}/{icon_name}.jpg"
    return requests_get(url, HEADERS).content

@ensure_single_request
def save_icon(icon_name: str):
    p = (PATH / "cache" / "icon" / icon_name).with_suffix(".jpg")
    if p.is_file():
        done.add(icon_name)
        return True
    
    try:
        icon = dl_icon(icon_name)
    except Exception:
        return False
    
    try:
        p.write_bytes(icon)
    except Exception as e:
        print(e)
        return False
    
    done.add(icon_name)
    return True


def __test():
    from concurrent.futures import ThreadPoolExecutor
    
    # g = ['17723', '17755', '17772', '1787']
    # with ThreadPoolExecutor(4) as tpe:
    #     tpe.map(ensure_single_instance, g)
    q = save_icon("inv_jewelry_necklace_48")
    print(q)
if __name__ == "__main__":
    __test()
