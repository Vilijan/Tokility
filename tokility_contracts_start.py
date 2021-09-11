from src.blockchain_utils.credentials import get_client, get_account_credentials, get_indexer
from src.models.asset_configurations import ASAConfiguration, ASAInitialOfferingConfiguration, ASAEconomyConfiguration
from src.smart_contracts.tokility_dex_asc1 import TokilityDEX
from src.smart_contracts.tokility_clawback_asc1 import TokilityClawbackASC1
from src.blockchain_utils.transaction_repository import ASATransactionRepository, \
    ApplicationTransactionRepository, PaymentTransactionRepository
from src.services import NetworkInteraction
from pyteal import compileTeal, Mode
import algosdk
import json

acc_pk, acc_addr, _ = get_account_credentials(3)

client = get_client()

# Creating and deploying the NFT.

initial_offering_config = ASAInitialOfferingConfiguration(asa_price=10000)
economy_configuration = ASAEconomyConfiguration(max_sell_price=1000000, owner_fee=1000)

asa_configuration = ASAConfiguration(asa_owner_address=acc_addr,
                                     unit_name="TOK",
                                     asset_name="TOK",
                                     initial_offering_configuration=initial_offering_config,
                                     economy_configuration=economy_configuration)

signed_txn = ASATransactionRepository.create_non_fungible_asa(
    client=client,
    creator_private_key=acc_pk,
    unit_name=asa_configuration.unit_name,
    asset_name=asa_configuration.asset_name,
    note=None,
    manager_address=acc_addr,
    reserve_address=acc_addr,
    freeze_address=acc_addr,
    clawback_address=acc_addr,
    url=None,
    default_frozen=True,
    sign_transaction=True,
)

nft_id, tx_id = NetworkInteraction.submit_asa_creation(
    client=client, transaction=signed_txn
)
print(f'NFT deployed with id: {nft_id}')

asa_configuration.asa_id = nft_id

# Deploy the Tokility Dex

tokility_dex = TokilityDEX()

approval_program_compiled = compileTeal(
    tokility_dex.approval_program(),
    mode=Mode.Application,
    version=4,
)

clear_program_compiled = compileTeal(
    tokility_dex.clear_program(),
    mode=Mode.Application,
    version=4
)

approval_program_bytes = NetworkInteraction.compile_program(
    client=client, source_code=approval_program_compiled
)

clear_program_bytes = NetworkInteraction.compile_program(
    client=client, source_code=clear_program_compiled
)

app_transaction = ApplicationTransactionRepository.create_application(
    client=client,
    creator_private_key=acc_pk,
    approval_program=approval_program_bytes,
    clear_program=clear_program_bytes,
    global_schema=tokility_dex.global_schema,
    local_schema=tokility_dex.local_schema,
)

tx_id = NetworkInteraction.submit_transaction(
    client, transaction=app_transaction
)

transaction_response = client.pending_transaction_info(tx_id)

app_id = transaction_response["application-index"]

print(f'DEX deployed with app_id: {app_id}')

# Create the stateless clawback contract.

tokility_clawback_asc1 = TokilityClawbackASC1(configuration=asa_configuration,
                                              app_id=app_id)

clawback_asc1_compiled = compileTeal(tokility_clawback_asc1.pyteal_code(),
                                     mode=Mode.Signature,
                                     version=4)

clawback_asc1_compiled_bytes = NetworkInteraction.compile_program(client=client,
                                                                  source_code=clawback_asc1_compiled)

clawback_address = algosdk.logic.address(clawback_asc1_compiled_bytes)

fund_clawback_txn = PaymentTransactionRepository.payment(
    client=client,
    sender_address=acc_addr,
    receiver_address=clawback_address,
    amount=1000000,
    sender_private_key=acc_pk,
    sign_transaction=True,
)

tx_id = NetworkInteraction.submit_transaction(
    client, transaction=fund_clawback_txn
)

# Set it as a clawback to the NFT.

txn = ASATransactionRepository.change_asa_management(
    client=client,
    current_manager_pk=acc_pk,
    asa_id=asa_configuration.asa_id,
    manager_address="",
    reserve_address="",
    freeze_address="",
    strict_empty_address_check=False,
    clawback_address=clawback_address,
    sign_transaction=True,
)

tx_id = NetworkInteraction.submit_transaction(client, transaction=txn)

print(f'NFT management changed')

# User optins to the app

params = client.suggested_params()
params.flat_fee = True
params.fee = 1000

# create unsigned transaction
txn = algosdk.future.transaction.ApplicationOptInTxn(acc_addr,
                                                     params,
                                                     app_id)

# sign transaction
signed_txn = txn.sign(acc_pk)

NetworkInteraction.submit_transaction(client, signed_txn)

print(f'User opted-in to the app.')

# New user opts in

buyer_pk, buyer_add, _ = get_account_credentials(2)

params = client.suggested_params()
params.flat_fee = True
params.fee = 1000

# create unsigned transaction
txn = algosdk.future.transaction.ApplicationOptInTxn(buyer_add,
                                                     params,
                                                     app_id)

# sign transaction
signed_txn = txn.sign(buyer_pk)

NetworkInteraction.submit_transaction(client, signed_txn)

print(f'User opted-in to the app.')

# Buyer opt-ins for the ASA
opt_in_txn = ASATransactionRepository.asa_opt_in(
    client=client, sender_private_key=buyer_pk, asa_id=asa_configuration.asa_id
)

tx_id = NetworkInteraction.submit_transaction(client, transaction=opt_in_txn)

# Initial buy

app_args = [
    TokilityDEX.AppMethods.initial_buy
]

app_call_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                 caller_private_key=buyer_pk,
                                                                 app_id=app_id,
                                                                 on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                                 app_args=app_args,
                                                                 foreign_assets=[asa_configuration.asa_id],
                                                                 sign_transaction=False)

# 2. Payment transaction: buyer -> seller
asa_buy_payment_txn = PaymentTransactionRepository.payment(client=client,
                                                           sender_address=buyer_add,
                                                           receiver_address=asa_configuration.asa_owner_address,
                                                           amount=asa_configuration.initial_offering_configuration.asa_price,
                                                           sender_private_key=None,
                                                           sign_transaction=False)

# 3. Asset transfer transaction: escrow -> buyer

asa_transfer_txn = ASATransactionRepository.asa_transfer(client=client,
                                                         sender_address=clawback_address,
                                                         receiver_address=buyer_add,
                                                         amount=1,
                                                         asa_id=asa_configuration.asa_id,
                                                         revocation_target=asa_configuration.asa_owner_address,
                                                         sender_private_key=None,
                                                         sign_transaction=False)

# Atomic transfer
gid = algosdk.future.transaction.calculate_group_id([app_call_txn,
                                                     asa_buy_payment_txn,
                                                     asa_transfer_txn])

app_call_txn.group = gid
asa_buy_payment_txn.group = gid
asa_transfer_txn.group = gid

app_call_txn_signed = app_call_txn.sign(buyer_pk)

asa_buy_txn_signed = asa_buy_payment_txn.sign(buyer_pk)

asa_transfer_txn_logic_signature = algosdk.future.transaction.LogicSig(clawback_asc1_compiled_bytes)
asa_transfer_txn_signed = algosdk.future.transaction.LogicSigTransaction(asa_transfer_txn,
                                                                         asa_transfer_txn_logic_signature)

signed_group = [app_call_txn_signed,
                asa_buy_txn_signed,
                asa_transfer_txn_signed]

tx_id = client.send_transactions(signed_group)

print(tx_id)
print("Initial buy completed.")

# Sell ASA


app_args = [
    TokilityDEX.AppMethods.sell_asa,
    asa_configuration.initial_offering_configuration.asa_price + 10
]

make_sell_order_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                        caller_private_key=buyer_pk,
                                                                        app_id=app_id,
                                                                        on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                                        app_args=app_args,
                                                                        foreign_assets=[asa_configuration.asa_id],
                                                                        sign_transaction=True)

NetworkInteraction.submit_transaction(client, make_sell_order_txn)
print("Sell order has been placed.")

# Query the indexer to list all the orders.

indexer = get_indexer()

# Local state for specific address.
#
# acc_info = indexer.account_info(address=buyer_add)
# print("Response Info: " + json.dumps(acc_info, indent=2, sort_keys=True))

import base64
import time

# print(int.from_bytes(base64.b64decode(acc_info['account']['apps-local-state'][0]['key-value'][0]['key']), "big"))
# print(asa_configuration.asa_id)

# Local states of all addresses.

time.sleep(5)

acc_app_info = indexer.accounts(application_id=app_id)
# print("Response Info: " + json.dumps(acc_app_info, indent=2, sort_keys=True))

for account in acc_app_info['accounts']:
    for local_state in account['apps-local-state']:
        if local_state['id'] == app_id:
            if 'key-value' in local_state:
                for local_state_stored in local_state['key-value']:
                    seller_address = account['address']
                    asa_id = int.from_bytes(base64.b64decode(local_state_stored['key']), "big")
                    asa_price = local_state_stored['value']['uint']
                    print(f'{seller_address} sells {asa_id} for {asa_price} micro Algos')

print(app_id)
