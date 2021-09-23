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

COLORS = [
    ("#6d9b47", "#3cffc2"),
    ("#80becb", "#02e9c8"),
    ("#fdae74", "#bb2d37"),
    ("#87279e", "#12688e"),
    ("#6f69d2", "#b9ebf9"),
    ("#55b6e1", "#707208"),
    ("#ae8f2d", "#729945"),
    ("#317ab8", "#4e3b61"),
    ("#c49610", "#6692b0"),
    ("#c6bc1a", "#75b131"),
    ("#ad4b00", "#612cc3"),
    ("#9f7cc6", "#806029"),
    ("#8f0c20", "#23b34f"),
    ("#611030", "#349a4a"),
]

APP_ID = 27661966


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


def ticket_holdings(account_address: str, creator_address: str) -> List[Ticket]:
    indexer = get_indexer()

    account_info = indexer.account_info(address=account_address)
    time.sleep(2)
    concert_assets_response = indexer.account_info(address=creator_address)
    concert_assets = set([asset['index'] for asset in concert_assets_response['account']['created-assets']])

    owning_concert_assets = set([asset['asset-id'] for asset in account_info['account']['assets']
                                 if asset['amount'] == 1 and asset['asset-id'] in concert_assets])

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
    global seller_address

    st.session_state[f"ticket_holdings_{seller_address}"] = ticket_holdings(account_address=seller_address,
                                                                            creator_address=CONCERT_COMPANY_ADDRESS)
    print(len(st.session_state[f"ticket_holdings_{seller_address}"]))
    time.sleep(2)
    st.session_state[f"sell_offers_{seller_address}"] = \
        SecondHandOfferingsService.available_offers(app_id=APP_ID,
                                                    sellers_of_interest={seller_address})
    print(len(st.session_state[f"sell_offers_{seller_address}"]))

    list_tickets()


def list_tickets():
    tickets: List[Ticket] = st.session_state[f"ticket_holdings_{seller_address}"]
    sale_offers: List[SaleOffer] = st.session_state[f"sell_offers_{seller_address}"]

    for idx, curr_ticket in enumerate(tickets):
        concert_ticket = ConcertTicket(**curr_ticket.dict())
        show_ticket_info(ticket=concert_ticket, color=COLORS[random.randint(0, len(COLORS) - 1)])
        credentials = [cred for cred in BUYERS if cred[1] == seller_address][0]

        # Show the current selling offer.
        curr_sell_offer = None
        for offer in sale_offers:
            if offer.asa_id == curr_ticket.asa_configuration.asa_id:
                curr_sell_offer = offer

        if curr_sell_offer is not None:
            cols = st.columns(2)
            cols[0].write(f'Ticket already on sale for {algos(curr_sell_offer.second_hand_amount)} algos')

            if cols[1].button("Stop selling", key=f"{seller_address}_stop_sell_button_{idx}"):
                tokility_dex_service.stop_selling(seller_pk=credentials[0],
                                                  asa_configuration=curr_ticket.asa_configuration)

                update_state()

        number = st.number_input('Insert sell price in Algos', key=f"{seller_address}_number_input_{idx}")

        if st.button("Sell token", key=f"{seller_address}_sell_button_{idx}"):
            tokility_dex_service.make_sell_offer(seller_pk=credentials[0],
                                                 sell_price=int(number * 1000000),
                                                 asa_configuration=curr_ticket.asa_configuration)

            update_state()


if __name__ == '__main__':
    PLATFORM_PK, PLATFORM_ADDRESS, _ = get_account_credentials(1)
    BUYERS = [get_account_credentials(2), get_account_credentials(3)]
    CONCERT_COMPANY_PK, CONCERT_COMPANY_ADDRESS, _ = get_account_with_name("concert_company")
    client = get_client()

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

    seller_address = st.sidebar.selectbox(
        "Seller address",
        tuple([credentials[1] for credentials in BUYERS])
    )

    st.title(f"Tokility marketplace")
    st.text(f"Smart contract id: {APP_ID}")

    if f'ticket_holdings_{seller_address}' not in st.session_state:
        update_state()
    else:
        list_tickets()
