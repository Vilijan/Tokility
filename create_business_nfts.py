from src.blockchain_utils.credentials import get_account_with_name
from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration
from src.blockchain_utils.transaction_repository import get_default_suggested_params, ApplicationTransactionRepository
from src.services import NetworkInteraction
from algosdk.future import transaction as algo_txn
from collections import defaultdict
import os


def save_json(path, json_dict):
    import json

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)


def load_json(path):
    import json
    f = open(path)

    return json.load(f)


foo_fighters_pk, foo_fighters_addr, _ = get_account_with_name("foo_fighters")
pathe_cinema_pk, pathe_cinema_addr, _ = get_account_with_name("pathe_cinema")
jamie_oliver_pk, jamie_oliver_addr, _ = get_account_with_name("jamie_oliver")
acc_pk, acc_addr, _ = get_account_credentials(1)

client = get_client()

asa_configurations_dummy = load_json('nft_configurations.json')
asa_configurations = [ASAConfiguration(**nft) for nft in asa_configurations_dummy['nfts']]

ipfs_configurations_dummy = load_json('ipfs_configurations_dummy_list.json')
ipfs_configurations_urls = [ipfs_url for ipfs_url in ipfs_configurations_dummy['ipfs_configurations']]

config_names = os.listdir('nft_configurations')

# Save the configurations locally for easy deployment to IPFS.

# nfts_per_business = defaultdict(lambda: 0)
#
# for asa_config in asa_configurations:
#     business_name = asa_config.asa_metadata['business']
#     id = nfts_per_business[business_name]
#     save_json(f'nft_configurations/{business_name}_{id}.json', asa_config.dict())
#     nfts_per_business[business_name] = id + 1

# NFT Deployment
# 1. Load the configuration from UI.

CONFIG_IDX = 0
NFT_CREATOR_PK = pathe_cinema_pk
NFT_CREATOR_ADDRESS = pathe_cinema_addr

asa_configuration = asa_configurations[CONFIG_IDX]

# 2. Deploy this configuration to the IPFS and load the url.

# TODO: - Implement configuration deployment to IPFS.
# ipfs_config_url = deploy_to_ipfs(asa_configuration)

asa_configuration.configuration_ipfs_url = ipfs_configurations_urls[CONFIG_IDX]

# 3. Deploy the NFT to the Network.

suggested_params = get_default_suggested_params(client=client)

txn = algo_txn.AssetConfigTxn(sender=NFT_CREATOR_ADDRESS,
                              sp=suggested_params,
                              total=1,
                              default_frozen=True,
                              unit_name=asa_configuration.unit_name,
                              asset_name=asa_configuration.asset_name,
                              manager=NFT_CREATOR_ADDRESS,
                              reserve=NFT_CREATOR_ADDRESS,
                              freeze=NFT_CREATOR_ADDRESS,
                              clawback=NFT_CREATOR_ADDRESS,
                              url=asa_configuration.configuration_ipfs_url,
                              decimals=0,
                              metadata_hash=asa_configuration.hashed_configuration,
                              note=None)

signed_txn = txn.sign(NFT_CREATOR_PK)

asa_id = NetworkInteraction.submit_asa_creation(client=client, transaction=signed_txn)
print(f'asa_id:{asa_id}')

asa_configuration.asa_id = asa_id

save_json(f'nft_configurations_deployed/{config_names[CONFIG_IDX]}', asa_configuration.dict())
