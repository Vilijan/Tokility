from typing import Optional
from pydantic import BaseModel
from src.services.network_interaction import NetworkInteraction
from src.blockchain_utils.transaction_repository import ASATransactionRepository
from algosdk import account as algo_acc


class ASAEconomyConfiguration(BaseModel):
    """
    Defines the behavior of the economy for the ASA by the 3rd parties. This configuration should be sent as parameter
    to the Smart Contracts of the application.
    """

    max_sell_price: int
    owner_fee: int
    profit_fee: int


class ASAProperties(BaseModel):
    """
    Defines the properties of the created Algorand Standard Asset. This properties should be used in the Smart Contracts
    """
    asa_owner_address: str
    unit_name: str
    asset_name: str
    total_supply: int
    asa_id: int
    economy_configuration: ASAEconomyConfiguration


class AssetCreationService:
    def __init__(self,
                 asa_owner_pk: str,
                 unit_name: str,
                 asset_name: str,
                 total_supply: int,
                 economy_configuration: ASAEconomyConfiguration):
        self.asa_owner_pk = asa_owner_pk
        self.asa_owner_address = algo_acc.address_from_private_key(private_key=asa_owner_pk)
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.total_supply = total_supply

        self.asa_id = None
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

    def get_asa_properties(self) -> ASAProperties:
        if self.asa_id is None:
            raise ValueError("The ASA has not been created.")

        return ASAProperties(asa_owner_address=self.asa_owner_address,
                             unit_name=self.unit_name,
                             asset_name=self.asset_name,
                             total_supply=self.total_supply,
                             asa_id=self.asa_id,
                             economy_configuration=self.economy_configuration)
