from src.blockchain_utils.credentials import get_client, get_account_credentials, get_account_with_name
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration
from src.blockchain_utils.transaction_repository import get_default_suggested_params, ApplicationTransactionRepository, \
    ASATransactionRepository, PaymentTransactionRepository
from src.services import NetworkInteraction
from src.smart_contracts.tokility_asc1 import approval_program, clear_program
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode
from src.smart_contracts.tokility_escrow import asa_escrow
from algosdk.encoding import decode_address


def save_json(path, json_dict):
    import json

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)


def load_json(path):
    import json
    f = open(path)

    return json.load(f)


client = get_client()

acc_pk, acc_address, _ = get_account_credentials(account_id=2)
pathe_pk, pathe_address, _ = get_account_with_name("pathe_cinema")

print(acc_address)

# Initialization of the Asset Configuration
# TODO: This should all be filled through UI.

# 1. Creating the NFT
# THIS IS DONE IN THE create_business_nfts.py script !
#
# suggested_params = get_default_suggested_params(client=client)
#
# txn = algo_txn.AssetConfigTxn(sender=acc_address,
#                               sp=suggested_params,
#                               total=1,
#                               default_frozen=True,
#                               unit_name=asa_configuration.unit_name,
#                               asset_name=asa_configuration.asset_name,
#                               manager=acc_address,
#                               reserve=acc_address,
#                               freeze=acc_address,
#                               clawback=acc_address,
#                               url=asa_configuration.hashed_metadata_digest,
#                               decimals=0,
#                               metadata_hash=asa_configuration.hashed_metadata_digest,
#                               note=None)
#
# signed_txn = txn.sign(acc_pk)
#
# asa_id = NetworkInteraction.submit_asa_creation(client=client, transaction=signed_txn)
# print(f'asa_id:{asa_id}')
#
# asa_configuration.asa_id = asa_id
#
# save_json('temp_configuration.json', asa_configuration.dict())

# 2. Setup the smart contract.

asa_configuration_dict = load_json('nft_configurations_deployed/Cinema Pathe_0.json')
asa_configuration = ASAConfiguration(**asa_configuration_dict)

approval_program_compiled = compileTeal(approval_program(asa_configuration=asa_configuration),
                                        mode=Mode.Application,
                                        version=4)

clear_program_compiled = compileTeal(clear_program(),
                                     mode=Mode.Application,
                                     version=4)

approval_program_bytes = NetworkInteraction.compile_program(client=client,
                                                            source_code=approval_program_compiled)

clear_program_bytes = NetworkInteraction.compile_program(client=client,
                                                         source_code=clear_program_compiled)

global_schema = algo_txn.StateSchema(num_uints=5,
                                     num_byte_slices=4)

local_schema = algo_txn.StateSchema(num_uints=0,
                                    num_byte_slices=0)

app_transaction = ApplicationTransactionRepository.create_application(client=client,
                                                                      creator_private_key=acc_pk,
                                                                      approval_program=approval_program_bytes,
                                                                      clear_program=clear_program_bytes,
                                                                      global_schema=global_schema,
                                                                      local_schema=local_schema,
                                                                      app_args=None)

tx_id = NetworkInteraction.submit_transaction(client,
                                              transaction=app_transaction)

transaction_response = client.pending_transaction_info(tx_id)

app_id = transaction_response['application-index']
print(f'Deployed Tokility app with app_id: {app_id}')

# Setup Escrow address.
escrow_fund_program_compiled = compileTeal(asa_escrow(app_id=app_id,
                                                      asa_configuration=asa_configuration),
                                           mode=Mode.Signature,
                                           version=4)

escrow_fund_program_bytes = NetworkInteraction.compile_program(client=client,
                                                               source_code=escrow_fund_program_compiled)

escrow_fund_address = algo_logic.address(escrow_fund_program_bytes)

app_args = [
    "initialize_escrow",
    decode_address(escrow_fund_address)
]

initialize_escrow_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                          caller_private_key=acc_pk,
                                                                          app_id=app_id,
                                                                          on_complete=algo_txn.OnComplete.NoOpOC,
                                                                          app_args=app_args)

tx_id = NetworkInteraction.submit_transaction(client,
                                              transaction=initialize_escrow_txn)

print(f'Escrow initialized in the Tokility ASC1.')

fund_escrow_txn = PaymentTransactionRepository.payment(client=client,
                                                       sender_address=acc_address,
                                                       receiver_address=escrow_fund_address,
                                                       amount=1000000,
                                                       sender_private_key=acc_pk,
                                                       sign_transaction=True)

_ = NetworkInteraction.submit_transaction(client,
                                          transaction=fund_escrow_txn)

print(f'Funds submited to the escrow address.')

# Change ASA Credentials:


change_asa_management_txn = ASATransactionRepository.change_asa_management(client=client,
                                                                           current_manager_pk=pathe_pk,
                                                                           asa_id=asa_configuration.asa_id,
                                                                           manager_address="",
                                                                           reserve_address="",
                                                                           freeze_address="",
                                                                           strict_empty_address_check=False,
                                                                           clawback_address=escrow_fund_address)

_ = NetworkInteraction.submit_transaction(client,
                                          transaction=change_asa_management_txn)

print('ASA management has been updated.')

# Buy ASA

# Opt-in

opt_in_txn = ASATransactionRepository.asa_opt_in(client=client,
                                                 sender_private_key=acc_pk,
                                                 asa_id=asa_configuration.asa_id)

opt_in_txn_id = NetworkInteraction.submit_transaction(client,
                                                      transaction=opt_in_txn)

print('Opt-in transaction completed')

# 1. Application call txn
app_args = [
    "buy_asa"
]

app_call_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                 caller_private_key=acc_pk,
                                                                 app_id=app_id,
                                                                 on_complete=algo_txn.OnComplete.NoOpOC,
                                                                 app_args=app_args,
                                                                 sign_transaction=False)

# 2. Asset transfer transaction
sp = get_default_suggested_params(client)
asa_transfer_txn = algo_txn.AssetTransferTxn(sender=escrow_fund_address,
                                             sp=sp,
                                             receiver=acc_address,
                                             amt=1,
                                             index=asa_configuration.asa_id,
                                             revocation_target=asa_configuration.asa_owner_address)  # current owner

# 3. Payment transaction

asa_buy_txn = PaymentTransactionRepository.payment(client=client,
                                                   sender_address=acc_address,
                                                   receiver_address=asa_configuration.asa_owner_address,
                                                   amount=10000000,
                                                   sender_private_key=None,
                                                   sign_transaction=False)

# Atomic transfer
gid = algo_txn.calculate_group_id([app_call_txn,
                                   asa_transfer_txn,
                                   asa_buy_txn])

app_call_txn.group = gid
asa_transfer_txn.group = gid
asa_buy_txn.group = gid

app_call_txn_signed = app_call_txn.sign(acc_pk)

asa_transfer_txn_logic_signature = algo_txn.LogicSig(escrow_fund_program_bytes)
asa_transfer_txn_signed = algo_txn.LogicSigTransaction(asa_transfer_txn, asa_transfer_txn_logic_signature)

asa_buy_txn_signed = asa_buy_txn.sign(acc_pk)

signed_group = [app_call_txn_signed,
                asa_transfer_txn_signed,
                asa_buy_txn_signed]

txid = client.send_transactions(signed_group)
print(f'Buy asa transaction completed in: {txid}')

# Sell ASA Second Hand

app_args = [
    "sell_asa",
    11000000
]

sell_asa_transaction = ApplicationTransactionRepository.call_application(client=client,
                                                                         caller_private_key=acc_pk,
                                                                         app_id=app_id,
                                                                         on_complete=algo_txn.OnComplete.NoOpOC,
                                                                         app_args=app_args,
                                                                         sign_transaction=True)

_ = NetworkInteraction.submit_transaction(client,
                                          transaction=sell_asa_transaction)

print(f'Offered selling for the ASA')

# STOP SELLING

app_args = [
    "stop_selling_asa"
]

stop_selling_asa_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                         caller_private_key=acc_pk,
                                                                         app_id=app_id,
                                                                         on_complete=algo_txn.OnComplete.NoOpOC,
                                                                         app_args=app_args,
                                                                         sign_transaction=True)

_ = NetworkInteraction.submit_transaction(client,
                                          transaction=stop_selling_asa_txn)

print("Stopped selling of the ASA")

# USE ASA
app_args = [
    "use_asa"
]

use_asa_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                caller_private_key=pathe_pk,
                                                                app_id=app_id,
                                                                on_complete=algo_txn.OnComplete.NoOpOC,
                                                                app_args=app_args,
                                                                sign_transaction=True)

_ = NetworkInteraction.submit_transaction(client,
                                          transaction=use_asa_txn)

print("ASA used in the real world.")


# TODO: DECODING UI VARIABLES

# import base64
# from hashlib import sha256
# myObj = [base64.b64decode(b"QmV0QW1vdW50").decode('utf-8')]
#
# print(myObj)
#
# value = "BetAmount"
#
# base64.b64encode(value.encode())
#
# print(sha256(value).hexdigest())
