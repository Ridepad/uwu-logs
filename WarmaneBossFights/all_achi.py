from typing import List
import requests
import concurrent.futures
from bs4 import BeautifulSoup
import json

URL = "http://armory.warmane.com/character/Lycanthrope/Lordaeron/achievements"
CATEGORIES = ['14861', '14862', '14863', '14777', '14778', '14779', '14780', '165', '14801', '14802', '14803', '14804', '14881', '14901', '15003', '14808', '14805', '14806', '14921', '14922', '14923', '14961', '14962', '15001', '15002', '15041', '15042', '170', '171', '172', '14864', '14865', '14866', '160', '187', '159', '163', '161', '162', '158', '14981', '156', '14941', '92', '96', '97', '95', '168', '169', '201', '155', '81']
ALL_ACHIEVEMENTS = {}

def get_categories():
    r = requests.get(URL).text
    soup = BeautifulSoup(r, features="html.parser")
    q: List[str] = []
    for t in ["data-subcategory", "data-category"]:
        for tag in soup.select(f"[{t}]"):
            q.append(tag.get(t))
    return [x for x in q if x.isdigit()]

def get_achievs(category: int):
    html = requests.post(URL, data={"category": category}).text
    html = json.loads(html)
    html = html['content']
    soup = BeautifulSoup(html, features="html.parser")
    ALL_ACHIEVEMENTS[category] = [x.get('id') for x in soup.find_all(class_="achievement")]

def get_all():
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        executor.map(get_achievs, CATEGORIES)
    print(ALL_ACHIEVEMENTS)

get_all()
# data-subcategory
# data-category