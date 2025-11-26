import os
import urllib

import requests
from dotenv import load_dotenv

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
DOWNLOAD_LINK_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'

load_dotenv()
DISK_TOKEN = os.environ.get('DISK_TOKEN')

AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}

response = requests.get(
    headers=AUTH_HEADERS,
    url=DOWNLOAD_LINK_URL, 
    params={'path': 'app:/filename.txt'}
)

link = response.json()['href']
print(link)
