# Uses regex to parse stats from tooltip of an item from evowow
# There is better way probably involving databases idk

import json
import re

from h_other import requests_get

URL_DOMAIN = "https://wotlk.evowow.com/"
HEADERS = {"User-Agent": "ItemParser/1.1; +uwu-logs.xyz"}
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
    item_url = f'{URL_DOMAIN}?item={id}'
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
