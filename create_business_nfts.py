from src.blockchain_utils.credentials import get_account_with_name
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


foo_fighters_pk, foo_fighters_addr, _ = get_account_with_name("foo_fighters")
pathe_cinema_pk, pathe_cinema_addr, _ = get_account_with_name("pathe_cinema")
jamie_oliver_pk, jamie_oliver_addr, _ = get_account_with_name("jamie_oliver")

client = get_client()

# NFT Initialization
asa_initial_offering_configuration = ASAInitialOfferingConfiguration(asa_price=10000000)
asa_economy_configuration = ASAEconomyConfiguration(owner_fee=1000000, max_sell_price=15000000)
asa_metadata = dict()
asa_metadata['business'] = 'Cinema Pathe'
asa_metadata['date'] = '25.08.2021'
asa_metadata['time'] = '21:00'
asa_metadata['hall'] = 15
asa_metadata['row'] = 25
asa_metadata['seat'] = 7
asa_metadata['image'] = "https://ipfs.io/ipfs/QmTz9RY7UrK3ppaPtUyRe8C3WJHwiRx56337RDZ6UwkR8S?filename=7.png"

asa_configuration = ASAConfiguration(asa_owner_address=pathe_cinema_addr,
                                     unit_name='Tokility',
                                     asset_name='PatheCinema',
                                     asa_id=None,
                                     initial_offering_configuration=asa_initial_offering_configuration,
                                     economy_configuration=asa_economy_configuration,
                                     asa_metadata=asa_metadata)

# 1. Creating the NFT

suggested_params = get_default_suggested_params(client=client)

txn = algo_txn.AssetConfigTxn(sender=pathe_cinema_addr,
                              sp=suggested_params,
                              total=1,
                              default_frozen=True,
                              unit_name=asa_configuration.unit_name,
                              asset_name=asa_configuration.asset_name,
                              manager=pathe_cinema_addr,
                              reserve=pathe_cinema_addr,
                              freeze=pathe_cinema_addr,
                              clawback=pathe_cinema_addr,
                              url=asa_configuration.asa_metadata.get("image", None),
                              decimals=0,
                              metadata_hash=asa_configuration.hashed_metadata_digest,
                              note=None)

signed_txn = txn.sign(pathe_cinema_pk)

asa_id = NetworkInteraction.submit_asa_creation(client=client, transaction=signed_txn)
print(f'asa_id:{asa_id}')

asa_configuration.asa_id = asa_id

save_json('nft_configurations/pathe_cinema_2.json', asa_configuration.dict())

print(pathe_cinema_addr)



