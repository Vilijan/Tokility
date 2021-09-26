import json
from src.models.asset_configurations import ASAConfiguration, ASAInitialOfferingConfiguration, ASAEconomyConfiguration
from src.models.ticket_models import ConferenceTicket, Ticket
import random
from src.services.asa_service import ASAService
from src.blockchain_utils.credentials import get_client
import requests


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


config = load_json('config.json')

ticket_type = ["VIP", "Regular", "VIP", "Regular", "VIP", "Regular", "VIP", "Regular"]

ticket_duration = [1, 2, 3, 1, 2, 3, 1, 2]

for i in range(len(ticket_type)):
    asa_configuration = create_random_asa_configuration(creator_address=config['conference_company_address'],
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

deploy_to_ipfs = input('Manually deploy the data/conference_ipfs folder to ipfs. Press any button to continue. ')
print('-' * 50)
base_ipfs_url = input('Enter the base ipfs url of the folder')
print('-' * 50)

client = get_client()

# TODO: Now we are manually deploying the folder to IPFS. We need to have an API that does that.

ipfs_deployed_configurations = [f"{base_ipfs_url}{i}.json" for i in range(len(ticket_type))]

print(f'OPEN THIS IN BROWSER: {ipfs_deployed_configurations[0]}')
check_input = input(
    'Open this link in browser to verify whether it is a correct conference configuration. Press any button to continue. ')
print('-' * 50)

asa_service = ASAService(creator_addr=config['conference_company_address'],
                         creator_pk=config['conference_company_pk'],
                         tokility_dex_app_id=config['app_id'],
                         client=client)

for i, ipfs_data_url in enumerate(ipfs_deployed_configurations):
    r = requests.get(ipfs_data_url)
    concert_ticket = ConferenceTicket(**r.json())
    concert_ticket.asa_configuration.configuration_ipfs_url = ipfs_data_url
    print('-' * 50)
    asa_id, tx_id = asa_service.create_asa(asa_configuration=concert_ticket.asa_configuration)
    print(f'Utility token deployed with asa_id: {asa_id}')
