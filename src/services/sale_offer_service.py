from typing import List
from src.blockchain_utils.credentials import get_indexer
from src.models.ticket_models import Ticket
from src.models.asset_sale_offer import SaleOffer
import base64
import time
import requests


class SecondHandOfferingsService:

    @staticmethod
    def available_offers(app_id: int) -> List[SaleOffer]:
        indexer = get_indexer()
        acc_app_info = indexer.accounts(application_id=app_id)
        sale_offers: List[SaleOffer] = []
        for account in acc_app_info['accounts']:
            for local_state in account['apps-local-state']:
                if local_state['id'] == app_id:
                    if 'key-value' in local_state:
                        for local_state_stored in local_state['key-value']:
                            seller_address = account['address']
                            asa_id = int.from_bytes(base64.b64decode(local_state_stored['key']), "big")
                            asa_price = local_state_stored['value']['uint']
                            # TODO: We can remove this once we have fast node or pay.
                            time.sleep(1.5)
                            asset_info = indexer.asset_info(asset_id=asa_id)
                            r = requests.get(asset_info['asset']['params']['url'])

                            sale_offers.append(SaleOffer(sale_type="second_hand",
                                                         ticket=Ticket(**r.json()),
                                                         second_hand_seller_address=seller_address,
                                                         second_hand_amount=asa_price))

        return sale_offers


class InitialBuyOfferingsService:

    @staticmethod
    def available_sell_offers(creator_address) -> List[SaleOffer]:
        indexer = get_indexer()
        assets = indexer.account_info(address=creator_address)
        available_for_sell_assets = set()

        for asset in assets['account']['assets']:
            if asset['amount'] == 1:
                available_for_sell_assets.add(asset['asset-id'])

        sale_offers: List[SaleOffer] = []
        for created_asset in assets['account']['created-assets']:
            if created_asset['index'] in available_for_sell_assets:
                r = requests.get(created_asset['params']['url'])
                sale_offers.append(SaleOffer(sale_type="initial_buy",
                                             ticket=Ticket(**r.json())))

        return sale_offers
