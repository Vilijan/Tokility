import json
from typing import List
from src.models.asset_configurations import ASAConfiguration, ASAInitialOfferingConfiguration, ASAEconomyConfiguration
from src.models.ticket_models import ConferenceTicket, Ticket
from src.blockchain_utils.credentials import get_account_with_name
import random
from src.services.asa_service import ASAService
from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer
import requests

CONFERENCE_COMPANY_PK, CONFERENCE_COMPANY_ADDR, _ = get_account_with_name("conference_company")


def micro_algo(algo):
    return int(algo * 1000000)


def create_random_asa_configuration(creator_address: str,
                                    asset_name: str,
                                    price_range: (float, float) = (1.0, 5.0),
                                    tokility_fee_range: (float, float) = (0.125, 0.5),
                                    max_sell_price_range: (float, float) = (20.0, 30.0),
                                    owner_fee_range: (float, float) = (0.5, 2.0),
                                    reselling_end_date: int = 1637833854):
    reselling_allowed = 1 if random.randint(0, 10) > 3 else 0
    gifting_allowed = 1 if random.randint(0, 10) > 2 else 0

    def price(algo_range: (float, float)):
        return random.randint(micro_algo(algo_range[0]), micro_algo(algo_range[1]))

    initial_offering_config = ASAInitialOfferingConfiguration(asa_price=price(price_range),
                                                              tokiliy_fee=price(tokility_fee_range))
    economy_configuration = ASAEconomyConfiguration(max_sell_price=price(max_sell_price_range),
                                                    owner_fee=price(owner_fee_range),
                                                    reselling_allowed=reselling_allowed,
                                                    reselling_end_date=reselling_end_date,
                                                    gifting_allowed=gifting_allowed)

    return ASAConfiguration(asa_creator_address=creator_address,
                            unit_name="TOK",
                            asset_name=asset_name,
                            initial_offering_configuration=initial_offering_config,
                            economy_configuration=economy_configuration)


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


ticket_type = ["VIP", "Regular", "VIP", "Regular", "VIP", "Regular", "VIP", "Regular"]

ticket_duration = [1, 2, 3, 1, 2, 3, 1, 2]

for i in range(len(ticket_type)):
    asa_configuration = create_random_asa_configuration(creator_address=CONFERENCE_COMPANY_ADDR,
                                                        asset_name="Decipher")

    conference_ticket = ConferenceTicket(asa_configuration=asa_configuration,
                                         business_type=Ticket.BusinessType.conference,
                                         issuer="Algorand Foundation",
                                         ipfs_image="https://gateway.pinata.cloud/ipfs/Qmf1JuhhG7qYBtQkPd2RtECWnaZsJvS2aSKWEPPHfypTwf/conference_vip.png",
                                         datetime="29.11.2021",
                                         type=ticket_type[i],
                                         name="Decipher - The Future is Built on Algorand",
                                         duration=str(ticket_duration[i]))

    save_json(f'data/conference_ipfs/{i}.json', conference_ticket.dict())

client = get_client()

APP_ID = 28715729

# TODO: Now we are manually deploying the folder to IPFS. We need to have an API that does that.

BASE_FOLDER_IPFS_URL = "https://gateway.pinata.cloud/ipfs/QmTaE1rkTetBX196cnFqwFc5MdPL3aS6Ffx8GcyngD4vrr/"

ipfs_deployed_configurations = [f"{BASE_FOLDER_IPFS_URL}{i}.json" for i in range(len(ticket_type))]

print(f'OPEN THIS IN BROWSER: {ipfs_deployed_configurations[0]}')

asa_service = ASAService(creator_addr=CONFERENCE_COMPANY_ADDR,
                         creator_pk=CONFERENCE_COMPANY_PK,
                         tokility_dex_app_id=APP_ID,
                         client=client)

for i, ipfs_data_url in enumerate(ipfs_deployed_configurations):
    r = requests.get(ipfs_data_url)
    concert_ticket = ConferenceTicket(**r.json())
    concert_ticket.asa_configuration.configuration_ipfs_url = ipfs_data_url
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
