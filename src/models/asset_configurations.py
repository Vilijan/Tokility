from pydantic import BaseModel
from typing import Optional, Dict
from algosdk.encoding import decode_address


class ASAInitialOfferingConfiguration(BaseModel):
    """
    Defines the configurations which describes the selling process of the ASA from the owner to the client.
    - asa_price: int - the price of the ASA in ALGOs.
    """
    asa_price: int
    tokiliy_fee: int


class ASAEconomyConfiguration(BaseModel):
    """
    Defines the configuration which describes the selling process of the ASA between clients i.e 3rd parties.
    - max_sell_price: int - the maximum allowed sell price of the ASA.
    - owner_fee: int - how much does the owner of the ASA receives from the profit of the asa in microAlgos.
    - reselling_allowed: int - whether the reselling on the second hand economy is allowed.
    - reselling_end_date: int - the timestamp of the last possible buy on the second hand economy.
    """
    max_sell_price: int
    owner_fee: int
    reselling_allowed: int
    reselling_end_date: int
    gifting_allowed: int


class ASAConfiguration(BaseModel):
    """
    Defines the properties of the created Algorand Standard Asset. This properties should be used in the Smart Contracts
    """
    asa_creator_address: str
    unit_name: str
    asset_name: str
    asa_id: Optional[int]
    initial_offering_configuration: ASAInitialOfferingConfiguration
    economy_configuration: ASAEconomyConfiguration
    asa_metadata: Optional[Dict]
    configuration_ipfs_url: Optional[str]

    @property
    def asa_price_bytes(self):
        return self.initial_offering_configuration.asa_price.to_bytes(8, 'big')

    @property
    def tokiliy_fee_bytes(self):
        return self.initial_offering_configuration.tokiliy_fee.to_bytes(8, 'big')

    @property
    def max_sell_price_bytes(self):
        return self.economy_configuration.max_sell_price.to_bytes(8, 'big')

    @property
    def owner_fee_bytes(self):
        return self.economy_configuration.owner_fee.to_bytes(8, 'big')

    @property
    def reselling_allowed_bytes(self):
        return self.economy_configuration.reselling_allowed.to_bytes(8, 'big')

    @property
    def reselling_end_date_bytes(self):
        return self.economy_configuration.reselling_end_date.to_bytes(8, 'big')

    @property
    def gifting_allowed_bytes(self):
        return self.economy_configuration.gifting_allowed.to_bytes(8, 'big')

    @property
    def dash_bytes(self):
        return bytes('-', 'utf-8')

    @property
    def asa_creator_address_bytes(self):
        return decode_address(self.asa_creator_address)

    @property
    def metadata_hash(self):
        return self.asa_price_bytes + \
               self.dash_bytes + \
               self.tokiliy_fee_bytes + \
               self.dash_bytes + \
               self.max_sell_price_bytes + \
               self.dash_bytes + \
               self.owner_fee_bytes + \
               self.dash_bytes + \
               self.reselling_allowed_bytes + \
               self.dash_bytes + \
               self.reselling_end_date_bytes + \
               self.dash_bytes + \
               self.gifting_allowed_bytes + \
               self.dash_bytes + \
               self.asa_owner_address_bytes
