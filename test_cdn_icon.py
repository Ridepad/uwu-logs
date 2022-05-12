import requests

import constants

@constants.running_time
def get_icon(url):
    requests.get(url).content

cdns = [
    'http://cdn.cavernoftime.com/wotlk/icons/large/',
    'https://wow.zamimg.com/images/wow/icons/large/',
    'https://wotlk.evowow.com/static/images/wow/icons/large/',
]

icon = 'inv_gauntlets_62.jpg'

for x in cdns:
    url = x + icon
    get_icon(url)
