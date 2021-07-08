from pydantic import BaseModel
from typing import Optional


class ASAInitialOfferingConfiguration(BaseModel):
    """
    Defines the configurations which describes the selling process of the ASA from the owner to the client.
    - asa_price: int - the price of the ASA in ALGOs.
    - max_asa_per_user: int - the maximum number of asa a single address can own.
    """
    asa_price: int
    max_asa_per_user: int


class ASAEconomyConfiguration(BaseModel):
    """
    Defines the configuration which describes the selling process of the ASA between clients i.e 3rd parties.
    - max_sell_price: int - the maximum allowed sell price of the ASA.
    - owner_fee: int - how much does the owner of the ASA receives from the selling transaction.
    - profit_fee: int - how much does the owner of the ASA receives from the profit of the asa.
    """
    max_sell_price: int
    owner_fee: int
    profit_fee: int


class ASAConfiguration(BaseModel):
    """
    Defines the properties of the created Algorand Standard Asset. This properties should be used in the Smart Contracts
    """
    asa_owner_address: str
    unit_name: str
    asset_name: str
    total_supply: int
    asa_id: int
    initial_offering_configuration: ASAInitialOfferingConfiguration
    economy_configuration: ASAEconomyConfiguration
