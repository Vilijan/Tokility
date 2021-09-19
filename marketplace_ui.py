from src.services.sale_offer_service import InitialBuyOfferingsService, SecondHandOfferingsService
from src.models.asset_sale_offer import SaleOffer
import time
from typing import List
import streamlit as st


def algos(micro_algos) -> float:
    return float(micro_algos / 1000000)


APP_ID = 27629360
CONCERT_COMPANY_ADDRESS = "BE6CYBSQA6XWJRC7NKEJRDWWVP3DI4N6FG5LGL6TQWRCGFHQ5XFZV7CFTA"

initial_offers = InitialBuyOfferingsService.available_sell_offers(creator_address=CONCERT_COMPANY_ADDRESS)
time.sleep(2)
second_hand_offers = SecondHandOfferingsService.available_offers(app_id=APP_ID)

sale_offers: List[SaleOffer] = []
sale_offers.extend(initial_offers)
sale_offers.extend(second_hand_offers)

for sale_offer in sale_offers:
    st.image(sale_offer.ticket.ipfs_image, width=400)

    if sale_offer.sale_type == "initial_buy":
        st.success("Initial buy")
    else:
        st.warning("Second hand buy")

    st.text(f"seller: {sale_offer.seller_address}")
    st.text(f"sale_price: {algos(sale_offer.amount)} algos")
