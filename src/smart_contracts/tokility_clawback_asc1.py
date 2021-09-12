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
        Arguments:
        - app_method_name: str

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to buy.

        Atomic Transfer:
        1. Application call.
        2. Payment from buyer to ASA_CREATOR.
        3. Asset transfer from Clawback to buyer.

        :return:
        """

        return Seq([
            Assert(Global.group_size() == Int(3)),

            # Valid first transaction
            Assert(Gtxn[0].type_enum() == TxnType.ApplicationCall),
            Assert(Gtxn[0].sender() == Gtxn[1].sender()),

            # Valid second transaction.
            Assert(Gtxn[1].type_enum() == TxnType.Payment),
            Assert(Gtxn[1].receiver() == Addr(self.configuration.asa_owner_address)),
            Assert(Gtxn[1].amount() == Int(self.configuration.initial_offering_configuration.asa_price)),

            # Valid third transaction.
            Assert(Gtxn[2].type_enum() == TxnType.AssetTransfer),
            Assert(Gtxn[2].xfer_asset() == Int(self.configuration.asa_id)),
            Assert(Gtxn[2].asset_receiver() == Gtxn[0].sender()),

            # TODO: Later on this should be allowed to more instances to be bought at once.
            Assert(Gtxn[2].asset_amount() == Int(1)),
            Assert(Gtxn[2].fee() <= Int(1000)),
            Assert(Gtxn[2].asset_close_to() == Global.zero_address()),
            Assert(Gtxn[2].rekey_to() == Global.zero_address()),

            Return(Int(1))
        ])

    def buy_from_seller(self):
        """
        Arguments:
        - app_method_name: str

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to buy.

        Accounts:
        - seller_account - the account address of the seller.

        Atomic Transfer:
        1. Application call.
        2. Payment from buyer to ASA_CREATOR. (fees are paid to the asa_creator)
        3. Payment from buyer to ASA_SELLER. (the actual price of the ASA on the asa offer)
        4. Asset transfer from Clawback to buyer.

        :return:
        """

        return Seq([
            Assert(Global.group_size() == Int(4)),

            # Valid first transaction.
            Assert(Gtxn[0].type_enum() == TxnType.ApplicationCall),
            Assert(Gtxn[0].sender() == Gtxn[1].sender()),
            Assert(Gtxn[0].sender() == Gtxn[2].sender()),

            # Valid second transaction.
            Assert(Gtxn[1].type_enum() == TxnType.Payment),
            Assert(Gtxn[1].receiver() == Addr(self.configuration.asa_owner_address)),
            Assert(Gtxn[1].amount() == Int(self.configuration.economy_configuration.owner_fee)),

            # # Valid third transaction.
            Assert(Gtxn[2].type_enum() == TxnType.Payment),
            Assert(Gtxn[2].amount() <= Int(self.configuration.economy_configuration.max_sell_price)),
            # The amount and the receiver of this transaction is validated in the dex application.


            # # Valid forth transaction.
            Assert(Gtxn[3].type_enum() == TxnType.AssetTransfer),
            Assert(Gtxn[3].xfer_asset() == Int(self.configuration.asa_id)),
            Assert(Gtxn[3].asset_receiver() == Gtxn[0].sender()),

            # TODO: Later on this should be allowed to more instances to be bought at once.
            Assert(Gtxn[3].asset_amount() == Int(1)),
            Assert(Gtxn[3].fee() <= Int(1000)),
            Assert(Gtxn[3].asset_close_to() == Global.zero_address()),
            Assert(Gtxn[3].rekey_to() == Global.zero_address()),

            Return(Int(1))
        ])

    def pyteal_code(self):
        is_initial_buy = Gtxn[0].application_args[0] == Bytes(TokilityDEX.AppMethods.initial_buy)
        is_second_hand_buy = Gtxn[0].application_args[0] == Bytes(TokilityDEX.AppMethods.buy_from_seller)

        return Seq([
            Assert(Gtxn[0].application_id() == Int(self.app_id)),
            Assert(Gtxn[0].application_args.length() == Int(1)),
            Cond(
                [is_initial_buy, self.initial_buy()],
                [is_second_hand_buy, self.buy_from_seller()]
            )

        ])
