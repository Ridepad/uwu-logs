import json

import requests
from bs4 import BeautifulSoup

CLASSES = [6, 11, 3, 8, 2, 5, 4, 7, 9, 1]
URL = "https://wotlk.evowow.com/?class="

SPELLS = {}

def __main(class_num):
    q = requests.get(f"{URL}{class_num}").text
    soup = BeautifulSoup(q, features="html.parser")
    try:
        z = soup.find(id="lv-generic").find_next_sibling()
    except AttributeError:
        return
    a = z.text.split("new Listview")[1]
    i1 = a.index('{"id"')
    i2 = a.index('],"name"')
    v = a[i1-1:i2+1]
    j = json.loads(v)
    SPELLS[CLASSES.index(class_num)] = {spell_data["id"]: spell_data["name"].replace('@', '') for spell_data in j}

for x in range(1,12):
    __main(x)

with open('DB_SPELLS.json', 'w') as f:
    json.dump(SPELLS, f, indent=2)
