from src.services.sale_offer_service import InitialBuyOfferingsService, SecondHandOfferingsService
from src.models.asset_sale_offer import SaleOffer
from src.models.ticket_models import Ticket, ConcertTicket
import time
from typing import List
import streamlit as st
from src.services.asa_service import ASAService
from src.services.tokility_dex_service import TokilityDEXService
from src.blockchain_utils.credentials import get_account_credentials, get_account_with_name, get_client, get_indexer
import requests
import random
from PIL import Image

COLORS = [
    ("#EC6F66", "#F3A183"),
]

APP_ID = 28715729


def algos(micro_algos) -> float:
    return float(micro_algos / 1000000)


def show_ticket_info(ticket: Ticket, color: (str, str)):
    html_format = f"""
        <div class="card">
            <header>
                <time datetime="2018-05-15T19:00">{ticket.datetime}</time>
                <div class="id"></div>
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
        html_format,
        unsafe_allow_html=True,
        key=ticket.asa_configuration.asa_id
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


# TODO: This needs to be extracted in the service.
def ticket_holdings(account_address: str, creator_address: str) -> List[Ticket]:
    indexer = get_indexer()

    account_info = indexer.account_info(address=account_address)
    time.sleep(2)
    concert_assets_response = indexer.account_info(address=creator_address)
    concert_assets = set([asset['index'] for asset in concert_assets_response['account']['created-assets']])

    if 'assets' in account_info['account']:
        owning_concert_assets = set([asset['asset-id'] for asset in account_info['account']['assets']
                                     if asset['amount'] == 1 and asset['asset-id'] in concert_assets])
    else:
        owning_concert_assets = set()

    tickets: List[Ticket] = []
    for asset in concert_assets_response['account']['created-assets']:
        if asset['index'] not in owning_concert_assets:
            continue

        r = requests.get(asset['params']['url'])
        ticket = Ticket(**r.json())
        ticket.asa_configuration.asa_id = asset['index']
        tickets.append(ticket)

    return tickets


def update_state():
    st.session_state[f"ticket_holdings_{SELLER_ADDRESS}"] = ticket_holdings(account_address=SELLER_ADDRESS,
                                                                            creator_address=CONFERENCE_COMPANY_ADDR)
    time.sleep(2)
    st.session_state[f"sell_offers_{SELLER_ADDRESS}"] = \
        SecondHandOfferingsService.available_offers(app_id=APP_ID,
                                                    sellers_of_interest={SELLER_ADDRESS})


def stop_selling(asa_configuration):
    tokility_dex_service.stop_selling(seller_pk=CURR_CREDENTIALS[0],
                                      asa_configuration=asa_configuration)
    time.sleep(1)
    update_state()


def sell_token(asa_configuration, price):
    tokility_dex_service.make_sell_offer(seller_pk=CURR_CREDENTIALS[0],
                                         sell_price=int(price * 1000000),
                                         asa_configuration=asa_configuration)
    time.sleep(1)
    update_state()


def list_tickets():
    tickets: List[Ticket] = st.session_state[f"ticket_holdings_{SELLER_ADDRESS}"]
    sale_offers: List[SaleOffer] = st.session_state[f"sell_offers_{SELLER_ADDRESS}"]

    for curr_ticket in tickets:
        ID = curr_ticket.asa_configuration.asa_id
        concert_ticket = ConcertTicket(**curr_ticket.dict())
        show_ticket_info(ticket=concert_ticket, color=COLORS[random.randint(0, len(COLORS) - 1)])

        # Show the current selling offer.
        curr_sell_offer = None
        for offer in sale_offers:
            if offer.asa_id == curr_ticket.asa_configuration.asa_id:
                curr_sell_offer = offer

        cols = st.columns(2)
        if curr_sell_offer is not None:
            cols[0].write(f'Ticket already on sale for {algos(curr_sell_offer.second_hand_amount)} algos')
            _ = cols[1].button("Stop selling",
                               key=f"{SELLER_ADDRESS}_stop_sell_button_{ID}",
                               on_click=stop_selling,
                               args=(concert_ticket.asa_configuration,))
        else:
            cols[0].write("")
            cols[1].write("")

        sell_price = st.number_input('Insert sell price in Algos', key=f"{SELLER_ADDRESS}_number_input_{ID}")

        sell_cols = st.columns(5)
        st.write("")

        _ = sell_cols[2].button("Sell token",
                                key=f"{SELLER_ADDRESS}_sell_button_{ID}",
                                on_click=sell_token,
                                args=(concert_ticket.asa_configuration, sell_price))

        st.write("_______")


client = get_client()

PLATFORM_PK, PLATFORM_ADDRESS, _ = get_account_credentials(1)
BUYERS = [get_account_credentials(2), get_account_credentials(3)]
CONFERENCE_COMPANY_PK, CONFERENCE_COMPANY_ADDR, _ = get_account_with_name("conference_company")

tokility_dex_service = TokilityDEXService(app_creator_addr=PLATFORM_ADDRESS,
                                          app_creator_pk=PLATFORM_PK,
                                          client=client,
                                          app_id=APP_ID)

concert_company_asa_service = ASAService(creator_addr=CONFERENCE_COMPANY_ADDR,
                                         creator_pk=CONFERENCE_COMPANY_PK,
                                         tokility_dex_app_id=tokility_dex_service.app_id,
                                         client=client)

image = Image.open("data/ui/tokility-logo-gray.png")
st.sidebar.header(f"Sell UI")
st.sidebar.image(image, width=300)
st.sidebar.header(f"ASC1: {APP_ID}")

SELLER_ADDRESS = st.sidebar.selectbox(
    "Seller address",
    tuple([c[1] for c in BUYERS])
)

CURR_CREDENTIALS = [cred for cred in BUYERS if cred[1] == SELLER_ADDRESS][0]

if f'ticket_holdings_{SELLER_ADDRESS}' not in st.session_state:
    update_state()

list_tickets()
