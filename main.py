import src.services as services
from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration

client = get_client()

acc_pk, acc_address, _ = get_account_credentials(account_id=1)

# Creating an ASA i.e utility tokens.

# This configuration should be configurable on UI per client.
economy_configuration = ASAEconomyConfiguration(max_sell_price=5000000,
                                                owner_fee=1000,
                                                profit_fee=1000)

initial_offering_configuration = ASAInitialOfferingConfiguration(asa_price=1000000,
                                                                 max_asa_per_user=5)

asa_creation_service = services.AssetCreationService(asa_owner_pk=acc_pk,
                                                     unit_name='Logona',
                                                     asset_name='LOG',
                                                     total_supply=1000,
                                                     initial_offering_configuration=initial_offering_configuration,
                                                     economy_configuration=economy_configuration)

# Creating the ASA

asa_creation_service.create_asa(client=client)
print(f'asa_id: {asa_creation_service.asa_id}')

# This properties should be logged in a database ?
asa_configuration: ASAConfiguration = asa_creation_service.get_asa_configuration()
print(asa_configuration)

asa_creation_service.setup_initial_offering_asc(client=client)

print(asa_creation_service.initial_offering_asc_address)

asa_creation_service.change_asa_clawback_address(client=client)


# Utils


def save_json(path, json_dict):
    import json

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)


def load_json(path):
    import json
    f = open(path)

    return json.load(f)


save_json('asa_configuration.json', asa_configuration.dict())

# ASA Buying

configuration = ASAConfiguration(**load_json('asa_configuration.json'))

from src.blockchain_utils.transaction_repository import ASATransactionRepository, PaymentTransactionRepository
from src.services.network_interaction import NetworkInteraction

buyer_pk, buyer_address, _ = get_account_credentials(account_id=2)

# Opt-in

opt_in_transaction = ASATransactionRepository.asa_opt_in(client=client,
                                                         sender_private_key=buyer_pk,
                                                         asa_id=configuration.asa_id)

NetworkInteraction.submit_transaction(client=client,
                                      transaction=opt_in_transaction)

# Atomic transfer


# get buytes
from src.smart_contracts.asa_initial_offering_asc import initial_offering_asc
from pyteal import compileTeal, Mode
from algosdk import logic as algo_logic

initial_offering_asc_compiled = compileTeal(initial_offering_asc(configuration=configuration),
                                            mode=Mode.Signature,
                                            version=3)

initial_offering_asc_bytes = NetworkInteraction.compile_program(client=client,
                                                                source_code=initial_offering_asc_compiled)

initial_offering_asc_address = algo_logic.address(initial_offering_asc_bytes)

payment_transaction = PaymentTransactionRepository.payment(client=client,
                                                           sender_address=buyer_address,
                                                           receiver_address=configuration.asa_owner_address,
                                                           amount=2000000,
                                                           sender_private_key=None,
                                                           sign_transaction=False)

asa_transfer_transaction = ASATransactionRepository.asa_transfer(client=client,
                                                                 sender_address=initial_offering_asc_address,
                                                                 receiver_address=buyer_address,
                                                                 amount=2,
                                                                 asa_id=configuration.asa_id,
                                                                 revocation_target=configuration.asa_owner_address,
                                                                 sender_private_key=None,
                                                                 sign_transaction=False)

from algosdk.future import transaction as algo_txn

gid = algo_txn.calculate_group_id([payment_transaction, asa_transfer_transaction])

payment_transaction.group = gid
asa_transfer_transaction.group = gid

payment_transaction_signed = payment_transaction.sign(buyer_pk)

asa_initial_offering_logic_signature = algo_txn.LogicSig(initial_offering_asc_bytes)
asa_transfer_transaction_signed = algo_txn.LogicSigTransaction(asa_transfer_transaction,
                                                               asa_initial_offering_logic_signature)

signed_group = [payment_transaction_signed,
                asa_transfer_transaction_signed]

txid = client.send_transactions(signed_group)

NetworkInteraction.wait_for_confirmation(client, txid)
