import requests
import json
import time

from headers_and_json import headers, json_data

response = requests.post(
    'https://api.investmoscow.ru/investmoscow/tender/v2/filtered-tenders/searchtenderobjects',
    headers=headers,
    json=json_data,
)

json_to_dict = json.loads(response.text)
apartments = json_to_dict["entities"]

def get_ids():
    time.sleep(1)
    Ids = []

    for a in apartments:
        tenders = a["tenders"][0]
        Id = tenders["id"]

        Ids.append(Id)
    return Ids
