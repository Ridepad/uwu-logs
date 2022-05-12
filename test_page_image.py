import os
import threading
import requests

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
STATIC = os.path.join(DIR_PATH, "static")
PAGES = os.path.join(STATIC, "pages")

PAGE_DOWNLOAD_THREADS = {}

def get_image_thread(url: str, report_id: str):
    u = f'https://render-tron.appspot.com/screenshot/{url}'
    response = requests.get(u, stream=True)
    print(response.status_code)
    if response.status_code != 200: return
    print(url)
    print(report_id, 'downloading page image...')
    path = os.path.join(PAGES, f"{report_id}.jpg")
    with open(path, 'wb') as file:
        for chunk in response:
            file.write(chunk)
    print(report_id, 'done!')


def get_image(base_url: str):
    if 'reports' not in base_url: return
    if 'ngrok' not in base_url: return

    _url = base_url.split('/')
    core = _url[2]
    report_id = _url[4]

    if report_id in PAGE_DOWNLOAD_THREADS:
        return PAGE_DOWNLOAD_THREADS[report_id]
    path = os.path.join(PAGES, f"{report_id}.jpg")
    if os.path.isfile(path): return

    # url = 'http://de27-5-29-61-156.eu.ngrok.io/reports/21-11-24--21-00--Safiyah/'
    url = f"http://{core}/reports/{report_id}"
    print(url)

    t = threading.Thread(target=get_image_thread, args=(url, report_id))
    t.start()
    PAGE_DOWNLOAD_THREADS[report_id] = t
    return t


def post_image(report_id):
    core = 'de27-5-29-61-156.eu.ngrok.io'
    path = os.path.join(PAGES, f"{report_id}.jpg")
    if os.path.isfile(path): return
    url = f"http://{core}/reports/{report_id}/"
    print(url)
    data = {
        'quality': 100,
        'clip ': {
            'width': 1920,
            'height': 600,
        }
    }
    url = "http://de27-5-29-61-156.eu.ngrok.io/reports/21-11-24--21-00--Safiyah/"
    u = f'https://render-tron.appspot.com/screenshot/{url}'
    u = "https://render-tron.appspot.com/screenshot/http://de27-5-29-61-156.eu.ngrok.io/reports/21-11-24--21-00--Safiyah/?width=1920&height=1080"
    # response = requests.post(u, stream=True, data=data)
    response = requests.get(u, stream=True)
    print(report_id, 'downloading page image...')
    with open(path, 'wb') as file:
        for chunk in response:
            file.write(chunk)
    print(report_id, 'done!')


post_image('21-11-24--21-00--Safiyah')