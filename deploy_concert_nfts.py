import json
from typing import List
from src.models.asset_configurations import *
from src.models.ticket_models import *
from src.blockchain_utils.credentials import get_account_with_name
import random
from src.services.asa_service import ASAService
from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer
import requests


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f)


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


def load_concert_tickets() -> List[ConcertTicket]:
    json_data = load_json('concert_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['concert_tickets']:
        tickets.append(ConcertTicket(**ticket_data))

    return tickets


acc_pk, acc_addr, _ = get_account_with_name("concert_company")
client = get_client()

APP_ID = 27661966
concert_tickets_dummy = load_concert_tickets()[:10]

concert_tickets = []
for i, t in enumerate(concert_tickets_dummy):
    new_t = t.copy(deep=True)
    new_t.asa_configuration.asa_id = None
    new_t.asa_configuration.asa_creator_address = acc_addr
    concert_tickets.append(new_t)
    save_json(f'data/concerts_ipfs/{i}.json', new_t.dict())

# TODO: Now we are manually deploying the folder to IPFS. We need to have an API that does that.

BASE_FOLDER_IPFS_URL = "https://gateway.pinata.cloud/ipfs/QmepNKHFeg8WjtBZviVtrzBfhVwhfrevLZnxuEHHJVd9Vw/"
# BASE_FOLDER_IPFS_URL = "https://ipfs.io/ipfs/QmQxNeQ4tqHRqpBnDsnGM9wecb8ndRTcpRbdxD9JEugmd6/"

ipfs_deployed_configurations = [f"{BASE_FOLDER_IPFS_URL}{i}.json" for i in range(10)]

asa_service = ASAService(creator_addr=acc_addr,
                         creator_pk=acc_pk,
                         tokility_dex_app_id=APP_ID,
                         client=client)

for i, ipfs_data_url in enumerate(ipfs_deployed_configurations):
    r = requests.get(ipfs_data_url)
    concert_ticket = ConcertTicket(**r.json())
    concert_ticket.asa_configuration.configuration_ipfs_url = ipfs_data_url
    concert_ticket.asa_configuration.asa_creator_address = acc_addr
    asa_id, tx_id = asa_service.create_asa(asa_configuration=concert_ticket.asa_configuration)
    print(asa_id, tx_id)

# indexer = get_indexer()
#
# response = indexer.search_assets(creator=acc_addr)
# print("Asset Name Info: " + json.dumps(response, indent=2, sort_keys=True))
#
# print(acc_addr)
#
# blockchain_tickets = []
# for asset in response["assets"]:
#     r = requests.get(asset["params"]["url"])
#     concert_ticket = ConcertTicket(**r.json())
#     concert_ticket.asa_configuration.asa_id = asset["index"]
#     blockchain_tickets.append(concert_ticket)
#
# print(blockchain_tickets)
#
