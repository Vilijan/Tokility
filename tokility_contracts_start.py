from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer
from src.models.asset_configurations import ASAConfiguration, ASAInitialOfferingConfiguration, ASAEconomyConfiguration
from src.services.asa_service import ASAService
from src.services.tokility_dex_service import TokilityDEXService
import json

acc_pk, acc_addr, _ = get_account_credentials(7)
buyer_pk, buyer_add, _ = get_account_credentials(8)
buyer_2_pk, buyer_2_add, _ = get_account_credentials(9)

client = get_client()

# Initialization of Tokility services.
tokility_dex_service = TokilityDEXService(app_creator_addr=acc_addr,
                                          app_creator_pk=acc_pk,
                                          client=client)

asa_service = ASAService(creator_addr=acc_addr,
                         creator_pk=acc_pk,
                         tokility_dex_app_id=tokility_dex_service.app_id,
                         client=client)

# Creating and deploying the ASAs.

initial_offering_config = ASAInitialOfferingConfiguration(asa_price=10000)
economy_configuration = ASAEconomyConfiguration(max_sell_price=10000000, owner_fee=1000)

asa_1_config = ASAConfiguration(asa_owner_address=acc_addr,
                                unit_name="TOK",
                                asset_name="TOK",
                                initial_offering_configuration=initial_offering_config,
                                economy_configuration=economy_configuration)

asa_1_id, _ = asa_service.create_asa(asa_configuration=asa_1_config)
asa_1_config.asa_id = asa_1_id

# Create the stateless clawback contract.
asa_1_clawback_addr, asa_1_clawback_bytes = asa_service.create_clawback(asa_configuration=asa_1_config)
# Fund clawback
tokility_dex_service.fund_address(receiver_address=asa_1_clawback_addr)

# Set it as a clawback to the NFT.

asa_service.update_asa_management(asa_id=asa_1_config.asa_id,
                                  manager_address="",
                                  reserve_address="",
                                  freeze_address="",
                                  clawback_address=asa_1_clawback_addr)

print(f'NFT management changed')

# User opt-ins to the app

tokility_dex_service.app_opt_in(user_pk=buyer_pk)

# Buyer opt-ins to the ASA
asa_service.asa_opt_in(asa_id=asa_1_config.asa_id,
                       user_pk=buyer_pk)

# Initial buy
# Buy the first ASA
tokility_dex_service.initial_buy(buyer_addr=buyer_add,
                                 buyer_pk=buyer_pk,
                                 asa_configuration=asa_1_config,
                                 asa_clawback_addr=asa_1_clawback_addr,
                                 asa_clawback_bytes=asa_1_clawback_bytes)

# Sell ASA

tokility_dex_service.make_sell_offer(seller_pk=buyer_pk,
                                     asa_id=asa_1_config.asa_id,
                                     sell_price=1000000)

tokility_dex_service.stop_selling(seller_pk=buyer_pk,
                                  asa_id=asa_1_config.asa_id)

# Buy second hand ASA.

asa_service.asa_opt_in(asa_id=asa_1_config.asa_id,
                       user_pk=buyer_2_pk)

tokility_dex_service.buy_from_seller(buyer_addr=buyer_2_add,
                                     buyer_pk=buyer_2_pk,
                                     seller_addr=buyer_add,
                                     price=1000000,
                                     asa_configuration=asa_1_config,
                                     asa_clawback_addr=asa_1_clawback_addr,
                                     asa_clawback_bytes=asa_1_clawback_bytes)

tokility_dex_service.app_opt_in(user_pk=buyer_2_pk)

tokility_dex_service.make_sell_offer(seller_pk=buyer_2_pk,
                                     asa_id=asa_1_config.asa_id,
                                     sell_price=252525)

# Buyer #2

#
# asa_2_config = ASAConfiguration(asa_owner_address=acc_addr,
#                                 unit_name="WAW",
#                                 asset_name="WAW",
#                                 initial_offering_configuration=initial_offering_config,
#                                 economy_configuration=economy_configuration)
#
# asa_2_id, _ = asa_service.create_asa(asa_configuration=asa_2_config)
# asa_2_config.asa_id = asa_2_id
#
# asa_2_clawback_addr, asa_2_clawback_bytes = asa_service.create_clawback(asa_configuration=asa_2_config)
# tokility_dex_service.fund_address(receiver_address=asa_2_clawback_addr)
#
# asa_service.update_asa_management(asa_id=asa_2_config.asa_id,
#                                   manager_address="",
#                                   reserve_address="",
#                                   freeze_address="",
#                                   clawback_address=asa_2_clawback_addr)
#
# tokility_dex_service.app_opt_in(user_pk=buyer_2_pk)
# asa_service.asa_opt_in(asa_id=asa_2_config.asa_id,
#                        user_pk=buyer_2_pk)
#
# tokility_dex_service.initial_buy(buyer_addr=buyer_2_add,
#                                  buyer_pk=buyer_2_pk,
#                                  asa_configuration=asa_2_config,
#                                  asa_clawback_addr=asa_2_clawback_addr,
#                                  asa_clawback_bytes=asa_2_clawback_bytes)
#
# tokility_dex_service.make_sell_offer(seller_pk=buyer_2_pk,
#                                      asa_id=asa_2_config.asa_id,
#                                      sell_price=991999)

# Query the indexer to list all the orders.

import base64
import time

time.sleep(5)

indexer = get_indexer()

# Local state for specific address.
#
# acc_info = indexer.account_info(address=buyer_add)
# print("Response Info: " + json.dumps(acc_info, indent=2, sort_keys=True))

# print(int.from_bytes(base64.b64decode(acc_info['account']['apps-local-state'][0]['key-value'][0]['key']), "big"))
# print(asa_1_config.asa_id)

# Local states of all addresses.


acc_app_info = indexer.accounts(application_id=tokility_dex_service.app_id)
# print("Response Info: " + json.dumps(acc_app_info, indent=2, sort_keys=True))

for account in acc_app_info['accounts']:
    for local_state in account['apps-local-state']:
        if local_state['id'] == tokility_dex_service.app_id:
            if 'key-value' in local_state:
                for local_state_stored in local_state['key-value']:
                    seller_address = account['address']
                    asa_id = int.from_bytes(base64.b64decode(local_state_stored['key']), "big")
                    asa_price = local_state_stored['value']['uint']
                    print(f'{seller_address} sells {asa_id} for {asa_price} micro Algos')

# print(asa_service.database)
#
print(tokility_dex_service.app_id)
print(asa_1_config.asa_id)

print(buyer_add)
