from typing import Optional
from pydantic import BaseModel
from src.services.network_interaction import NetworkInteraction
from src.blockchain_utils.transaction_repository import ASATransactionRepository
from algosdk import account as algo_acc
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration


class AssetCreationService:
    def __init__(self,
                 asa_owner_pk: str,
                 unit_name: str,
                 asset_name: str,
                 total_supply: int,
                 initial_offering_configuration: ASAInitialOfferingConfiguration,
                 economy_configuration: ASAEconomyConfiguration):
        self.asa_owner_pk = asa_owner_pk
        self.asa_owner_address = algo_acc.address_from_private_key(private_key=asa_owner_pk)
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.total_supply = total_supply

        self.asa_id = None
        self.initial_offering_configuration = initial_offering_configuration
        self.economy_configuration = economy_configuration

    def create_asa(self, client):
        transaction = ASATransactionRepository.create_asa(client=client,
                                                          creator_private_key=self.asa_owner_pk,
                                                          unit_name=self.unit_name,
                                                          asset_name=self.asset_name,
                                                          total=self.total_supply,
                                                          decimals=0,
                                                          manager_address=self.asa_owner_address,
                                                          reserve_address=self.asa_owner_address,
                                                          freeze_address=self.asa_owner_address,
                                                          clawback_address=self.asa_owner_address,
                                                          default_frozen=True)

        self.asa_id = NetworkInteraction.submit_asa_creation(client=client,
                                                             transaction=transaction)

    def get_asa_configuration(self) -> ASAConfiguration:
        if self.asa_id is None:
            raise ValueError("The ASA has not been created.")

        return ASAConfiguration(asa_owner_address=self.asa_owner_address,
                                unit_name=self.unit_name,
                                asset_name=self.asset_name,
                                total_supply=self.total_supply,
                                asa_id=self.asa_id,
                                initial_offering_configuration=self.initial_offering_configuration,
                                economy_configuration=self.economy_configuration)
