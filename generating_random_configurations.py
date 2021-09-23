from src.models.asset_configurations import *
from src.models.ticket_models import *
from src.blockchain_utils.credentials import get_account_with_name
import random
import json
from src.services.asa_service import ASAService
from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer

FOO_FIGHTERS_ADDRESS = get_account_with_name(account_name="foo_fighters")[1]


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f)


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


def micro_algo(algo):
    return int(algo * 1000000)


def create_random_asa_configuration(creator_address: str,
                                    asset_name: str,
                                    price_range: (float, float) = (3, 5.0),
                                    tokility_fee_range: (float, float) = (0.1, 0.2),
                                    max_sell_price_range: (float, float) = (20, 30.0),
                                    owner_fee_range: (float, float) = (0.2, 0.3),
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
                                 name: str):
    return ConcertTicket(asa_configuration=asa_configuration,
                         business_type=Ticket.BusinessType.concert,
                         issuer=issuer,
                         name=name,
                         type=random.choice(["VIP", "Standing", "Seating"]),
                         location=random.choice(["Amsterdam", "Skopje", "New York"]),
                         datetime=random.choice(["11.12.2021", "25.11.2022", "30.06.2022"]))


# random_configuration = create_random_asa_configuration(creator_address=FOO_FIGHTERS_ADDRESS,
#                                                        asset_name="Foo Fighters")
#
# concert_ticket = create_random_concert_ticket(random_configuration,
#                                               issuer="Foo Fighters",
#                                               name="Foo Fighters - Sonic Highways Tour")
#
# save_json('concert_ticket.json', concert_ticket.dict())

concert_ticket = ConcertTicket(**load_json("concert_ticket.json"))

ipfs_concert_json = "https://gateway.pinata.cloud/ipfs/QmdaPDebJhQBXV5vik8XHmtvX5gwCtvEQ6pzmk1HsZyorB"

concert_ticket.asa_configuration.configuration_ipfs_url = ipfs_concert_json

# Deploy the NFT


acc_pk, acc_addr, _ = get_account_credentials(7)
client = get_client()

APP_ID = 1234

asa_service = ASAService(creator_addr=acc_addr,
                         creator_pk=acc_pk,
                         tokility_dex_app_id=APP_ID,
                         client=client)


asa_id, tx_id = asa_service.create_asa(asa_configuration=concert_ticket.asa_configuration)

# Query the indexer

indexer = get_indexer()

response = indexer.search_assets(asset_id=asa_id)
print("Asset Name Info: " + json.dumps(response, indent=2, sort_keys=True))


import requests

concert_ticket_marina = requests.get("https://gateway.pinata.cloud/ipfs/QmdaPDebJhQBXV5vik8XHmtvX5gwCtvEQ6pzmk1HsZyorB")

concert_ticket_marina = ConcertTicket(**concert_ticket_marina.json())
