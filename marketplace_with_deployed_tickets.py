from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer, get_account_with_name
from src.models.asset_configurations import ASAConfiguration, ASAInitialOfferingConfiguration, ASAEconomyConfiguration
from src.services.asa_service import ASAService
from src.services.tokility_dex_service import TokilityDEXService
import json
from typing import List
from src.models.ticket_models import ConcertTicket, Ticket
import requests
import base64
import time
from src.models.asset_sale_offer import SaleOffer

acc_pk, acc_addr, _ = get_account_credentials(1)
buyer_pk, buyer_add, _ = get_account_credentials(2)
buyer_2_pk, buyer_2_add, _ = get_account_credentials(3)
concert_company_pk, concert_company_addr, _ = get_account_with_name("concert_company")
client = get_client()


def algo(micro_algo) -> int:
    return int(micro_algo * 1000000)


def load_concert_tickets_blockchain() -> List[ConcertTicket]:
    indexer = get_indexer()

    response = indexer.search_assets(creator=concert_company_addr)
    blockchain_tickets: List[ConcertTicket] = []

    for asset in response["assets"]:
        r = requests.get(asset["params"]["url"])
        concert_ticket = ConcertTicket(**r.json())
        concert_ticket.asa_configuration.asa_id = asset["index"]
        concert_ticket.asa_configuration.asa_creator_address = concert_company_addr
        blockchain_tickets.append(concert_ticket)

    return blockchain_tickets


# Initialization of Tokility services.
tokility_dex_service = TokilityDEXService(app_creator_addr=acc_addr,
                                          app_creator_pk=acc_pk,
                                          client=client,
                                          app_id=27629360)

concert_company_asa_service = ASAService(creator_addr=concert_company_addr,
                                         creator_pk=concert_company_pk,
                                         tokility_dex_app_id=tokility_dex_service.app_id,
                                         client=client)

CLAWBACK_ADDRESS = concert_company_asa_service.clawback_address
CLAWBACK_ADDRESS_BYTES = concert_company_asa_service.clawback_address_bytes

available_tickets = load_concert_tickets_blockchain()

# tokility_dex_service.fund_address(receiver_address=concert_company_asa_service.clawback_address)
print('Clawback funded')

# tokility_dex_service.app_opt_in(user_pk=buyer_pk)
print('Buyer opted-int for the app')

# Ticket 1
ticket_1_config = available_tickets[0].asa_configuration
concert_company_asa_service.asa_opt_in(asa_id=ticket_1_config.asa_id,
                                       user_pk=buyer_pk)

tokility_dex_service.initial_buy(buyer_addr=buyer_add,
                                 buyer_pk=buyer_pk,
                                 asa_configuration=ticket_1_config,
                                 asa_clawback_addr=CLAWBACK_ADDRESS,
                                 asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)

tokility_dex_service.make_sell_offer(seller_pk=buyer_pk,
                                     sell_price=1000000,
                                     asa_configuration=ticket_1_config)

# Ticket 2
ticket_2_config = available_tickets[2].asa_configuration
concert_company_asa_service.asa_opt_in(asa_id=ticket_2_config.asa_id,
                                       user_pk=buyer_2_pk)

tokility_dex_service.initial_buy(buyer_addr=buyer_2_add,
                                 buyer_pk=buyer_2_pk,
                                 asa_configuration=ticket_2_config,
                                 asa_clawback_addr=CLAWBACK_ADDRESS,
                                 asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)

tokility_dex_service.app_opt_in(buyer_2_pk)
tokility_dex_service.make_sell_offer(seller_pk=buyer_2_pk,
                                     sell_price=2000000,
                                     asa_configuration=ticket_2_config)

# Active listings
indexer = get_indexer()


class SecondHandOfferingsRepository:

    @staticmethod
    def available_second_hand_offers(app_id: int) -> List[SaleOffer]:
        acc_app_info = indexer.accounts(application_id=app_id)
        sale_offers: List[SaleOffer] = []
        for account in acc_app_info['accounts']:
            for local_state in account['apps-local-state']:
                if local_state['id'] == app_id:
                    if 'key-value' in local_state:
                        for local_state_stored in local_state['key-value']:
                            seller_address = account['address']
                            asa_id = int.from_bytes(base64.b64decode(local_state_stored['key']), "big")
                            asa_price = local_state_stored['value']['uint']
                            # TODO: We can remove this once we have fast node or pay.
                            time.sleep(1.5)
                            asset_info = indexer.asset_info(asset_id=second_hand_offers[0][1])
                            r = requests.get(asset_info['asset']['params']['url'])

                            sale_offers.append(SaleOffer(sale_type="second_hand",
                                                         ticket=Ticket(**r.json()),
                                                         second_hand_seller_address=seller_address,
                                                         second_hand_amount=asa_price))

        return sale_offers


second_hand_offers = SecondHandOfferingsRepository.available_second_hand_offers(app_id=27629360)

print(second_hand_offers)

# Application transacitons

dex_transactions = indexer.search_transactions(application_id=tokility_dex_service.app_id)

for i, transaction in enumerate(dex_transactions['transactions']):
    print(f'Transaction: {i}')
    app_arguments = transaction['application-transaction']['application-args']
    print(f'Application args: {app_arguments}')
    if len(app_arguments) >= 9:
        method_name = base64.b64decode(app_arguments[0]).decode('utf-8')
        print(f'method_name: {method_name}')
    print('-' * 5)


# Creator holdings
class InitialBuyOfferingsRepository:

    @staticmethod
    def available_sell_offers(creator_address) -> List[SaleOffer]:
        indexer = get_indexer()
        assets = indexer.account_info(address=creator_address)
        available_for_sell_assets = set()

        for asset in assets['account']['assets']:
            if asset['amount'] == 1:
                available_for_sell_assets.add(asset['asset-id'])

        sale_offers: List[SaleOffer] = []
        for created_asset in assets['account']['created-assets']:
            if created_asset['index'] in available_for_sell_assets:
                r = requests.get(created_asset['params']['url'])
                sale_offers.append(SaleOffer(sale_type="initial_buy",
                                             ticket=Ticket(**r.json())))

        return sale_offers


available_concert_tokens = InitialBuyOfferingsRepository.available_sell_offers(creator_address=concert_company_addr)
