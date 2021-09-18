from algosdk.v2client import algod
from src.models.asset_configurations import ASAConfiguration
from src.blockchain_utils.transaction_repository import ApplicationTransactionRepository, PaymentTransactionRepository, \
    ASATransactionRepository
from src.services import NetworkInteraction
from src.smart_contracts.tokility_clawback_asc1 import TokilityClawbackASC1
from src.smart_contracts.tokility_dex_asc1 import TokilityDEX
import algosdk
from pyteal import compileTeal, Mode


class TokilityDEXService:
    def __init__(self,
                 app_creator_addr,
                 app_creator_pk,
                 client: algod.AlgodClient,
                 app_id=None):
        self.app_creator_addr = app_creator_addr
        self.app_creator_pk = app_creator_pk
        self.client = client

        self.app_id = app_id

        if app_id is None:
            self.app_id = self._deploy_application()

    def _deploy_application(self):
        tokility_dex = TokilityDEX()

        approval_program_compiled = compileTeal(tokility_dex.approval_program(),
                                                mode=Mode.Application,
                                                version=4)

        clear_program_compiled = compileTeal(tokility_dex.clear_program(),
                                             mode=Mode.Application,
                                             version=4)

        approval_program_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                    source_code=approval_program_compiled)

        clear_program_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                 source_code=clear_program_compiled)

        app_args = [
            algosdk.encoding.decode_address(self.app_creator_addr)
        ]
        app_transaction = ApplicationTransactionRepository.create_application(
            client=self.client,
            creator_private_key=self.app_creator_pk,
            approval_program=approval_program_bytes,
            clear_program=clear_program_bytes,
            global_schema=tokility_dex.global_schema,
            local_schema=tokility_dex.local_schema,
            # TODO: Maybe pass a new wallet address.
            app_args=app_args
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=app_transaction
        )

        transaction_response = self.client.pending_transaction_info(tx_id)

        app_id = transaction_response["application-index"]

        print('Application deployed')

        return app_id

    @staticmethod
    def dex_configuration_arguments(asa_configuration: ASAConfiguration):
        return [
            asa_configuration.asa_price_bytes,
            asa_configuration.tokiliy_fee_bytes,
            asa_configuration.max_sell_price_bytes,
            asa_configuration.owner_fee_bytes,
            asa_configuration.reselling_allowed_bytes,
            asa_configuration.reselling_end_date_bytes,
            asa_configuration.gifting_allowed_bytes,
            asa_configuration.asa_creator_address_bytes
        ]

    def fund_address(self, receiver_address: str, amount: int = 1000000):
        fund_clawback_txn = PaymentTransactionRepository.payment(
            client=self.client,
            sender_address=self.app_creator_addr,
            receiver_address=receiver_address,
            amount=amount,
            sender_private_key=self.app_creator_pk,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=fund_clawback_txn
        )

        return tx_id

    def app_opt_in(self, user_pk: str):
        txn = ApplicationTransactionRepository.app_opt_in(client=self.client,
                                                          caller_private_key=user_pk,
                                                          app_id=self.app_id)

        tx_id = NetworkInteraction.submit_transaction(self.client, txn)
        return tx_id

    def initial_buy(self,
                    buyer_addr: str,
                    buyer_pk: str,
                    asa_configuration: ASAConfiguration,
                    asa_clawback_addr: str,
                    asa_clawback_bytes):
        # 1. App call.
        app_args = [
            TokilityDEX.AppMethods.initial_buy
        ]
        app_args.extend(TokilityDEXService.dex_configuration_arguments(asa_configuration))

        app_call_txn = \
            ApplicationTransactionRepository.call_application(client=self.client,
                                                              caller_private_key=buyer_pk,
                                                              app_id=self.app_id,
                                                              on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                              app_args=app_args,
                                                              foreign_assets=[asa_configuration.asa_id],
                                                              sign_transaction=False)

        # 2. Payment transaction: buyer -> seller.
        asa_buy_payment_txn = \
            PaymentTransactionRepository.payment(client=self.client,
                                                 sender_address=buyer_addr,
                                                 receiver_address=asa_configuration.asa_creator_address,
                                                 amount=asa_configuration.initial_offering_configuration.asa_price,
                                                 sender_private_key=None,
                                                 sign_transaction=False)

        # 3. Asset transfer transaction: escrow -> buyer

        asa_transfer_txn = ASATransactionRepository.asa_transfer(client=self.client,
                                                                 sender_address=asa_clawback_addr,
                                                                 receiver_address=buyer_addr,
                                                                 amount=1,
                                                                 asa_id=asa_configuration.asa_id,
                                                                 revocation_target=asa_configuration.asa_creator_address,
                                                                 sender_private_key=None,
                                                                 sign_transaction=False)

        # Atomic transfer
        gid = algosdk.future.transaction.calculate_group_id([app_call_txn,
                                                             asa_buy_payment_txn,
                                                             asa_transfer_txn])

        app_call_txn.group = gid
        asa_buy_payment_txn.group = gid
        asa_transfer_txn.group = gid

        app_call_txn_signed = app_call_txn.sign(buyer_pk)

        asa_buy_txn_signed = asa_buy_payment_txn.sign(buyer_pk)

        asa_transfer_txn_logic_signature = algosdk.future.transaction.LogicSig(asa_clawback_bytes)
        asa_transfer_txn_signed = algosdk.future.transaction.LogicSigTransaction(asa_transfer_txn,
                                                                                 asa_transfer_txn_logic_signature)

        signed_group = [app_call_txn_signed,
                        asa_buy_txn_signed,
                        asa_transfer_txn_signed]

        tx_id = self.client.send_transactions(signed_group)

        print("Initial buy completed.")
        return tx_id

    def make_sell_offer(self,
                        seller_pk: str,
                        sell_price: int,
                        asa_configuration: ASAConfiguration):
        app_args = [
            TokilityDEX.AppMethods.sell_asa,
        ]
        app_args.extend(TokilityDEXService.dex_configuration_arguments(asa_configuration))
        app_args.append(sell_price)

        make_sell_order_txn = \
            ApplicationTransactionRepository.call_application(client=self.client,
                                                              caller_private_key=seller_pk,
                                                              app_id=self.app_id,
                                                              on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                              app_args=app_args,
                                                              foreign_assets=[asa_configuration.asa_id],
                                                              sign_transaction=True)

        tx_id = NetworkInteraction.submit_transaction(self.client, make_sell_order_txn)
        print("Sell order has been placed.")
        return tx_id

    def buy_from_seller(self,
                        buyer_addr: str,
                        buyer_pk: str,
                        seller_addr: str,
                        price: int,
                        asa_configuration: ASAConfiguration,
                        asa_clawback_addr: str,
                        asa_clawback_bytes):
        """
        Atomic Transfer:
        0. Application call.
        1. Payment from buyer to ASA_CREATOR. (fees are paid to the asa_creator)
        2. Payment from buyer to ASA_SELLER. (the actual price of the ASA on the asa offer)
        3. Payment from buyer to TOKILITY. (fees for the platform).
        4. Asset transfer from Clawback to buyer.
        """
        # 1. App call.
        app_args = [
            TokilityDEX.AppMethods.buy_from_seller
        ]
        app_args.extend(TokilityDEXService.dex_configuration_arguments(asa_configuration))

        # 0. Application call
        app_call_txn = \
            ApplicationTransactionRepository.call_application(client=self.client,
                                                              caller_private_key=buyer_pk,
                                                              app_id=self.app_id,
                                                              on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                              app_args=app_args,
                                                              accounts=[seller_addr],
                                                              foreign_assets=[asa_configuration.asa_id],
                                                              sign_transaction=False)

        # 1. Payment transaction: buyer -> asa creator.
        creator_fee_txn = \
            PaymentTransactionRepository.payment(client=self.client,
                                                 sender_address=buyer_addr,
                                                 receiver_address=asa_configuration.asa_creator_address,
                                                 amount=asa_configuration.economy_configuration.owner_fee,
                                                 sender_private_key=None,
                                                 sign_transaction=False)

        # 2. Payment transaction: buyer -> asa seller
        asa_sell_price_txn = \
            PaymentTransactionRepository.payment(client=self.client,
                                                 sender_address=buyer_addr,
                                                 receiver_address=seller_addr,
                                                 amount=price,
                                                 sender_private_key=None,
                                                 sign_transaction=False)

        # 3. Platform fees: buyer -> platform address
        platform_fee_txn = \
            PaymentTransactionRepository.payment(client=self.client,
                                                 sender_address=buyer_addr,
                                                 receiver_address=self.app_creator_addr,
                                                 amount=asa_configuration.initial_offering_configuration.tokiliy_fee,
                                                 sender_private_key=None,
                                                 sign_transaction=False)

        # 4. Asset transfer transaction: escrow -> buyer

        asa_transfer_txn = ASATransactionRepository.asa_transfer(client=self.client,
                                                                 sender_address=asa_clawback_addr,
                                                                 receiver_address=buyer_addr,
                                                                 amount=1,
                                                                 asa_id=asa_configuration.asa_id,
                                                                 revocation_target=seller_addr,
                                                                 sender_private_key=None,
                                                                 sign_transaction=False)

        # Atomic transfer
        gid = algosdk.future.transaction.calculate_group_id([app_call_txn,
                                                             creator_fee_txn,
                                                             asa_sell_price_txn,
                                                             platform_fee_txn,
                                                             asa_transfer_txn])

        app_call_txn.group = gid
        creator_fee_txn.group = gid
        asa_sell_price_txn.group = gid
        platform_fee_txn.group = gid
        asa_transfer_txn.group = gid

        app_call_txn_signed = app_call_txn.sign(buyer_pk)
        creator_fee_txn_txn_signed = creator_fee_txn.sign(buyer_pk)
        asa_sell_price_txn_signed = asa_sell_price_txn.sign(buyer_pk)
        platform_fee_txn_signed = platform_fee_txn.sign(buyer_pk)

        asa_transfer_txn_logic_signature = algosdk.future.transaction.LogicSig(asa_clawback_bytes)
        asa_transfer_txn_signed = algosdk.future.transaction.LogicSigTransaction(asa_transfer_txn,
                                                                                 asa_transfer_txn_logic_signature)

        signed_group = [app_call_txn_signed,
                        creator_fee_txn_txn_signed,
                        asa_sell_price_txn_signed,
                        platform_fee_txn_signed,
                        asa_transfer_txn_signed]

        tx_id = self.client.send_transactions(signed_group)

        print(f"Second hand buy completed in {tx_id}")
        return tx_id

    def stop_selling(self,
                     seller_pk: str,
                     asa_configuration: ASAConfiguration):
        app_args = [
            TokilityDEX.AppMethods.stop_selling,
        ]
        app_args.extend(TokilityDEXService.dex_configuration_arguments(asa_configuration))

        stop_sell_order_txn = \
            ApplicationTransactionRepository.call_application(client=self.client,
                                                              caller_private_key=seller_pk,
                                                              app_id=self.app_id,
                                                              on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                              app_args=app_args,
                                                              foreign_assets=[asa_configuration.asa_id],
                                                              sign_transaction=True)

        tx_id = NetworkInteraction.submit_transaction(self.client, stop_sell_order_txn)
        print("Sell order has been stopped.")
        return tx_id

    def gift_asa(self,
                 asa_owner_addr: str,
                 asa_owner_pk: str,
                 asa_receiver_addr: str,
                 asa_configuration: ASAConfiguration,
                 asa_clawback_addr: str,
                 asa_clawback_bytes):
        """
        Atomic Transfer:
        0. Application call.
        1. Payment from ASA_OWNER to ASA_CREATOR. (fees for creator).
        2. Payment from ASA_OWNER to TOKILITY_ADDR. (fees for platform).
        3. Asset transfer from Clawback to GIFT_ADDRESS.
        """
        # 1. App call.
        app_args = [
            TokilityDEX.AppMethods.gift_asa,
        ]
        app_args.extend(TokilityDEXService.dex_configuration_arguments(asa_configuration))

        app_args.append(algosdk.encoding.decode_address(asa_receiver_addr))

        # 0. Application call
        app_call_txn = \
            ApplicationTransactionRepository.call_application(client=self.client,
                                                              caller_private_key=asa_owner_pk,
                                                              app_id=self.app_id,
                                                              on_complete=algosdk.future.transaction.OnComplete.NoOpOC,
                                                              app_args=app_args,
                                                              foreign_assets=[asa_configuration.asa_id],
                                                              sign_transaction=False)

        # 1. Fee for the creator: asa_owner -> asa_creator
        creator_fee_txn = \
            PaymentTransactionRepository.payment(client=self.client,
                                                 sender_address=asa_owner_addr,
                                                 receiver_address=asa_configuration.asa_creator_address,
                                                 amount=asa_configuration.economy_configuration.owner_fee,
                                                 sender_private_key=None,
                                                 sign_transaction=False)

        # 2. Fee for the platform: asa_owner -> platform_address
        platform_fee_txn = \
            PaymentTransactionRepository.payment(client=self.client,
                                                 sender_address=asa_owner_addr,
                                                 receiver_address=self.app_creator_addr,
                                                 amount=asa_configuration.initial_offering_configuration.tokiliy_fee,
                                                 sender_private_key=None,
                                                 sign_transaction=False)

        # 3. Asset transfer transaction: escrow -> asa_receiver

        asa_transfer_txn = ASATransactionRepository.asa_transfer(client=self.client,
                                                                 sender_address=asa_clawback_addr,
                                                                 receiver_address=asa_receiver_addr,
                                                                 amount=1,
                                                                 asa_id=asa_configuration.asa_id,
                                                                 revocation_target=asa_owner_addr,
                                                                 sender_private_key=None,
                                                                 sign_transaction=False)

        # Atomic transfer
        gid = algosdk.future.transaction.calculate_group_id([app_call_txn,
                                                             creator_fee_txn,
                                                             platform_fee_txn,
                                                             asa_transfer_txn])

        app_call_txn.group = gid
        creator_fee_txn.group = gid
        platform_fee_txn.group = gid
        asa_transfer_txn.group = gid

        app_call_txn_signed = app_call_txn.sign(asa_owner_pk)

        creator_fee_txn_signed = creator_fee_txn.sign(asa_owner_pk)
        platform_fee_txn_signed = platform_fee_txn.sign(asa_owner_pk)

        asa_transfer_txn_logic_signature = algosdk.future.transaction.LogicSig(asa_clawback_bytes)
        asa_transfer_txn_signed = algosdk.future.transaction.LogicSigTransaction(asa_transfer_txn,
                                                                                 asa_transfer_txn_logic_signature)

        signed_group = [app_call_txn_signed,
                        creator_fee_txn_signed,
                        platform_fee_txn_signed,
                        asa_transfer_txn_signed]

        tx_id = self.client.send_transactions(signed_group)

        print("ASA has been gifted.")
        return tx_id
