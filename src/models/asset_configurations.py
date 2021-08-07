from pydantic import BaseModel
from typing import Optional, Dict
from hashlib import sha256
from algosdk.encoding import decode_address


class ASAInitialOfferingConfiguration(BaseModel):
    """
    Defines the configurations which describes the selling process of the ASA from the owner to the client.
    - asa_price: int - the price of the ASA in ALGOs.
    """
    asa_price: int


class ASAEconomyConfiguration(BaseModel):
    """
    Defines the configuration which describes the selling process of the ASA between clients i.e 3rd parties.
    - max_sell_price: int - the maximum allowed sell price of the ASA.
    - profit_fee: int - how much does the owner of the ASA receives from the profit of the asa in microAlgos.
    """
    max_sell_price: int
    owner_fee: int


class ASAConfiguration(BaseModel):
    """
    Defines the properties of the created Algorand Standard Asset. This properties should be used in the Smart Contracts
    """
    asa_owner_address: str
    unit_name: str
    asset_name: str
    asa_id: Optional[int]
    initial_offering_configuration: ASAInitialOfferingConfiguration
    economy_configuration: ASAEconomyConfiguration
    asa_metadata: Optional[Dict]

    @property
    def hashed_metadata_digest(self):
        if self.asa_metadata is None:
            return None
        return sha256(self.asa_metadata.__str__().encode()).digest()

    @property
    def hashed_metadata_hexdigest(self):
        if self.asa_metadata is None:
            return None
        return sha256(self.asa_metadata.__str__().encode()).hexdigest()
