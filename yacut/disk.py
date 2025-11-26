import os
from pprint import pprint

import requests
from dotenv import load_dotenv

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
DISK_INFO_URL = f'{API_HOST}{API_VERSION}/disk/'

# Загрузить из .env значение токена.
load_dotenv()
DISK_TOKEN = os.environ.get('y0__xDMlfdFGKPjOyClw82lFY5XyeYJCqbY7GOk-mOpgijgwfW7')

# Словарь с заголовком авторизации.
AUTH_HEADERS = {
    'Authorization': f'OAuth {DISK_TOKEN}'
}

# Запрос.
response = requests.get(url=DISK_INFO_URL, headers=AUTH_HEADERS)

pprint(response.json())