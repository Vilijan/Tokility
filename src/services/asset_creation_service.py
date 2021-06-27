from typing import Optional
from pydantic import BaseModel


class ASAEconomyConfiguration(BaseModel):
    """
    Defines the behavior of the economy for the ASA by the 3rd parties.
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
                 asa_configuration: ASAEconomyConfiguration):
        self.asa_owner_pk = asa_owner_pk
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.total_supply = total_supply

        self.asa_id = ''
        self.asa_configuration = asa_configuration
