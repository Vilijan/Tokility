from algosdk import account as algo_acc
from algosdk import logic as algo_logic
from pyteal import compileTeal, Mode

from src.blockchain_utils.transaction_repository import ASATransactionRepository, PaymentTransactionRepository
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration
from src.services.network_interaction import NetworkInteraction
from src.smart_contracts.asa_initial_offering_asc import initial_offering_asc


class AssetCreationService:
    def __init__(self,
                 asa_owner_pk: str,
                 unit_name: str,
                 asset_name: str,
                 total_supply: int,
                 initial_offering_configuration: ASAInitialOfferingConfiguration,
                 economy_configuration: ASAEconomyConfiguration,
                 teal_version: int = 3):

        self.asa_owner_pk = asa_owner_pk
        self.asa_owner_address = algo_acc.address_from_private_key(private_key=asa_owner_pk)
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.total_supply = total_supply
        self.teal_version = teal_version

        self.asa_id = None
        self.initial_offering_asc_address = ""
        self.initial_offering_configuration = initial_offering_configuration
        self.economy_configuration = economy_configuration

    def get_asa_configuration(self) -> ASAConfiguration:
        if self.asa_id is None:
            raise ValueError("The ASA has not been created.")

        return ASAConfiguration(asa_owner_address=self.asa_owner_address,
                                unit_name=self.unit_name,
                                asset_name=self.asset_name,
                                total_supply=self.total_supply,
                                asa_id=self.asa_id,
                                initial_offering_configuration=self.initial_offering_configuration,
                                economy_configuration=self.economy_configuration)

    def create_asa(self, client):
        transaction = ASATransactionRepository.create_asa(client=client,
                                                          creator_private_key=self.asa_owner_pk,
                                                          unit_name=self.unit_name,
                                                          asset_name=self.asset_name,
                                                          total=self.total_supply,
                                                          decimals=0,
                                                          manager_address=self.asa_owner_address,
                                                          reserve_address=self.asa_owner_address,
                                                          freeze_address=self.asa_owner_address,
                                                          clawback_address=self.asa_owner_address,
                                                          default_frozen=True)

        self.asa_id = NetworkInteraction.submit_asa_creation(client=client,
                                                             transaction=transaction)

    def setup_initial_offering_asc(self, client):
        """
        Set up the Smart Contract that is responsible for the initial offering of the ASA.
        :return:
        """
        if self.asa_id is None:
            raise ValueError('The Algorand Standard Asset of interest has not been created')

        configuration = self.get_asa_configuration()

        initial_offering_asc_compiled = compileTeal(initial_offering_asc(configuration=configuration),
                                                    mode=Mode.Signature,
                                                    version=self.teal_version)

        initial_offering_asc_bytes = NetworkInteraction.compile_program(client=client,
                                                                        source_code=initial_offering_asc_compiled)

        self.initial_offering_asc_address = algo_logic.address(initial_offering_asc_bytes)

        # fee deposit
        fee_transaction = PaymentTransactionRepository.payment(client=client,
                                                               sender_address=self.asa_owner_address,
                                                               receiver_address=self.initial_offering_asc_address,
                                                               amount=1000000,
                                                               sender_private_key=self.asa_owner_pk)
        NetworkInteraction.submit_transaction(client=client,
                                              transaction=fee_transaction)

    def change_asa_clawback_address(self, client):

        transaction = ASATransactionRepository.change_asa_management(client=client,
                                                                     current_manager_pk=self.asa_owner_pk,
                                                                     asa_id=self.asa_id,
                                                                     manager_address=self.asa_owner_address,
                                                                     reserve_address=self.asa_owner_address,
                                                                     freeze_address=self.asa_owner_address,
                                                                     clawback_address=self.initial_offering_asc_address,
                                                                     strict_empty_address_check=False)

        NetworkInteraction.submit_transaction(client=client, transaction=transaction)
