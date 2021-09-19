from pydantic import BaseModel
from src.models.ticket_models import Ticket
from typing import Optional


class SaleOffer(BaseModel):
    sale_type: str  # ["initial_buy", "second_hand"]
    ticket: Ticket
    second_hand_seller_address: Optional[str]
    second_hand_amount: Optional[int]

    @property
    def seller_address(self):
        if self.sale_type == "initial_buy":
            return self.ticket.asa_configuration.asa_creator_address
        elif self.sale_type == "second_hand":
            if self.second_hand_seller_address is None:
                raise ValueError(f"second_hand_seller_address cant be none")
            return self.second_hand_seller_address
        else:
            return NotImplemented

    @property
    def amount(self):
        if self.sale_type == "initial_buy":
            return self.ticket.asa_configuration.initial_offering_configuration.asa_price
        elif self.sale_type == "second_hand":
            if self.second_hand_amount is None:
                raise ValueError(f"second_hand_amount cant be none")
            return self.second_hand_amount \
                   + self.ticket.asa_configuration.economy_configuration.owner_fee \
                   + self.ticket.asa_configuration.initial_offering_configuration.tokiliy_fee
