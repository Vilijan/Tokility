from pyteal import *
from src.models.asset_configurations import ASAConfiguration


def asa_escrow(app_id: int,
               asa_configuration: ASAConfiguration):
    return Seq([
        Assert(Gtxn[0].application_id() == Int(app_id)),
        Assert(Gtxn[1].asset_amount() == Int(1)),
        Assert(Gtxn[1].xfer_asset() == Int(asa_configuration.asa_id)),
        Assert(Gtxn[1].fee() <= Int(1000)),
        Assert(Gtxn[1].asset_close_to() == Global.zero_address()),
        Assert(Gtxn[1].rekey_to() == Global.zero_address()),

        Assert(Gtxn[2].type_enum() == TxnType.Payment),
        Assert(Gtxn[2].asset_close_to() == Global.zero_address()),
        Assert(Gtxn[2].rekey_to() == Global.zero_address()),

        Return(Int(1))
    ])
