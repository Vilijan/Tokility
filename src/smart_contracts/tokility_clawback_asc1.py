from pyteal import *
from src.models.asset_configurations import ASAConfiguration
from src.smart_contracts.tokility_dex_asc1 import TokilityDEX


class TokilityClawbackASC1:

    def __init__(self,
                 configuration: ASAConfiguration,
                 app_id: int):
        self.configuration = configuration
        self.app_id = app_id

    def initial_buy(self):
        """
        Atomic Transfer:
        0. Application call.
        1. Payment from buyer to ASA_CREATOR.
        2. Asset transfer from Clawback to buyer.
        """

        return Seq([
            Assert(Gtxn[1].fee() <= Int(1000)),
            Assert(Gtxn[1].close_remainder_to() == Global.zero_address()),
            Assert(Gtxn[1].rekey_to() == Global.zero_address()),

            Assert(Gtxn[2].fee() <= Int(1000)),
            Assert(Gtxn[2].asset_close_to() == Global.zero_address()),
            Assert(Gtxn[2].rekey_to() == Global.zero_address()),

            Return(Int(1))
        ])

    def buy_from_seller(self):
        """
        Atomic Transfer:
        0. Application call.
        1. Payment from buyer to ASA_CREATOR. (creator fee)
        2. Payment from buyer to ASA_SELLER. (the actual price of the ASA on the asa offer)
        3. Payment from buyer to PLATFORM_ADDRESS. (platform fee)
        4. Asset transfer from Clawback to buyer.

        :return:
        """

        return Seq([
            Assert(Gtxn[1].fee() <= Int(1000)),
            Assert(Gtxn[1].close_remainder_to() == Global.zero_address()),
            Assert(Gtxn[1].rekey_to() == Global.zero_address()),

            Assert(Gtxn[2].fee() <= Int(1000)),
            Assert(Gtxn[2].close_remainder_to() == Global.zero_address()),
            Assert(Gtxn[3].rekey_to() == Global.zero_address()),

            Assert(Gtxn[3].fee() <= Int(1000)),
            Assert(Gtxn[3].close_remainder_to() == Global.zero_address()),
            Assert(Gtxn[3].rekey_to() == Global.zero_address()),

            Assert(Gtxn[4].fee() <= Int(1000)),
            Assert(Gtxn[4].asset_close_to() == Global.zero_address()),
            Assert(Gtxn[4].rekey_to() == Global.zero_address()),

            Return(Int(1))
        ])

    def gift_asa(self):
        """
        A ASA_OWNER transfers the ASA to a GIFT_ADDRESS for free. The ASA_OWNER only needs to pay
        the asa_owner fee to the ASA_CREATOR.
        This simulates gifting the ASA to a friend instead of selling it through sell offer.
        Arguments:
        - app_method_name: str
        - GIFT_ADDRESS: str - the address which will receive the ASA.

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to gift.

        Atomic Transfer:
        0. Application call.
        1. Payment from ASA_OWNER to ASA_CREATOR. (fees are paid to the asa_creator)
        2. Payment from ASA_OWNER to PLATFORM_ADDRESS.
        3. Asset transfer from Clawback to GIFT_ADDRESS.

        """
        return Seq([
            Assert(Gtxn[1].fee() <= Int(1000)),
            Assert(Gtxn[1].close_remainder_to() == Global.zero_address()),
            Assert(Gtxn[1].rekey_to() == Global.zero_address()),

            Assert(Gtxn[2].fee() <= Int(1000)),
            Assert(Gtxn[2].close_remainder_to() == Global.zero_address()),
            Assert(Gtxn[3].rekey_to() == Global.zero_address()),

            Assert(Gtxn[3].fee() <= Int(1000)),
            Assert(Gtxn[3].asset_close_to() == Global.zero_address()),
            Assert(Gtxn[3].rekey_to() == Global.zero_address()),

            Return(Int(1))
        ])

    def pyteal_code(self):
        is_initial_buy = Gtxn[0].application_args[0] == Bytes(TokilityDEX.AppMethods.initial_buy)
        is_second_hand_buy = Gtxn[0].application_args[0] == Bytes(TokilityDEX.AppMethods.buy_from_seller)
        is_gift = Gtxn[0].application_args[0] == Bytes(TokilityDEX.AppMethods.gift_asa)

        return Seq([
            Assert(Gtxn[0].application_id() == Int(self.app_id)),
            Cond(
                [is_initial_buy, self.initial_buy()],
                [is_second_hand_buy, self.buy_from_seller()],
                [is_gift, self.gift_asa()]
            )

        ])
