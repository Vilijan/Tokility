from abc import ABC, abstractmethod
import algosdk
from pyteal import *


class TokilityDEXInterface(ABC):

    @abstractmethod
    def initial_buy(self, asa_id):
        # asa_id
        pass

    @abstractmethod
    def sell_asa(self):
        # asa_id, price
        pass

    @abstractmethod
    def buy_from_seller(self):
        # asa_id, seller_address
        pass

    @abstractmethod
    def stop_selling(self):
        # asa_id
        pass

    @abstractmethod
    def gift_asa(self, asa_id, receiver_address):
        # asa_id, receiver_address
        pass


class TokilityDEX(TokilityDEXInterface):
    class AppMethods:
        initial_buy = "initial_buy"
        sell_asa = "sell_asa"
        buy_from_seller = "buy_from_seller"
        stop_selling = "stop_selling"
        gift_asa = "gift_asa"

    def application_start(self):
        actions = Cond(
            [Txn.application_id() == Int(0), self.app_initialization()],

            [Txn.application_args[0] == Bytes(self.AppMethods.initial_buy),
             self.initial_buy()],

            [Txn.application_args[0] == Bytes(self.AppMethods.sell_asa),
             self.sell_asa()],

            [Txn.application_args[0] == Bytes(self.AppMethods.buy_from_seller),
             self.buy_from_seller()],

            [Txn.application_args[0] == Bytes(self.AppMethods.buy_from_seller),
             self.stop_selling()],

            [Txn.application_args[0] == Bytes(self.AppMethods.gift_asa),
             self.gift_asa()]
        )
        return If(Txn.on_completion() == OnComplete.OptIn) \
            .Then(self.app_opt_in()) \
            .Else(actions)

    def app_opt_in(self):
        return Return(Int(1))

    def app_initialization(self):
        return Return(Int(1))

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

        # We want to make sure that we are buying a tokility NFT. The NFT
        # should be frozen and have only a clawback address.

        asset_escrow = AssetParam.clawback(Txn.assets[0])
        manager_address = AssetParam.manager(Txn.assets[0])
        freeze_address = AssetParam.freeze(Txn.assets[0])
        reserve_address = AssetParam.reserve(Txn.assets[0])
        default_frozen = AssetParam.defaultFrozen(Txn.assets[0])

        return Seq([
            Assert(Global.group_size() == Int(3)),

            # Valid Token
            asset_escrow,
            manager_address,
            freeze_address,
            reserve_address,
            default_frozen,
            Assert(asset_escrow.hasValue()),
            Assert(default_frozen.value()),
            Assert(manager_address.value() == Global.zero_address()),
            Assert(freeze_address.value() == Global.zero_address()),
            Assert(reserve_address.value() == Global.zero_address()),

            # # Valid receiver
            Assert(Gtxn[2].xfer_asset() == Txn.assets[0]),

            Assert(Gtxn[2].asset_receiver() == Gtxn[1].sender()),
            Assert(Gtxn[1].sender() == Gtxn[0].sender()),

            Assert(Txn.application_args.length() == Int(1)),

            Return(Int(1))
        ])

    def sell_asa(self):
        """
         Arguments:
        - app_method_name: str
        - asa_price: int - the price of the ASA in microAlgos

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to sell.

        Atomic Transfer:
        1. Application call.
        :return:
        """
        #

        asa_balance = AssetHolding.balance(
            Txn.sender(),
            Txn.assets[0],
        )

        return Seq([
            # Checks whether the sender that wants to sell the ASA actually owns that ASA.

            asa_balance,
            Assert(asa_balance.hasValue()),
            Assert(
                Ge(
                    asa_balance.value(),
                    Int(1),
                )
            ),

            # Set the local state of that sender.
            App.localPut(Txn.sender(), Itob(Txn.assets[0]), Btoi(Txn.application_args[1])),

            Return(Int(1))
        ])

    def buy_from_seller(self):
        return Return(Int(0))

    def stop_selling(self):
        return Return(Int(0))

    def gift_asa(self):
        return Return(Int(0))

    def approval_program(self):
        return self.application_start()

    def clear_program(self):
        return Return(Int(1))

    @property
    def global_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=0,
                                                      num_byte_slices=0)

    @property
    def local_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=16,
                                                      num_byte_slices=0)
