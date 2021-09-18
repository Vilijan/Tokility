from algosdk.v2client import algod
from src.models.asset_configurations import ASAConfiguration
from src.blockchain_utils.transaction_repository import ASATransactionRepository
from src.services import NetworkInteraction
from src.smart_contracts.tokility_clawback_asc1 import TokilityClawbackASC1
import algosdk
from pyteal import compileTeal, Mode
from hashlib import sha256


class ASAService:
    def __init__(self,
                 creator_addr: str,
                 creator_pk: str,
                 tokility_dex_app_id: int,
                 client: algod.AlgodClient):
        self.creator_addr = creator_addr
        self.creator_pk = creator_pk
        self.tokility_dex_app_id = tokility_dex_app_id
        self.client = client

        self.database = dict()

    def create_asa(self, asa_configuration: ASAConfiguration):
        """
        Creates an ASA from the given ASAConfiguration.
        :param asa_configuration: Configuration that defines the ASA.
        :return: (int, str): returns the tuple of the ASA_ID and the TXN_ID that created the ASA.
        """
        txn = ASATransactionRepository.create_non_fungible_asa(
            client=self.client,
            creator_private_key=self.creator_pk,
            unit_name=asa_configuration.unit_name,
            asset_name=asa_configuration.asset_name,
            note=None,
            manager_address=self.creator_addr,
            reserve_address=self.creator_addr,
            freeze_address=self.creator_addr,
            clawback_address=self.creator_addr,
            url=None,
            metadata_hash=sha256(asa_configuration.metadata_hash).digest(),
            default_frozen=True,
            sign_transaction=True,
        )

        asa_id, tx_id = NetworkInteraction.submit_asa_creation(client=self.client,
                                                               transaction=txn)

        asa_configuration.asa_id = asa_id

        self.database[asa_id] = dict()
        self.database[asa_id]["configuration"] = asa_configuration.dict()

        return asa_id, tx_id

    def create_clawback(self, asa_configuration: ASAConfiguration):
        """
        Creates clawback for the specified asa configuration.
        :param asa_configuration:
        :return: (str, bytes) - clawback address and clawback bytes compiled.
        """
        tokility_clawback_asc1 = TokilityClawbackASC1(configuration=asa_configuration,
                                                      app_id=self.tokility_dex_app_id)

        clawback_asc1_compiled = compileTeal(tokility_clawback_asc1.pyteal_code(),
                                             mode=Mode.Signature,
                                             version=4)

        clawback_asc1_compiled_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                          source_code=clawback_asc1_compiled)

        clawback_address = algosdk.logic.address(clawback_asc1_compiled_bytes)

        self.database[asa_configuration.asa_id]["clawback_address"] = clawback_address
        self.database[asa_configuration.asa_id]["clawback_bytes"] = clawback_asc1_compiled_bytes

        return clawback_address, clawback_asc1_compiled_bytes

    def update_asa_management(self,
                              asa_id: int,
                              manager_address: str,
                              reserve_address: str,
                              freeze_address: str,
                              clawback_address: str):
        txn = ASATransactionRepository.change_asa_management(
            client=self.client,
            current_manager_pk=self.creator_pk,
            asa_id=asa_id,
            manager_address=manager_address,
            reserve_address=reserve_address,
            freeze_address=freeze_address,
            strict_empty_address_check=False,
            clawback_address=clawback_address,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=txn)

        return tx_id

    def asa_opt_in(self, asa_id, user_pk):
        txn = ASATransactionRepository.asa_opt_in(client=self.client,
                                                  sender_private_key=user_pk,
                                                  asa_id=asa_id)

        tx_id = NetworkInteraction.submit_transaction(self.client,
                                                      transaction=txn)

        return tx_id
