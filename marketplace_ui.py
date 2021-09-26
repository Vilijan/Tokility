from src.services.sale_offer_service import InitialBuyOfferingsService, SecondHandOfferingsService
from src.models.asset_sale_offer import SaleOffer
from src.models.ticket_models import Ticket, ConferenceTicket
import time
from typing import List
import streamlit as st
from src.services.asa_service import ASAService
from src.services.tokility_dex_service import TokilityDEXService
from PIL import Image
import json
from src.blockchain_utils.credentials import get_client


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


COLORS = [
    ("#9E392B", "#B98888"),
]


def algos(micro_algos) -> float:
    return float(micro_algos / 1000000)


def show_sale_offer(sale_offer: SaleOffer, color: (str, str)):
    ticket = sale_offer.ticket
    html_format = f"""
        <div class="card">
            <header>
                <time datetime="2018-05-15T19:00">{ticket.datetime}</time>
                <div class="id">{algos(sale_offer.amount)} algos</div>
        <div class="sponsor">ID: {ticket.asa_configuration.asa_id}</div>
            </header>
        <div class="announcement">
            <h1>{ticket.ticket_name}</h1>
            <h3>{ticket.ticket_info}</h3>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row1()}</h4>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row2()}</h4>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row3()}</h4>
        </div>    
        </div>
    """
    st.write(
        html_format
        ,
        unsafe_allow_html=True
    )

    st.write(
        f"""
            <style>
            @import url('https://fonts.googleapis.com/css?family=Asap+Condensed:600i,700');

                h1 {{
                  font-size: 25px;
                  color: #fff;
                  text-transform: uppercase;
                }}
                h3 {{
                  font-size: 20px;
                  color: #fff;
                  text-transform: uppercase;
                }}

                h4 {{
                  font-size: 18px;
                  color: #fff;
                }}

                .card {{
                  display: flex;
                  font-family: 'Asap Condensed', sans-serif;
                  position: relative;
                  margin: auto;
                  height: 350px;
                  width: 600px;
                  text-align: center;
                  background: linear-gradient({color[0]}, {color[1]});
                  border-radius: 2px;
                  box-shadow: 0 6px 12px -3px rgba(0,0,0,.3);
                  color: #fff;
                  padding: 30px;

                }}

                .card header {{
                  position: absolute;
                  top: 31px;
                  left: 0;
                  width: 100%;
                  padding: 0 10%;
                  transform: translateY(-50%);
                  display: grid;
                  grid-template-columns: 1fr 1fr 1fr;
                  align-items: center;
                }}

                .card header > *:first-child {{
                  text-align: left;
                }}
                .card header > *:last-child {{
                  text-align: right;
                }}

                .id {{
                  font-size: 24px;
                  position: relative;
                }}

                .announcement {{
                  position: relative;
                  border: 3px solid currentColor;
                  border-top: 0;
                  width: 100%;
                  height: 100%;
                  display: flex;
                  flex-direction: column;
                  justify-content: center;
                  align-items: center;
                }}

                .announcement:before,
                .announcement:after {{
                  content: '';
                  position: absolute;
                  top: 0px;
                  border-top: 3px solid currentColor;
                  height: 0;
                  width: 15px;
                }}
                .announcement:before {{
                  left: -3px;
                }}
                .announcement:after {{
                  right: -3px;
                }}

                * {{
                  box-sizing: border-box;
                  margin: 0;
                  padding: 0;
                }}

                html, body {{
                  height: 100%;
                }}

                h1, h2, h3, h4 {{
                  margin: .15em 0;
                }}
            """,
        unsafe_allow_html=True,
        key=f"{ticket.asa_configuration.asa_id}"
    )


def buy_ticket_first_sale(buyer_private_key, buyer_address, asa_configuration):
    concert_company_asa_service.asa_opt_in(asa_id=asa_configuration.asa_id,
                                           user_pk=buyer_private_key)

    tx_id = tokility_dex_service.initial_buy(buyer_addr=buyer_address,
                                             buyer_pk=buyer_private_key,
                                             asa_configuration=asa_configuration,
                                             asa_clawback_addr=CLAWBACK_ADDRESS,
                                             asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)
    print(f'initial buy completed in: {tx_id}')


def buy_ticket_second_hand(buyer_private_key: str,
                           buyer_address: str,
                           sale_offer: SaleOffer):
    concert_company_asa_service.asa_opt_in(asa_id=sale_offer.ticket.asa_configuration.asa_id,
                                           user_pk=buyer_private_key)

    tx_id = tokility_dex_service.buy_from_seller(buyer_addr=buyer_address,
                                                 buyer_pk=buyer_private_key,
                                                 seller_addr=sale_offer.seller_address,
                                                 price=sale_offer.second_hand_amount,
                                                 asa_configuration=sale_offer.ticket.asa_configuration,
                                                 asa_clawback_addr=CLAWBACK_ADDRESS,
                                                 asa_clawback_bytes=CLAWBACK_ADDRESS_BYTES)

    print(f'Second hand buy completed in: {tx_id}')


def load_offers():
    time.sleep(2)
    initial_offers = InitialBuyOfferingsService.available_sell_offers(creator_address=CONFERENCE_COMPANY_ADDR)
    time.sleep(3)
    second_hand_offers = SecondHandOfferingsService.available_offers(app_id=APP_ID)

    curr_offers: List[SaleOffer] = []
    curr_offers.extend(initial_offers)
    curr_offers.extend(second_hand_offers)

    st.session_state.sale_offers = curr_offers


def buy_sell_offer(sale_offer: SaleOffer):
    if sale_offer.sale_type == "initial_buy":
        buy_ticket_first_sale(buyer_private_key=CREDENTIALS[0],
                              buyer_address=CREDENTIALS[1],
                              asa_configuration=sale_offer.ticket.asa_configuration)
    else:
        buy_ticket_second_hand(buyer_private_key=CREDENTIALS[0],
                               buyer_address=CREDENTIALS[1],
                               sale_offer=sale_offer)

    load_offers()


def list_sale_offers(available_sale_offers: List[SaleOffer]):
    for sale_offer in available_sale_offers:
        ID = sale_offer.ticket.asa_configuration.asa_id
        # TODO: This should be improved, currently is hard cast
        sale_offer.ticket = ConferenceTicket(**sale_offer.ticket.dict())

        show_sale_offer(sale_offer=sale_offer, color=COLORS[0])

        # Buy token.
        col1, col2, col3, col4, col5 = st.columns(5)
        st.write("_______")
        st.write("")
        _ = col3.button("⬆ ️Buy token",
                        key=f"buy_button_{ID}",
                        on_click=buy_sell_offer,
                        args=(sale_offer,))


config = load_json('config.json')
APP_ID = config['app_id']

PLATFORM_PK = config['app_creator_pk']
PLATFORM_ADDRESS = config['app_creator_address']

BUYER_1_PK = config['buyer_1_pk']
BUYER_1_ADDRESS = config['buyer_1_address']

BUYER_2_PK = config['buyer_2_pk']
BUYER_2_ADDRESS = config['buyer_2_address']

BUYERS = [(BUYER_1_PK, BUYER_1_ADDRESS), (BUYER_2_PK, BUYER_2_ADDRESS)]

CONFERENCE_COMPANY_PK = config['conference_company_pk']
CONFERENCE_COMPANY_ADDR = config['conference_company_address']

client = get_client()

tokility_dex_service = TokilityDEXService(app_creator_addr=PLATFORM_ADDRESS,
                                          app_creator_pk=PLATFORM_PK,
                                          client=client,
                                          app_id=APP_ID)

concert_company_asa_service = ASAService(creator_addr=CONFERENCE_COMPANY_ADDR,
                                         creator_pk=CONFERENCE_COMPANY_PK,
                                         tokility_dex_app_id=tokility_dex_service.app_id,
                                         client=client)

CLAWBACK_ADDRESS = concert_company_asa_service.clawback_address
CLAWBACK_ADDRESS_BYTES = concert_company_asa_service.clawback_address_bytes

image = Image.open("data/ui/tokility-logo.png")
st.sidebar.header(f"Marketplace UI")
st.sidebar.image(image, width=300)
st.sidebar.header(f"ASC1: {APP_ID}")

BUYER_ADDRESS = st.sidebar.selectbox(
    "Buyer address",
    tuple([credentials[1] for credentials in BUYERS])
)

if 'sale_offers' not in st.session_state:
    load_offers()

sale_offers = st.session_state.sale_offers

CREDENTIALS = [cred for cred in BUYERS if cred[1] == BUYER_ADDRESS][0]

sale_offers = [offer for offer in sale_offers if offer.seller_address != BUYER_ADDRESS]

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
reselling_allowed_checkbox = st.sidebar.checkbox('Reselling allowed', value=False)

if reselling_allowed_checkbox:
    sale_offers = [offer for offer in sale_offers
                   if offer.ticket.asa_configuration.economy_configuration.reselling_allowed == 1]

list_sale_offers(available_sale_offers=sale_offers)
