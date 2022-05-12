import json
import os
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import constants

HEADERS = {'User-Agent': 'tst3'}

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
FIREFOX = os.path.join(DIR_PATH, 'geckodriver.exe')
DL_LINKS = os.path.join(DIR_PATH, "legacy_dl_links.json")

DEFAULT_DL = "https://legacyplayers.com/uploads/upload_0.zip"
KEYS = ('raid_name', 'mode', 'guild', 'server', 'start', 'end')
URLS = {
    "icc_10": "https://legacyplayers.com/tiny_url/6946",
    "icc_10h": "https://legacyplayers.com/tiny_url/6945",
    "icc_25": "https://legacyplayers.com/tiny_url/6944",
    "icc_25h": "https://legacyplayers.com/tiny_url/6943",
}

def name_from_key(key):
    return f'legacy_{key}_data.json'

class element_attribute_changed(object):
    def __init__(self, locator, first_value, attribute):
        self.locator = locator
        self.first_value = first_value
        self.attribute = attribute

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        new_value = element.get_attribute(self.attribute)
        return new_value != self.first_value

class Parser:
    def __enter__(self):
        print('enter method called')
        self.DRIVER = webdriver.Firefox(executable_path=FIREFOX)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        print('exit method called')
        print(exc_traceback)
        self.DRIVER.quit()

    def get_dl_link(self, url):
        print(url)
        self.DRIVER.get(url)
        locator = (By.CSS_SELECTOR, ".left_nav_bar > a")

        element = WebDriverWait(self.DRIVER, 10).until(
            EC.presence_of_element_located(locator)
        )
        current_link = element.get_attribute('href')
        print(current_link)

        if current_link == DEFAULT_DL:
            WebDriverWait(self.DRIVER, 10).until(
                element_attribute_changed(locator, current_link, 'href')
            )
            element = self.DRIVER.find_element(*locator)
            current_link = element.get_attribute('href')
            print(current_link)
        
        return current_link

    def get_all_dl_links(self, key):
        fname = name_from_key(key)
        j: list[dict[str, str]] = constants.json_read(fname)
        old_links = constants.json_read(DL_LINKS)
        links = {x['link'] for x in j}
        new_links = {}
        try:
            for url in links:
                if url in old_links or url in new_links:
                    continue

                for _ in range(2):
                    try:
                        new_links[url] = self.get_dl_link(url)
                        sleep(1)
                        break
                    except TimeoutException:
                        continue

        finally:
            if new_links:
                old_links.update(new_links)
                constants.json_write(DL_LINKS, old_links)
    

    def check_if_ready(self):
        for _ in range(20):
            try:
                row = self.DRIVER.find_element(By.TAG_NAME, 'bodyrow')
                WebDriverWait(self.DRIVER, .5).until(
                    EC.staleness_of(row)
                )
            except TimeoutException:
                return True

        return False

    def get_new_table_data(self):
        data = []
        rows = self.DRIVER.find_elements(By.TAG_NAME, "bodyrow")
        for row in rows:
            rdata = row.get_attribute('innerText').split('\n')
            ddata = dict(zip(KEYS, rdata))
            a = row.find_element(By.TAG_NAME, 'a')
            ddata['link'] = a.get_attribute('href')
            data.append(ddata)
        return data

    def pve_gen(self, url):
        self.DRIVER.get(url)
        WebDriverWait(self.DRIVER, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "bodyrow"))
        )

        NEXT_PAGE_BUTTON = self.DRIVER.find_element(By.CLASS_NAME, 'nextPage')
        PAGE_TEXT = self.DRIVER.find_element(By.CSS_SELECTOR, '.previousPage + div')
        
        last_page_text = PAGE_TEXT.get_attribute('innerText')
        
        for page_n in range(1, 10000):
            if self.check_if_ready():
                print('[pve_parse] Done with page:', page_n)
                yield self.get_new_table_data()
            else:
                print('[pve_parse] Skipped page:', page_n)

            NEXT_PAGE_BUTTON.click()
            new_page_text = PAGE_TEXT.get_attribute('innerText')
            if new_page_text == last_page_text:
                print("[pve_parse] Reached end!")
                break
            
            last_page_text = new_page_text


    def pve_parse(self, url: str, all_data: list):
        new_data = []
        try:
            for page_data in self.pve_gen(url):
                dublicates = 0
                for row_data in reversed(page_data):
                    if row_data in all_data:
                        dublicates += 1
                    else:
                        new_data.append(row_data)
                if dublicates > 4:
                    print("[pve_parse] Reached dublicates!")
                    break
        finally:
            all_data.extend(new_data)
            return all_data

    def pve_parse_main(self, key):
        url = URLS[key]
        fname = name_from_key(key)
        all_data = constants.json_read(fname)
        all_data = self.pve_parse(url, all_data)
        with open(fname, 'w') as f:
            json.dump(all_data, f, indent=2)

def main():
    key = 'icc_25h'
    do_all = False
    do_all = True
    with Parser() as parser:
        if do_all:
            for key in URLS:
                print(key)
                parser.pve_parse_main(key)
                parser.get_all_dl_links(key)
        else:
            # parser.pve_parse_main(key)
            parser.get_all_dl_links(key)

if __name__ == "__main__":
    main()
