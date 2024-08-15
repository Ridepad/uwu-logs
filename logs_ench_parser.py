# Parses stats of enchants and gems.
# BeautifulSoup is like document.querySelector() in js

import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from h_other import requests_get

URL_DOMAIN = "https://wotlk.evowow.com/"
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
    url = f"{URL_DOMAIN}?enchantment={id}"
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
