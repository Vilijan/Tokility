from pyteal import *

from src.models.asset_configurations import ASAConfiguration


def initial_offering_asc(configuration: ASAConfiguration):
    """
    This is the ASC that transfers the ASA from the seller wallet to the buyer according to the
    passed configuration.

    :param configuration: Configuration that defines the behavior of the initial offering of the ASA.
    :return:
    """
    are_valid_transaction_types = And(Gtxn[0].type_enum() == TxnType.Payment,
                                      Gtxn[1].type_enum() == TxnType.AssetTransfer)

    are_asa_buyer_and_seller_same = Gtxn[0].sender() == Gtxn[1].asset_receiver()

    is_correct_asa_id = Gtxn[1].xfer_asset() == Int(configuration.asa_id)

    is_correct_funds_receiver = Gtxn[0].receiver() == Addr(configuration.asa_owner_address)

    # Price
    asa_price = Int(configuration.initial_offering_configuration.asa_price)
    actual_asa_amount = Gtxn[1].asset_amount() * asa_price
    is_correct_amount = Gtxn[0].amount() == actual_asa_amount

    # Fees
    fee_1 = Gtxn[0].fee() <= Int(1000)
    fee_2 = Gtxn[1].fee() <= Int(1000)
    are_fees_acceptable = And(fee_1, fee_2)

    # Some checks ?
    is_valid_close_to_address = Gtxn[1].asset_close_to() == Global.zero_address()
    is_valid_rekey_to_address = Gtxn[1].rekey_to() == Global.zero_address()

    # TODO: we should check how much ASA that the buyer currently owns.

    return And(are_valid_transaction_types,
               are_asa_buyer_and_seller_same,
               is_correct_asa_id,
               is_correct_funds_receiver,
               is_correct_amount,
               are_fees_acceptable,
               is_valid_close_to_address,
               is_valid_rekey_to_address)
