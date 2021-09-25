from abc import ABC, abstractmethod
import algosdk
from pyteal import *


class TokilityDEXInterface(ABC):

    @abstractmethod
    def initial_buy(self):
        pass

    @abstractmethod
    def sell_asa(self):
        pass

    @abstractmethod
    def buy_from_seller(self):
        pass

    @abstractmethod
    def stop_selling(self):
        pass

    @abstractmethod
    def gift_asa(self):
        pass


class TokilityDEX(TokilityDEXInterface):
    """
    Stateful smart contract that implements the tokility DEX.
    When executing methods of this smart contract, the first 9 parameters are fixed.
    1. Method of the name
    2-9. Tokility Token configuration. sha256(args[1]...args[8]) == ASA.Metadata Hash
    This ensures that whenever we try to interact we the token we are following the rules defined by the owner.
    """

    class AppMethods:
        initial_buy = "initial_buy"
        sell_asa = "sell_asa"
        buy_from_seller = "buy_from_seller"
        stop_selling = "stop_selling"
        gift_asa = "gift_asa"

    class ASAConfiguration:
        asa_price = Btoi(Txn.application_args[1])
        tokility_fee = Btoi(Txn.application_args[2])
        max_sell_price = Btoi(Txn.application_args[3])
        creator_fee = Btoi(Txn.application_args[4])
        reselling_allowed = Btoi(Txn.application_args[5])
        reselling_end_date = Btoi(Txn.application_args[6])
        gifting_allowed = Btoi(Txn.application_args[7])
        creator_address = Txn.application_args[8]

    class GlobalVariables:
        tokility_fee_address = Bytes("tokility_fee_address")

    MIN_NUM_PARAMETERS = 9

    def application_start(self):
        return Cond(
            [Txn.on_completion() == OnComplete.OptIn, self.approve],
            [Txn.application_id() == Int(0), self.initialize_app()],
            [Int(1), self.execute_actions()]

        )

    def execute_actions(self):
        metadata_hash = AssetParam.metadataHash(asset=Txn.assets[0])
        concat_args = Concat(Txn.application_args[1],
                             Bytes('-'),
                             Txn.application_args[2],
                             Bytes('-'),
                             Txn.application_args[3],
                             Bytes('-'),
                             Txn.application_args[4],
                             Bytes('-'),
                             Txn.application_args[5],
                             Bytes('-'),
                             Txn.application_args[6],
                             Bytes('-'),
                             Txn.application_args[7],
                             Bytes('-'),
                             Txn.application_args[8])

        return Seq([
            metadata_hash,
            Assert(metadata_hash.hasValue()),
            Assert(metadata_hash.value() == Sha256(concat_args)),

            Cond([Txn.application_args[0] == Bytes(self.AppMethods.initial_buy),
                  self.initial_buy()],

                 [Txn.application_args[0] == Bytes(self.AppMethods.sell_asa),
                  self.sell_asa()],

                 [Txn.application_args[0] == Bytes(self.AppMethods.buy_from_seller),
                  self.buy_from_seller()],

                 [Txn.application_args[0] == Bytes(self.AppMethods.stop_selling),
                  self.stop_selling()],

                 [Txn.application_args[0] == Bytes(self.AppMethods.gift_asa),
                  self.gift_asa()])
        ])

    @property
    def approve(self):
        return Return(Int(1))

    def _valid_payment_creator_fee(self, group_tx_id):
        return Assert(And(Gtxn[group_tx_id].type_enum() == TxnType.Payment,
                          Gtxn[group_tx_id].receiver() == self.ASAConfiguration.creator_address,
                          Gtxn[group_tx_id].amount() == self.ASAConfiguration.creator_fee))

    def _valid_payment_tokility_fee(self, group_tx_id):
        tokility_fee_address = App.globalGet(self.GlobalVariables.tokility_fee_address)
        return Assert(And(Gtxn[group_tx_id].type_enum() == TxnType.Payment,
                          Gtxn[group_tx_id].receiver() == tokility_fee_address,
                          Gtxn[group_tx_id].amount() == self.ASAConfiguration.tokility_fee))

    def initialize_app(self):
        """
        Setup the tokility address in the global variable address.
        :return:
        """
        return Seq([
            App.globalPut(self.GlobalVariables.tokility_fee_address, Txn.application_args[0]),
            Return(Int(1))
        ])

    def initial_buy(self):
        """
        Arguments:
        1. app_method_name: str
        [2-9]. config arguments

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to buy.

        Atomic Transfer:
        0. Application call.
        1. Payment from buyer to ASA_CREATOR.
        2. Asset transfer from Clawback to buyer.
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

            # Valid app call transaction
            Assert(Global.group_size() == Int(3)),
            Assert(Txn.application_args.length() == Int(self.MIN_NUM_PARAMETERS)),
            Assert(Gtxn[0].sender() == Gtxn[1].sender()),

            # Valid payment transaction
            Assert(Gtxn[1].type_enum() == TxnType.Payment),
            Assert(Gtxn[1].receiver() == self.ASAConfiguration.creator_address),
            Assert(Gtxn[1].amount() == self.ASAConfiguration.asa_price),

            # Valid asset transfer
            Assert(Gtxn[2].asset_amount() == Int(1)),  # Currently we only support NFTs... this should change.
            Assert(Gtxn[2].xfer_asset() == Txn.assets[0]),
            Assert(Gtxn[2].asset_receiver() == Txn.sender()),

            Return(Int(1))
        ])

    def sell_asa(self):
        """
         Arguments:
        1. app_method_name: str
        [2-9]. config arguments
        10. asa_price: int - the price of the ASA in microAlgos

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to sell.

        Single transaction:
        0. Application call.
        :return:
        """
        #
        asa_balance = AssetHolding.balance(
            Txn.sender(),
            Txn.assets[0],
        )

        return Seq([
            Assert(Txn.assets.length() == Int(1)),
            Assert(Txn.application_args.length() == Int(self.MIN_NUM_PARAMETERS + 1)),

            # Checks whether the sender that wants to sell the ASA actually owns that ASA.
            asa_balance,
            Assert(asa_balance.hasValue()),
            Assert(
                Ge(
                    asa_balance.value(),
                    Int(1),
                )
            ),

            # Are you allowed to sell.
            Assert(self.ASAConfiguration.reselling_allowed == Int(1)),
            Assert(Global.latest_timestamp() < self.ASAConfiguration.reselling_end_date),

            # Set the local state of that sender.
            App.localPut(Txn.sender(), Itob(Txn.assets[0]), Btoi(Txn.application_args[9])),
            Return(Int(1))
        ])

    def buy_from_seller(self):
        """
        The escrow handles the fees setup in the asa_configuration. In this call we need
        to make sure that the seller has made a selling offer and owns the ASA.
        Arguments:
        1. app_method_name: str
        [2-9]. config arguments

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to buy.

        Accounts:
        - address of the seller

        Atomic Transfer:
        0. Application call.
        1. Payment from buyer to ASA_CREATOR. (fees are paid to the asa_creator)
        2. Payment from buyer to ASA_SELLER. (the actual price of the ASA on the asa offer)
        3. Payment from buyer to TOKILITY. (fees for the platform).
        4. Asset transfer from Clawback to buyer.

        :return:
        """
        asa_sell_offer = App.localGetEx(Txn.accounts[1], Txn.application_id(), Itob(Txn.assets[0]))

        return Seq([
            Assert(Txn.accounts.length() == Int(1)),
            Assert(Txn.assets.length() == Int(1)),
            Assert(Txn.application_args.length() == Int(self.MIN_NUM_PARAMETERS)),
            Assert(Global.group_size() == Int(5)),

            # has made a sell offer.
            asa_sell_offer,
            Assert(asa_sell_offer.hasValue()),

            # is allowed to buy it from the configuration constraints.
            Assert(Global.latest_timestamp() < self.ASAConfiguration.reselling_end_date),
            Assert(self.ASAConfiguration.reselling_allowed == Int(1)),

            # application call
            Assert(Gtxn[0].sender() == Gtxn[1].sender()),
            Assert(Gtxn[0].sender() == Gtxn[2].sender()),
            Assert(Gtxn[0].sender() == Gtxn[3].sender()),

            # payment to creator, handle creator fees.
            self._valid_payment_creator_fee(group_tx_id=1),

            # payment to seller, official sale.
            Assert(Gtxn[2].type_enum() == TxnType.Payment),
            Assert(Gtxn[2].receiver() == Txn.accounts[1]),
            Assert(Gtxn[2].amount() == asa_sell_offer.value()),

            # payment to tokility, handle platform fees.
            self._valid_payment_tokility_fee(group_tx_id=3),

            # asset transfer.
            Assert(Gtxn[4].type_enum() == TxnType.AssetTransfer),
            Assert(Gtxn[4].xfer_asset() == Txn.assets[0]),
            Assert(Gtxn[4].asset_receiver() == Gtxn[0].sender()),
            Assert(Gtxn[4].asset_amount() == Int(1)),

            # remove the sell_offer since it has been executed.
            App.localDel(Txn.accounts[1], Itob(Txn.assets[0])),

            self.approve
        ])

    def stop_selling(self):
        """
         Arguments:
        - app_method_name: str

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to stop the sell order.

        Single transaction:
        1. Application call.
        :return:
        """
        return Seq([
            Assert(Txn.assets.length() == Int(1)),
            App.localDel(Txn.sender(), Itob(Txn.assets[0])),
            self.approve
        ])

    def gift_asa(self):
        """
        A ASA_OWNER transfers the ASA to a GIFT_ADDRESS for free. The ASA_OWNER only needs to pay
        the asa_owner fee to the ASA_CREATOR.
        This simulates gifting the ASA to a friend instead of selling it through sell offer.
        1. app_method_name: str
        [2-9]. config arguments
        10. GIFT_ADDRESS: str - the address which will receive the ASA.

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to buy.

        Foreign assets:
        - asa_id - the ID of the asa that the user wants to gift.

        Atomic Transfer:
        0. Application call.
        1. Payment from ASA_OWNER to ASA_CREATOR. (fees for creator).
        2. Payment from ASA_OWNER to TOKILITY_ADDR. (fees for platform).
        3. Asset transfer from Clawback to GIFT_ADDRESS.

        :return:
        """
        asa_balance = AssetHolding.balance(
            Txn.sender(),
            Txn.assets[0],
        )

        return Seq([
            Assert(Txn.assets.length() == Int(1)),
            Assert(Txn.application_args.length() == Int(self.MIN_NUM_PARAMETERS + 1)),

            # Checks whether the sender that wants to gift the ASA actually owns that ASA.
            asa_balance,
            Assert(asa_balance.hasValue()),
            Assert(
                Ge(
                    asa_balance.value(),
                    Int(1),
                )
            ),

            # allowed to gift
            Assert(self.ASAConfiguration.gifting_allowed == Int(1)),

            # payment to creator, handle creator fees.
            self._valid_payment_creator_fee(group_tx_id=1),

            # payment to tokility, handle platform fees.
            self._valid_payment_tokility_fee(group_tx_id=2),

            # Valid third transaction
            Assert(Gtxn[3].asset_receiver() == Txn.application_args[9]),
            Assert(Txn.assets[0] == Gtxn[3].xfer_asset()),
            Assert(Gtxn[3].asset_amount() == Int(1)),

            self.approve
        ])

    def approval_program(self):
        return self.application_start()

    def clear_program(self):
        return self.approve

    @property
    def global_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=0,
                                                      num_byte_slices=1)

    @property
    def local_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=16,
                                                      num_byte_slices=0)
