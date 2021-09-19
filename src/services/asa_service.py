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

    @property
    def clawback_address_bytes(self):
        tokility_clawback_asc1 = TokilityClawbackASC1(app_id=self.tokility_dex_app_id)

        clawback_asc1_compiled = compileTeal(tokility_clawback_asc1.pyteal_code(),
                                             mode=Mode.Signature,
                                             version=4)

        clawback_asc1_compiled_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                          source_code=clawback_asc1_compiled)

        return clawback_asc1_compiled_bytes

    @property
    def clawback_address(self):
        return algosdk.logic.address(self.clawback_address_bytes)

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
            manager_address="",
            reserve_address="",
            freeze_address="",
            clawback_address=self.clawback_address,
            url=asa_configuration.configuration_ipfs_url,
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

    def asa_opt_in(self, asa_id, user_pk):
        txn = ASATransactionRepository.asa_opt_in(client=self.client,
                                                  sender_private_key=user_pk,
                                                  asa_id=asa_id)

        tx_id = NetworkInteraction.submit_transaction(self.client,
                                                      transaction=txn)

        return tx_id
