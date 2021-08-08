from pyteal import *
from src.models.asset_configurations import ASAConfiguration


class AppVariables:
    ASACreatorAddress = Bytes("ASACreatorAddress")
    ASAOwnerAddress = Bytes("ASAOwnerAddress")

    ASAMaxPrice = Bytes("ASAMaxPrice")
    ResellOwnerFee = Bytes("ResellOwnerFee")

    ASACurrentSellPrice = Bytes("ASACurrentSellPrice")
    IsAppActive = Bytes("IsAppActive")

    ASA_ID = Bytes("ASA_ID")

    EscrowAddress = Bytes("EscrowAddress")


class AppMethods:
    buy_asa = Bytes("buy_asa")
    sell_asa = Bytes("sell_asa")
    stop_selling_asa = Bytes("stop_selling_asa")
    use_asa = Bytes("use_asa")
    initialize_escrow = Bytes("initialize_escrow")


def application_start(asa_configuration: ASAConfiguration):
    is_app_initialization = Txn.application_id() == Int(0)

    actions = Cond(
        [Txn.application_args[0] == AppMethods.buy_asa, buy_asa_from_owner_logic()],
        [Txn.application_args[0] == AppMethods.initialize_escrow, initialize_escrow_logic()],
        [Txn.application_args[0] == AppMethods.stop_selling_asa, stop_selling_asa_logic()],
        [Txn.application_args[0] == AppMethods.sell_asa, sell_asa_logic()],
        [Txn.application_args[0] == AppMethods.use_asa, use_asa_logic()]
    )

    return If(is_app_initialization) \
        .Then(app_initialization_logic(asa_configuration)).Else(actions)


def app_initialization_logic(asa_configuration: ASAConfiguration):
    asa_initial_price = asa_configuration.initial_offering_configuration.asa_price
    asa_max_price = asa_configuration.economy_configuration.max_sell_price
    creator_fee = asa_configuration.economy_configuration.owner_fee
    return Seq([
        App.globalPut(AppVariables.ASACreatorAddress, Addr(asa_configuration.asa_owner_address)),
        App.globalPut(AppVariables.ASAOwnerAddress, Addr(asa_configuration.asa_owner_address)),
        App.globalPut(AppVariables.ASAMaxPrice, Int(asa_max_price)),
        App.globalPut(AppVariables.ResellOwnerFee, Int(creator_fee)),
        App.globalPut(AppVariables.ASACurrentSellPrice, Int(asa_initial_price)),
        App.globalPut(AppVariables.IsAppActive, Int(1)),
        App.globalPut(AppVariables.ASA_ID, Int(asa_configuration.asa_id)),
        Return(Int(1))
    ])


def initialize_escrow_logic():
    escrow_address = App.globalGetEx(Int(0), AppVariables.EscrowAddress)

    setup_failed = Seq([
        Return(Int(0))
    ])

    setup_escrow = Seq([
        App.globalPut(AppVariables.EscrowAddress, Txn.application_args[1]),
        Return(Int(1))
    ])

    return Seq([
        escrow_address,
        If(escrow_address.hasValue()).Then(setup_failed).Else(setup_escrow)
    ])


def buy_asa_from_owner_logic():
    is_first_sell = App.globalGet(AppVariables.ASAOwnerAddress) == App.globalGet(AppVariables.ASACreatorAddress)
    asa_can_be_bought = App.globalGet(AppVariables.ASACurrentSellPrice) != Int(0)
    is_app_active = App.globalGet(AppVariables.IsAppActive) == Int(1)

    # valid second transaction
    valid_escrow = App.globalGet(AppVariables.EscrowAddress) == Gtxn[1].sender()

    # valid third transaction
    correct_funds_receiver = App.globalGet(AppVariables.ASAOwnerAddress) == Gtxn[2].receiver()
    correct_price = App.globalGet(AppVariables.ASACurrentSellPrice) == Gtxn[2].amount()

    update_state = Seq([
        App.globalPut(AppVariables.ASAOwnerAddress, Gtxn[2].sender()),
        App.globalPut(AppVariables.ASACurrentSellPrice, Int(0)),
        Return(Int(1))
    ])

    valid_logic = And(is_first_sell,
                      asa_can_be_bought,
                      is_app_active,
                      valid_escrow,
                      correct_funds_receiver,
                      correct_price)

    return If(valid_logic).Then(update_state).Else(Return(Int(0)))


def stop_selling_asa_logic():
    is_app_active = App.globalGet(AppVariables.IsAppActive) == Int(1)

    valid_caller = Txn.sender() == App.globalGet(AppVariables.ASAOwnerAddress)

    disable_selling = Seq([
        App.globalPut(AppVariables.ASACurrentSellPrice, Int(0)),
        Return(Int(1))
    ])

    return If(And(is_app_active, valid_caller)).Then(disable_selling).Else(Return(Int(0)))


def sell_asa_logic():
    is_app_active = App.globalGet(AppVariables.IsAppActive) == Int(1)
    valid_caller = Txn.sender() == App.globalGet(AppVariables.ASAOwnerAddress)
    new_sell_price = Btoi(Txn.application_args[1]) + App.globalGet(AppVariables.ResellOwnerFee)
    valid_price = new_sell_price <= App.globalGet(AppVariables.ASAMaxPrice)

    valid_selling_logic = And(is_app_active,
                              valid_caller,
                              valid_price)

    update_sell_price = Seq([
        App.globalPut(AppVariables.ASACurrentSellPrice, new_sell_price),
        Return(Int(1))
    ])

    return If(valid_selling_logic).Then(update_sell_price).Else(Return(Int(0)))


def use_asa_logic():
    is_app_active = App.globalGet(AppVariables.IsAppActive) == Int(1)
    valid_caller = Txn.sender() == App.globalGet(AppVariables.ASACreatorAddress)

    can_use_asa = And(is_app_active, valid_caller)

    return If(can_use_asa) \
        .Then(Seq([App.globalPut(AppVariables.IsAppActive, Int(0)),
                   Return(Int(1))])) \
        .Else(Return(Int(0)))


def approval_program(asa_configuration: ASAConfiguration):
    return application_start(asa_configuration)


def clear_program():
    return Return(Int(1))
