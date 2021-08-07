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


class AppMethods:
    buy_asa = Bytes("buy_asa")
    sell_asa = Bytes("sell_asa")
    stop_selling_asa = Bytes("stop_selling_asa")
    asa_withdraw = Bytes("asa_withdraw")


def application_start(asa_configuration: ASAConfiguration):
    is_app_initialization = Txn.application_id() == Int(0)
    #
    # actions = Cond(
    #     [Txn.application_args[0] == AppActions.SetupPlayers, initialize_players_logic()],
    #     [And(Txn.application_args[0] == AppActions.ActionMove,
    #          Global.group_size() == Int(1)), play_action_logic()],
    #     [Txn.application_args[0] == AppActions.MoneyRefund, money_refund_logic()]
    # )

    return If(is_app_initialization) \
        .Then(app_initialization_logic(asa_configuration))


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
        App.globalPut(AppVariables.ASA_ID, Int(1)),
        Return(Int(1))
    ])


def approval_program(asa_configuration: ASAConfiguration):
    return application_start(asa_configuration)


def clear_program():
    return Return(Int(1))
