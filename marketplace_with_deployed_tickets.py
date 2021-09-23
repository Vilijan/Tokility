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
from src.services.sale_offer_service import InitialBuyOfferingsService

acc_pk, acc_addr, _ = get_account_credentials(1)
buyer_pk, buyer_add, _ = get_account_credentials(2)
buyer_2_pk, buyer_2_add, _ = get_account_credentials(3)
concert_company_pk, concert_company_addr, _ = get_account_with_name("concert_company")
client = get_client()
APP_ID = 27661966


def algo(micro_algo) -> int:
    return int(micro_algo * 1000000)


# Initialization of Tokility services.
tokility_dex_service = TokilityDEXService(app_creator_addr=acc_addr,
                                          app_creator_pk=acc_pk,
                                          client=client,
                                          app_id=APP_ID)

concert_company_asa_service = ASAService(creator_addr=concert_company_addr,
                                         creator_pk=concert_company_pk,
                                         tokility_dex_app_id=tokility_dex_service.app_id,
                                         client=client)

CLAWBACK_ADDRESS = concert_company_asa_service.clawback_address
CLAWBACK_ADDRESS_BYTES = concert_company_asa_service.clawback_address_bytes

initial_buy_sale_offers = InitialBuyOfferingsService.available_sell_offers(creator_address=concert_company_addr)

for i, sale_offer in enumerate(initial_buy_sale_offers):
    print(f"{i}. asa_id: {sale_offer.ticket.asa_configuration.asa_id} "
          f"selling_allowed: {sale_offer.ticket.asa_configuration.economy_configuration.reselling_allowed}")

# Fund the clawback
# tokility_dex_service.fund_address(receiver_address=concert_company_asa_service.clawback_address)
print('Clawback funded')

# Opt-in buyers to the app.
# tokility_dex_service.app_opt_in(user_pk=buyer_pk)
# tokility_dex_service.app_opt_in(user_pk=buyer_2_pk)

# Ticket 1
ticket_1_config = initial_buy_sale_offers[0].ticket.asa_configuration
concert_company_asa_service.asa_opt_in(asa_id=ticket_1_config.asa_id,
                                       user_pk=buyer_pk)

tokility_dex_service.initial_buy(buyer_addr=buyer_add,
                                 buyer_pk=buyer_pk,
                                 asa_configuration=ticket_1_config,
                                 asa_clawback_addr=CLAWBACK_ADDRESS,
                                 asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)

tokility_dex_service.make_sell_offer(seller_pk=buyer_pk,
                                     sell_price=2200000,
                                     asa_configuration=ticket_1_config)

# Ticket 2
ticket_2_config = initial_buy_sale_offers[2].ticket.asa_configuration
concert_company_asa_service.asa_opt_in(asa_id=ticket_2_config.asa_id,
                                       user_pk=buyer_2_pk)

tokility_dex_service.initial_buy(buyer_addr=buyer_2_add,
                                 buyer_pk=buyer_2_pk,
                                 asa_configuration=ticket_2_config,
                                 asa_clawback_addr=CLAWBACK_ADDRESS,
                                 asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)

tokility_dex_service.make_sell_offer(seller_pk=buyer_2_pk,
                                     sell_price=1100000,
                                     asa_configuration=ticket_2_config)


# Buy ticket N
def buy_and_sell_ticket(buyer_private_key, buyer_address, asa_configuration, sell_price):
    concert_company_asa_service.asa_opt_in(asa_id=asa_configuration.asa_id,
                                           user_pk=buyer_private_key)

    tokility_dex_service.initial_buy(buyer_addr=buyer_address,
                                     buyer_pk=buyer_private_key,
                                     asa_configuration=asa_configuration,
                                     asa_clawback_addr=CLAWBACK_ADDRESS,
                                     asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)

    tokility_dex_service.make_sell_offer(seller_pk=buyer_private_key,
                                         sell_price=sell_price,
                                         asa_configuration=asa_configuration)


# buy_and_sell_ticket(buyer_private_key=buyer_2_pk,
#                     buyer_address=buyer_2_add,
#                     asa_configuration=initial_buy_sale_offers[1].ticket.asa_configuration,
#                     sell_price=5000000)

# Active listings
indexer = get_indexer()

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
