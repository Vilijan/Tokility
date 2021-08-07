from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration
from src.blockchain_utils.transaction_repository import get_default_suggested_params, ApplicationTransactionRepository
from src.services import NetworkInteraction
from src.smart_contracts.tokility_asc1 import approval_program, clear_program
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode


def save_json(path, json_dict):
    import json

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)


def load_json(path):
    import json
    f = open(path)

    return json.load(f)


client = get_client()

acc_pk, acc_address, _ = get_account_credentials(account_id=1)

# Initialization of the Asset Configuration
# TODO: This should all be filled through UI.
asa_initial_offering_configuration = ASAInitialOfferingConfiguration(asa_price=1000000)
asa_economy_configuration = ASAEconomyConfiguration(owner_fee=500000, max_sell_price=5000000)
asa_metadata = dict()
asa_metadata['band_name'] = 'Skopski Merak'
asa_metadata['date'] = '11.08.2021'
asa_metadata['time'] = '18:00'
asa_metadata['table'] = 25
asa_metadata['image'] = "https://ipfs.io/ipfs/QmWipYGMDZPPAvPWGGY7ten1RmQ6JENy5KrQPPCZ8MXDGF"

asa_configuration = ASAConfiguration(asa_owner_address=acc_address,
                                     unit_name='Tokility',
                                     asset_name='SkopskiMerak',
                                     asa_id=None,
                                     initial_offering_configuration=asa_initial_offering_configuration,
                                     economy_configuration=asa_economy_configuration,
                                     asa_metadata=asa_metadata)

# 1. Creating the NFT

suggested_params = get_default_suggested_params(client=client)

txn = algo_txn.AssetConfigTxn(sender=acc_address,
                              sp=suggested_params,
                              total=1,
                              default_frozen=True,
                              unit_name=asa_configuration.unit_name,
                              asset_name=asa_configuration.asset_name,
                              manager=acc_address,
                              reserve=acc_address,
                              freeze=acc_address,
                              clawback=acc_address,
                              url=asa_configuration.asa_metadata.get("image", None),
                              decimals=0,
                              metadata_hash=asa_configuration.hashed_metadata_digest,
                              note=None)

signed_txn = txn.sign(acc_pk)

asa_id = NetworkInteraction.submit_asa_creation(client=client, transaction=signed_txn)
print(f'asa_id:{asa_id}')

asa_configuration.asa_id = asa_id

save_json('temp_configuration.json', asa_configuration.dict())

# 2. Setup the smart contract.

asa_configuration_dict = load_json('temp_configuration.json')
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

global_schema = algo_txn.StateSchema(num_uints=4,
                                     num_byte_slices=3)

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
print(f'Tokility app_id: {app_id}')


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
