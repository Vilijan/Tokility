from src.blockchain_utils.credentials import get_client, get_account_credentials
import src.services as services
from src.services.asset_creation import ASAProperties, ASAEconomyConfiguration

client = get_client()

acc_pk, acc_address, _ = get_account_credentials(account_id=1)

# Creating an ASA i.e utility tokens.

# This configuration should be configurable on UI per client.
economy_configuration = ASAEconomyConfiguration(max_sell_price=5000000,
                                                owner_fee=1000000,
                                                profit_fee=0)

asa_creation_service = services.AssetCreationService(asa_owner_pk=acc_pk,
                                                     unit_name='Logona',
                                                     asset_name='LOG',
                                                     total_supply=1000,
                                                     economy_configuration=economy_configuration)

# Creating the ASA

asa_creation_service.create_asa(client=client)
print(f'asa_id: {asa_creation_service.asa_id}')

# This properties should be logged in a database ?
asa_properties: ASAProperties = asa_creation_service.get_asa_properties()
print(asa_properties)
