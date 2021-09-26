from src.blockchain_utils.credentials import get_client, get_account_credentials, get_account_with_name
from src.services.asa_service import ASAService
from src.services.tokility_dex_service import TokilityDEXService
import algosdk
import json


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


app_creator_pk, app_creator_address = algosdk.account.generate_account()
conference_company_pk, conference_company_address = algosdk.account.generate_account()
buyer_1_pk, buyer_1_address = algosdk.account.generate_account()
buyer_2_pk, buyer_2_address = algosdk.account.generate_account()

client = get_client()

print(f'Application creator address: {app_creator_address}')
print(f'Utility provider for conference tickets address: {conference_company_address}')
print(f'Buyer 1 address: {buyer_1_address}')
print(f'Buyer 2 address: {buyer_2_address}')
print('-' * 50)

print(f'Fund the accounts on: https://bank.testnet.algorand.network/')
fund_accounts = input('Press any button once you have funded them.    ')

print(f'Accounts funded.')
print('-' * 50)

# Initialization of Tokility services.
tokility_dex_service = TokilityDEXService(app_creator_addr=app_creator_address,
                                          app_creator_pk=app_creator_pk,
                                          client=client)
print(f'Marketplace APP_ID: {tokility_dex_service.app_id}')

concert_company_asa_service = ASAService(creator_addr=conference_company_address,
                                         creator_pk=conference_company_pk,
                                         tokility_dex_app_id=tokility_dex_service.app_id,
                                         client=client)

print(f'Tokility CLAWBACK_ADDRESS: {concert_company_asa_service.clawback_address}')

# Fund the clawback
print('-' * 50)
tx_id = tokility_dex_service.fund_address(receiver_address=concert_company_asa_service.clawback_address)
print(f'Clawback funded in: {tx_id}')

# Opt-in buyers to the app.
print('-' * 50)
tokility_dex_service.app_opt_in(user_pk=buyer_1_pk)
print(f'Buyer 1 opted-in the marketplace application')
print('-' * 50)
tokility_dex_service.app_opt_in(user_pk=buyer_2_pk)
print(f'Buyer 2 opted-in the marketplace application')

config = dict()

config['app_creator_address'] = app_creator_address
config['app_creator_pk'] = app_creator_pk

config['conference_company_address'] = conference_company_address
config['conference_company_pk'] = conference_company_pk

config['buyer_1_address'] = buyer_1_address
config['buyer_1_pk'] = buyer_1_pk

config['buyer_2_address'] = buyer_2_address
config['buyer_2_pk'] = buyer_2_pk

config['app_id'] = tokility_dex_service.app_id

print('-' * 50)
print('Configuration saved')
save_json('config.json', config)
