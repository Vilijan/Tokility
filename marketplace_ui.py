from src.services.sale_offer_service import InitialBuyOfferingsService, SecondHandOfferingsService
from src.models.asset_sale_offer import SaleOffer
from src.models.ticket_models import Ticket, ConcertTicket
import time
from typing import List
import streamlit as st
from src.services.asa_service import ASAService
from src.services.tokility_dex_service import TokilityDEXService
from src.blockchain_utils.credentials import get_account_credentials, get_account_with_name, get_client
from PIL import Image

PLATFORM_PK, PLATFORM_ADDRESS, _ = get_account_credentials(1)
BUYERS = [get_account_credentials(2), get_account_credentials(3)]
CONCERT_COMPANY_PK, CONCERT_COMPANY_ADDRESS, _ = get_account_with_name("concert_company")
client = get_client()


def algos(micro_algos) -> float:
    return float(micro_algos / 1000000)


def show_sale_offer(sale_offer: SaleOffer):
    ticket = sale_offer.ticket
    offer_type = "Buying from the creator" if sale_offer.sale_type == "initial_buy" else "Buying from reseller"
    html_format = f"""
        <div class="card">
            <header>
                <time datetime="2018-05-15T19:00">{ticket.datetime}</time>
                <div class="id">{algos(sale_offer.amount)} algos</div>
        <div class="sponsor">ID: {ticket.asa_configuration.asa_id}</div>
            </header>
        <div class="announcement">
            <h1>{ticket.ticket_name}</h1>
            <h3>{ticket.asa_configuration.economy_configuration.show_info_row1()}</h3>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row2()}</h4>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row3()}</h4>
            <h4>{ticket.ticket_info}</h4>
            <h4>{offer_type}</h4>
        </div>    
        </div>
    """
    st.write(
        html_format
        ,
        unsafe_allow_html=True
    )

    st.write(
        """
        <style>
        @import url('https://fonts.googleapis.com/css?family=Asap+Condensed:600i,700');

            h1 {
              font-size: 25px;
              color: #fff;
              text-transform: uppercase;
            }
            h3 {
              font-size: 20px;
              color: #fff;
              text-transform: uppercase;
            }

            h4 {
              font-size: 18px;
              color: #ccc;
            }

            .card {
              display: flex;
              font-family: 'Asap Condensed', sans-serif;
              position: relative;
              margin: auto;
              height: 350px;
              width: 600px;
              text-align: center;
              background: linear-gradient(#E96874, #6E3663, #2B0830);
              border-radius: 2px;
              box-shadow: 0 6px 12px -3px rgba(0,0,0,.3);
              color: #fff;
              padding: 30px;

            }

            .card header {
              position: absolute;
              top: 31px;
              left: 0;
              width: 100%;
              padding: 0 10%;
              transform: translateY(-50%);
              display: grid;
              grid-template-columns: 1fr 1fr 1fr;
              align-items: center;
            }

            .card header > *:first-child {
              text-align: left;
            }
            .card header > *:last-child {
              text-align: right;
            }

            .id {
              font-size: 24px;
              position: relative;
            }

            .announcement {
              position: relative;
              border: 3px solid currentColor;
              border-top: 0;
              width: 100%;
              height: 100%;
              display: flex;
              flex-direction: column;
              justify-content: center;
              align-items: center;
            }

            .announcement:before,
            .announcement:after {
              content: '';
              position: absolute;
              top: 0px;
              border-top: 3px solid currentColor;
              height: 0;
              width: 15px;
            }
            .announcement:before {
              left: -3px;
            }
            .announcement:after {
              right: -3px;
            }

            * {
              box-sizing: border-box;
              margin: 0;
              padding: 0;
            }

            html, body {
              height: 100%;
            }

            h1, h2, h3, h4 {
              margin: .15em 0;
            }
        """,
        unsafe_allow_html=True
    )


APP_ID = 27661966

tokility_dex_service = TokilityDEXService(app_creator_addr=PLATFORM_ADDRESS,
                                          app_creator_pk=PLATFORM_PK,
                                          client=client,
                                          app_id=APP_ID)

concert_company_asa_service = ASAService(creator_addr=CONCERT_COMPANY_ADDRESS,
                                         creator_pk=CONCERT_COMPANY_PK,
                                         tokility_dex_app_id=tokility_dex_service.app_id,
                                         client=client)

CLAWBACK_ADDRESS = concert_company_asa_service.clawback_address
CLAWBACK_ADDRESS_BYTES = concert_company_asa_service.clawback_address_bytes


def buy_ticket(buyer_private_key, buyer_address, asa_configuration):
    concert_company_asa_service.asa_opt_in(asa_id=asa_configuration.asa_id,
                                           user_pk=buyer_private_key)

    tx_id = tokility_dex_service.initial_buy(buyer_addr=buyer_address,
                                             buyer_pk=buyer_private_key,
                                             asa_configuration=asa_configuration,
                                             asa_clawback_addr=CLAWBACK_ADDRESS,
                                             asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)
    print(f'ticket bought in: {tx_id}')


def load_offers() -> List[SaleOffer]:
    initial_offers = InitialBuyOfferingsService.available_sell_offers(creator_address=CONCERT_COMPANY_ADDRESS)
    time.sleep(3)
    second_hand_offers = SecondHandOfferingsService.available_offers(app_id=APP_ID)

    sale_offers: List[SaleOffer] = []
    sale_offers.extend(initial_offers)
    sale_offers.extend(second_hand_offers)

    return sale_offers


if 'sale_offers' not in st.session_state:
    st.session_state.sale_offers = load_offers()

image = Image.open("tokility-logo-gray.png")
st.sidebar.image(image, width=300)
st.sidebar.subheader(f"ASC1: {APP_ID}")

ui_type = st.sidebar.selectbox("Market type", ("Buy Tokility tokens", "Sell Tokility tokens"))


def buy_ui():
    sale_offers = st.session_state.sale_offers

    buyer_address = st.sidebar.selectbox(
        "Buyer address",
        tuple([credentials[1] for credentials in BUYERS])
    )

    sale_offers = [offer for offer in sale_offers if offer.seller_address != buyer_address]

    # Ticket type
    ticket_type = st.sidebar.selectbox(
        "Ticket type",
        ('all', Ticket.BusinessType.concert, Ticket.BusinessType.cinema, Ticket.BusinessType.conference,
         Ticket.BusinessType.restaurant, Ticket.BusinessType.appointment)
    )

    if ticket_type != 'all':
        sale_offers = [offer for offer in sale_offers if offer.ticket.business_type == ticket_type]

    # Price range.
    # TODO: Implement proper max price. Take the max
    price_slider = st.sidebar.slider('Select price range', 0.0, 30.0, (0.0, 15.0))

    sale_offers = [offer for offer in sale_offers if algos(offer.amount) >= price_slider[0]]
    sale_offers = [offer for offer in sale_offers if algos(offer.amount) <= price_slider[1]]

    # Re-selling allowed
    reselling_allowed_checkbox = st.sidebar.checkbox('Reselling allowed', value=True)

    if reselling_allowed_checkbox:
        sale_offers = [offer for offer in sale_offers
                       if offer.ticket.asa_configuration.economy_configuration.reselling_allowed == 1]

    def asa_config_ui(ticket: Ticket, asa_id: int):
        my_expander = st.expander(label=f'Ticket configuration for {asa_id}', expanded=False)
        with my_expander:
            st.image(ticket.ipfs_image, width=400)
            st.text(f"Issued by: {ticket.issuer}")
            st.text(f"owner_fee: {algos(ticket.asa_configuration.economy_configuration.owner_fee)} "
                    f"platform_fee: {algos(ticket.asa_configuration.initial_offering_configuration.tokiliy_fee)}")
            if ticket.asa_configuration.economy_configuration.reselling_allowed == 1:
                st.success("Reselling is allowed")
                st.text(f"maximum sell price: {algos(ticket.asa_configuration.economy_configuration.max_sell_price)}")
            else:
                st.error("Reselling is not allowed")

            if ticket.asa_configuration.economy_configuration.gifting_allowed == 1:
                st.success("Gifting of the ticket is allowed")
            else:
                st.error("Gifting of the ticket is not allowed")

    st.title(f"Marketplace")

    for idx, sale_offer in enumerate(sale_offers):
        # TODO: This should be improved, currently is hard cast
        sale_offer.ticket = ConcertTicket(**sale_offer.ticket.dict())

        # show_ticket_info(ticket=concert_ticket)
        show_sale_offer(sale_offer=sale_offer)

        if st.button("Buy token", key=str(idx)):
            credentials = [cred for cred in BUYERS if cred[1] == buyer_address][0]
            buy_ticket(buyer_private_key=credentials[0],
                       buyer_address=credentials[1],
                       asa_configuration=sale_offer.ticket.asa_configuration)
            st.session_state.sale_offers = load_offers()


def sell_ui():
    st.title("Sell tokens")


if ui_type == "Buy Tokility tokens":
    buy_ui()
else:
    sell_ui()
