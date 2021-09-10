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

            # Valid second transaction.
            Assert(Gtxn[1].type_enum() == TxnType.Payment),
            Assert(Gtxn[1].receiver() == Addr(self.configuration.asa_owner_address), ),
            Assert(Gtxn[1].amount() == Int(self.configuration.initial_offering_configuration.asa_price)),

            # Valid third transaction.
            Assert(Gtxn[2].type_enum() == TxnType.AssetTransfer),
            Assert(Gtxn[2].xfer_asset() == Int(self.configuration.asa_id)),

            # TODO: Later on this should be allowed to more instances to be bought at once.
            Assert(Gtxn[2].asset_amount() == Int(1)),
            Assert(Gtxn[2].fee() <= Int(1000)),
            Assert(Gtxn[2].asset_close_to() == Global.zero_address()),
            Assert(Gtxn[2].rekey_to() == Global.zero_address()),

            Return(Int(1))
        ])

    def pyteal_code(self):
        is_initial_buy = Gtxn[0].application_args[0] == Bytes(TokilityDEX.AppMethods.initial_buy)

        return Seq([
            Assert(Gtxn[0].application_id() == Int(self.app_id)),

            Cond(
                [is_initial_buy, self.initial_buy()]
            )

        ])
