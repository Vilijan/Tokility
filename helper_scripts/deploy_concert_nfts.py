import json
from typing import List
from src.models.asset_configurations import *
from src.models.ticket_models import *
from src.blockchain_utils.credentials import get_account_with_name
import random
from src.services.asa_service import ASAService
from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer
import requests

CONCERT_COMPANY_PK, CONCERT_COMPANY_ADDR, _ = get_account_with_name("concert_company")


def micro_algo(algo):
    return int(algo * 1000000)


def create_random_asa_configuration(creator_address: str,
                                    asset_name: str,
                                    price_range: (float, float) = (1.0, 5.0),
                                    tokility_fee_range: (float, float) = (0.125, 0.5),
                                    max_sell_price_range: (float, float) = (20.0, 30.0),
                                    owner_fee_range: (float, float) = (0.5, 2.0),
                                    reselling_end_date: int = 1668143794):
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


def create_random_concert_ticket(asa_configuration: ASAConfiguration,
                                 issuer: str,
                                 name: str,
                                 ipfs_image: str):
    return ConcertTicket(asa_configuration=asa_configuration,
                         business_type=Ticket.BusinessType.concert,
                         issuer=issuer,
                         ipfs_image=ipfs_image,
                         name=name,
                         type=random.choice(["VIP", "Standing", "Seating"]),
                         location=random.choice(["Amsterdam", "Skopje", "New York"]),
                         datetime=random.choice(["11.12.2021", "25.11.2022", "30.06.2022"]))


def generate_foo_fighters_ticket():
    random_asa_configuration = create_random_asa_configuration(creator_address=CONCERT_COMPANY_ADDR,
                                                               asset_name="Tokility Concert")

    return create_random_concert_ticket(asa_configuration=random_asa_configuration,
                                        issuer="Foo Fighters",
                                        name="Foo Fighters - Sonic Highways Tour",
                                        ipfs_image="https://gateway.pinata.cloud/ipfs/QmRSA7n5CHNwJW7njsBNYXfiT6adsLVwSJv623piky93CH/foo_fitghters_vip.png")


def generate_u2_ticket():
    random_asa_configuration = create_random_asa_configuration(creator_address=CONCERT_COMPANY_ADDR,
                                                               asset_name="Tokility Concert")

    return create_random_concert_ticket(asa_configuration=random_asa_configuration,
                                        issuer="U2",
                                        name="U2 - The Joshua Tree Tour",
                                        ipfs_image="https://gateway.pinata.cloud/ipfs/QmRSA7n5CHNwJW7njsBNYXfiT6adsLVwSJv623piky93CH/u2_vip.png")


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


client = get_client()

APP_ID = 28471564

for i in range(0, 10, 2):
    foo_fighters_ticket = generate_foo_fighters_ticket()
    u2_ticket = generate_u2_ticket()
    save_json(f'data/concerts_ipfs/{i}.json', foo_fighters_ticket.dict())
    save_json(f'data/concerts_ipfs/{i + 1}.json', u2_ticket.dict())

# TODO: Now we are manually deploying the folder to IPFS. We need to have an API that does that.

BASE_FOLDER_IPFS_URL = "https://gateway.pinata.cloud/ipfs/QmP8GJyGi3hg1c8FpMFMvPX81Nv2zhqWeb3pV88trG3Sxq/"
# BASE_FOLDER_IPFS_URL = "https://ipfs.io/ipfs/QmQxNeQ4tqHRqpBnDsnGM9wecb8ndRTcpRbdxD9JEugmd6/"

ipfs_deployed_configurations = [f"{BASE_FOLDER_IPFS_URL}{i}.json" for i in range(10)]

print(f'OPEN THIS IN BROWSER: {ipfs_deployed_configurations[0]}')

asa_service = ASAService(creator_addr=CONCERT_COMPANY_ADDR,
                         creator_pk=CONCERT_COMPANY_PK,
                         tokility_dex_app_id=APP_ID,
                         client=client)

for i, ipfs_data_url in enumerate(ipfs_deployed_configurations):
    r = requests.get(ipfs_data_url)
    concert_ticket = ConcertTicket(**r.json())
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
