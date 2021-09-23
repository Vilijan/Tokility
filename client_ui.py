import json
import time
import uuid
from datetime import date
from typing import List
from PIL import Image

import streamlit as st

from src.blockchain_utils.credentials import get_account_with_name
from src.models.asset_configurations import *
from src.models.ticket_models import *


def run_app():
    image = Image.open("tokility-logo-gray.png")
    st.sidebar.image(image, width=300)
    st.sidebar.header("Simulating login of a seller")
    seller_list = ["-"] + list(all_sellers_dict.keys())
    seller_selected = st.sidebar.selectbox("Select a seller", seller_list)

    if seller_selected != "-":
        asa_type = all_sellers_dict[seller_selected]['asa_type']
        show_seller_config(seller_selected, asa_type)
        show_tickets(asa_type)


def show_seller_config(seller_selected: str, asa_type: str) -> None:
    st.header(f"👋Hello {seller_selected}")
    st.header(f"Set the tickets behaviour and track their lifespan.")
    # seller configuration

    with st.form(key='seller_settings_form'):
        if asa_type == 'concert':
            st.session_state['current_address'] = get_account_with_name(account_name='foo_fighters')[1]
            asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
            date_time, name, ticket_type, location = show_concert_input()

        if asa_type == 'cinema':
            st.session_state['current_address'] = get_account_with_name(account_name='pathe_cinema')[1]
            asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
            date_time, name, ticket_type, row, seat = show_cinema_input()

        if asa_type == 'conference':
            st.session_state['current_address'] = get_account_with_name(account_name='pathe_cinema')[1]
            asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
            date_time, name, ticket_type, duration = show_conference_input()

        if asa_type == 'appointment':
            st.session_state['current_address'] = get_account_with_name(account_name='pathe_cinema')[1]
            asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
            date_time, name, duration = show_appointment_input()

        if asa_type == 'restaurant':
            st.session_state['current_address'] = get_account_with_name(account_name='jamie_oliver')[1]
            asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
            date_time, name, ticket_type = show_restaurant_input()

        submit_button = st.form_submit_button(label='Submit')

    # save all settings for a token from the chosen seller after submit button
    if submit_button:
        if validate_input(asa_price, reselling_allowed, max_sell_price, reselling_end_date, name):
            if asa_type == 'concert':
                store_concert_input(asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date,
                                    gifting_allowed, date_time, name, ticket_type, location)
            if asa_type == 'cinema':
                store_cinema_input(asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date,
                                   gifting_allowed, date_time, name, ticket_type, seat, row)

            if asa_type == 'conference':
                store_conference_input(asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date,
                                       gifting_allowed, date_time, name, ticket_type, duration)

            if asa_type == 'appointment':
                store_appointment_input(asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date,
                                        gifting_allowed, date_time, name, duration)

            if asa_type == 'restaurant':
                store_restaurant_input(asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date,
                                       gifting_allowed, date_time, name, ticket_type)

            st.success("Config was saved. New ticket created!🎉")
        else:
            st.warning("Config was not saved. Edit the fields and try again.")


def show_tickets(asa_type: str) -> None:
    # seller tickets
    # all_transactions = read_json("demo_transactions.json")["executed_transactions"]
    if asa_type == 'concert':
        seller_tokens = load_concert_tickets()

    if asa_type == 'cinema':
        seller_tokens = load_cinema_tickets()

    if asa_type == 'conference':
        seller_tokens = load_conference_tickets()

    if asa_type == 'appointment':
        seller_tokens = load_appointment_tickets()

    if asa_type == 'restaurant':
        seller_tokens = load_restaurant_tickets()

    # seller all tickets overview
    with st.expander("Tickets", True):
        for ticket in seller_tokens:
            show_ticket_info(ticket)

    # seller transactions overview
    with st.expander("All transactions", True):
        # seller overview over all transactions
        st.header("🕵️ All transactions overview")
        # TODO: Add dummy data and display it in a nice way


def store_concert_input(asa_price: int,
                        reselling_allowed: bool,
                        max_sell_price: int,
                        creator_fee: int,
                        reselling_end_date: date,
                        gifting_allowed: bool,
                        date_time: date,
                        name: str,
                        ticket_type: str,
                        location: str) -> None:
    try:
        unix_timestamp = int(time.mktime(datetime.strptime(str(reselling_end_date), "%Y-%m-%d").timetuple()))

        initial_offering_config = ASAInitialOfferingConfiguration(asa_price=asa_price,
                                                                  tokiliy_fee="5")

        economy_configuration = ASAEconomyConfiguration(max_sell_price=max_sell_price,
                                                        owner_fee=creator_fee,
                                                        reselling_allowed=1 * reselling_allowed,
                                                        reselling_end_date=unix_timestamp,
                                                        gifting_allowed=1 * gifting_allowed)

        asa_configuration = ASAConfiguration(asa_id=generate_id(),
                                             asa_creator_address=st.session_state['current_address'],
                                             unit_name="TOK",
                                             asset_name=st.session_state['current_address'],
                                             initial_offering_configuration=initial_offering_config,
                                             economy_configuration=economy_configuration)

        concert_ticket = ConcertTicket(asa_configuration=asa_configuration,
                                       business_type=Ticket.BusinessType.concert,
                                       issuer=st.session_state['current_address'],
                                       ipfs_image="https://gateway.pinata.cloud/ipfs/QmY7Ywogdc2q6du8TyFjaCegpTpuZqZSpL9WiBJ5uLgV99",
                                       type=ticket_type,
                                       name=name,
                                       location=location,
                                       datetime=str(date_time))

        concert_tickets.append(concert_ticket)
        json_data = read_json('concert_tickets_dummy.json')
        json_data['concert_tickets'].append(concert_ticket.dict())
        save_json('concert_tickets_dummy.json', json_data)

    except ValueError as error:
        st.error(f"Error! Ticket cannot be stored due to inconsistent formats. {error}")


def store_cinema_input(asa_price: int,
                       reselling_allowed: bool,
                       max_sell_price: int,
                       creator_fee: int,
                       reselling_end_date: date,
                       gifting_allowed: bool,
                       date_time: date,
                       name: str,
                       ticket_type: str,
                       seat: int,
                       row: int) -> None:
    try:
        unix_timestamp = int(time.mktime(datetime.strptime(str(reselling_end_date), "%Y-%m-%d").timetuple()))

        initial_offering_config = ASAInitialOfferingConfiguration(asa_price=asa_price,
                                                                  tokiliy_fee="5")

        economy_configuration = ASAEconomyConfiguration(max_sell_price=max_sell_price,
                                                        owner_fee=creator_fee,
                                                        reselling_allowed=1 * reselling_allowed,
                                                        reselling_end_date=unix_timestamp,
                                                        gifting_allowed=1 * gifting_allowed)

        asa_configuration = ASAConfiguration(asa_id=generate_id(),
                                             asa_creator_address=st.session_state['current_address'],
                                             unit_name="TOK",
                                             asset_name=st.session_state['current_address'],
                                             initial_offering_configuration=initial_offering_config,
                                             economy_configuration=economy_configuration)

        cinema_ticket = CinemaTicket(asa_configuration=asa_configuration,
                                     business_type=Ticket.BusinessType.concert,
                                     issuer=st.session_state['current_address'],
                                     ipfs_image="https://gateway.pinata.cloud/ipfs/QmY7Ywogdc2q6du8TyFjaCegpTpuZqZSpL9WiBJ5uLgV99",
                                     type=ticket_type,
                                     name=name,
                                     seat=seat,
                                     row=row,
                                     datetime=str(date_time))

        cinema_tickets.append(cinema_ticket)
        json_data = read_json('cinema_tickets_dummy.json')
        json_data['cinema_tickets'].append(cinema_ticket.dict())
        save_json('cinema_tickets_dummy.json', json_data)

    except ValueError as error:
        st.error(f"Error! Ticket cannot be stored due to inconsistent formats. {error}")


def store_conference_input(asa_price: int,
                           reselling_allowed: bool,
                           max_sell_price: int,
                           creator_fee: int,
                           reselling_end_date: date,
                           gifting_allowed: bool,
                           date_time: date,
                           name: str,
                           ticket_type: str,
                           duration: int) -> None:
    try:
        unix_timestamp = int(time.mktime(datetime.strptime(str(reselling_end_date), "%Y-%m-%d").timetuple()))

        initial_offering_config = ASAInitialOfferingConfiguration(asa_price=asa_price,
                                                                  tokiliy_fee="5")

        economy_configuration = ASAEconomyConfiguration(max_sell_price=max_sell_price,
                                                        owner_fee=creator_fee,
                                                        reselling_allowed=1 * reselling_allowed,
                                                        reselling_end_date=unix_timestamp,
                                                        gifting_allowed=1 * gifting_allowed)

        asa_configuration = ASAConfiguration(asa_id=generate_id(),
                                             asa_creator_address=st.session_state['current_address'],
                                             unit_name="TOK",
                                             asset_name=st.session_state['current_address'],
                                             initial_offering_configuration=initial_offering_config,
                                             economy_configuration=economy_configuration)

        conference_ticket = ConferenceTicket(asa_configuration=asa_configuration,
                                             business_type=Ticket.BusinessType.conference,
                                             issuer=st.session_state['current_address'],
                                             ipfs_image="https://gateway.pinata.cloud/ipfs/QmY7Ywogdc2q6du8TyFjaCegpTpuZqZSpL9WiBJ5uLgV99",
                                             name=name,
                                             type=ticket_type,
                                             duration=duration,
                                             datetime=str(date_time))

        conference_tickets.append(conference_ticket)
        json_data = read_json('conference_tickets_dummy.json')
        json_data['conference_tickets'].append(conference_ticket.dict())
        save_json('conference_tickets_dummy.json', json_data)

    except ValueError as error:
        st.error(f"Error! Ticket cannot be stored due to inconsistent formats. {error}")


def store_appointment_input(asa_price: int,
                            reselling_allowed: bool,
                            max_sell_price: int,
                            creator_fee: int,
                            reselling_end_date: date,
                            gifting_allowed: bool,
                            date_time: date,
                            name: str,
                            duration: int) -> None:
    try:
        unix_timestamp = int(time.mktime(datetime.strptime(str(reselling_end_date), "%Y-%m-%d").timetuple()))

        initial_offering_config = ASAInitialOfferingConfiguration(asa_price=asa_price,
                                                                  tokiliy_fee="5")

        economy_configuration = ASAEconomyConfiguration(max_sell_price=max_sell_price,
                                                        owner_fee=creator_fee,
                                                        reselling_allowed=1 * reselling_allowed,
                                                        reselling_end_date=unix_timestamp,
                                                        gifting_allowed=1 * gifting_allowed)

        asa_configuration = ASAConfiguration(asa_id=generate_id(),
                                             asa_creator_address=st.session_state['current_address'],
                                             unit_name="TOK",
                                             asset_name=st.session_state['current_address'],
                                             initial_offering_configuration=initial_offering_config,
                                             economy_configuration=economy_configuration)

        appointment_ticket = AppointmentTicket(asa_configuration=asa_configuration,
                                               business_type=Ticket.BusinessType.appointment,
                                               issuer=st.session_state['current_address'],
                                               ipfs_image="https://gateway.pinata.cloud/ipfs/QmY7Ywogdc2q6du8TyFjaCegpTpuZqZSpL9WiBJ5uLgV99",
                                               doctor_name=name,
                                               duration=duration,
                                               datetime=str(date_time))

        appointment_tickets.append(appointment_ticket)
        json_data = read_json('appointment_tickets_dummy.json')
        json_data['appointment_tickets'].append(appointment_ticket.dict())
        save_json('appointment_tickets_dummy.json', json_data)

    except ValueError as error:
        st.error(f"Error! Ticket cannot be stored due to inconsistent formats. {error}")


def store_restaurant_input(asa_price: int,
                           reselling_allowed: bool,
                           max_sell_price: int,
                           creator_fee: int,
                           reselling_end_date: date,
                           gifting_allowed: bool,
                           date_time: date,
                           name: str,
                           ticket_type: str, ) -> None:
    try:
        unix_timestamp = int(time.mktime(datetime.strptime(str(reselling_end_date), "%Y-%m-%d").timetuple()))

        initial_offering_config = ASAInitialOfferingConfiguration(asa_price=asa_price,
                                                                  tokiliy_fee="5")

        economy_configuration = ASAEconomyConfiguration(max_sell_price=max_sell_price,
                                                        owner_fee=creator_fee,
                                                        reselling_allowed=1 * reselling_allowed,
                                                        reselling_end_date=unix_timestamp,
                                                        gifting_allowed=1 * gifting_allowed)

        asa_configuration = ASAConfiguration(asa_id=generate_id(),
                                             asa_creator_address=st.session_state['current_address'],
                                             unit_name="TOK",
                                             asset_name=st.session_state['current_address'],
                                             initial_offering_configuration=initial_offering_config,
                                             economy_configuration=economy_configuration)

        restaurant_ticket = RestaurantTicket(asa_configuration=asa_configuration,
                                             business_type=Ticket.BusinessType.restaurant,
                                             issuer=st.session_state['current_address'],
                                             ipfs_image="https://gateway.pinata.cloud/ipfs/QmY7Ywogdc2q6du8TyFjaCegpTpuZqZSpL9WiBJ5uLgV99",
                                             name=name,
                                             type=ticket_type,
                                             datetime=str(date_time))

        restaurant_tickets.append(restaurant_ticket)
        json_data = read_json('restaurant_tickets_dummy.json')
        json_data['restaurant_tickets'].append(restaurant_ticket.dict())
        save_json('restaurant_tickets_dummy.json', json_data)

    except ValueError as error:
        st.error(f"Error! Ticket cannot be stored due to inconsistent formats. {error}")


def show_concert_input() -> tuple:
    asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
    date_time, name = show_general_input_fields('concert')

    with st.expander("Concert specifics", True):
        ticket_types = ['Seating', 'Standing', 'VIP']
        ticket_type = st.selectbox("Select the ticket type", ticket_types, key=f'concert_ticket_types')
        location = st.text_input("Enter the location of the concert", key=f'concert_location')

        return asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, \
               gifting_allowed, date_time, name, ticket_type, location


def show_cinema_input() -> tuple:
    asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
    date_time, name = show_general_input_fields('cinema')
    with st.expander("Cinema specifics", True):
        ticket_types = ['Regular', 'VIP']
        ticket_type = st.selectbox("Select the ticket type", ticket_types, key=f'cinema_ticket_types')
        seat = st.slider("Select a seat", min_value=1, max_value=100, step=1, key=f'cinema_seat')
        row = st.slider("Select the row", min_value=1, max_value=30, step=1, key=f'cinema_row')

        return asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, \
               gifting_allowed, date_time, name, ticket_type, row, seat


def show_conference_input() -> tuple:
    asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
    date_time, name = show_general_input_fields('conference')
    with st.expander("Conference specifics", True):
        ticket_types = ['Regular', 'VIP']
        ticket_type = st.selectbox("Select the ticket type", ticket_types, key=f'conference_ticket_types')

        duration = st.number_input("Select the duration in days", key=f'conference_duration')

        return asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, \
               gifting_allowed, date_time, name, ticket_type, duration


def show_appointment_input() -> tuple:
    asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
    date_time, name = show_general_input_fields('appointment')
    with st.expander("Appointment specifics", True):
        duration = st.number_input("Select the duration in hours", key=f'appointment_duration')

        return asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, \
               gifting_allowed, date_time, name, duration


def show_restaurant_input() -> tuple:
    asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, gifting_allowed, \
    date_time, name = show_general_input_fields('restaurant')
    with st.expander("Restaurant specifics", True):
        ticket_types = ['Food', 'Drinks only']
        ticket_type = st.selectbox("Select the ticket type", ticket_types, key=f'restaurant_ticket_types')

        return asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, \
               gifting_allowed, date_time, name, ticket_type


def generate_id():
    return uuid.uuid4().int & (1 << 32) - 1


# we need this so that streamlit form refreshes when changing a seller
def show_general_input_fields(key: str) -> tuple:
    with st.expander("Base Configuration", True):
        st.header("🎟 Set the general rules")
        asa_price = st.number_input("Insert price", key=f'{key}_price')
        reselling_allowed = st.checkbox("Tick this box if you allow reselling", key=f'{key}_reselling_allowed')
        max_sell_price = st.number_input("Insert maximum reselling price", key=f'{key}_max_resell_price')
        creator_fee = st.number_input("Insert your fee of the resold ticket", key=f'{key}_creator_fee')
        reselling_end_date = st.date_input('End date', date.today(), key=f'{key}_reselling_end_date')
        gifting_allowed = st.checkbox("Tick this box if you allow gifting", key=f'{key}_allow_gifting')
        datetime = st.date_input("Enter the date of the event", key=f'{key}_datetime')
        name = st.text_input("Enter the event name", key=f'{key}_name')

        return asa_price, reselling_allowed, max_sell_price, creator_fee, reselling_end_date, \
               gifting_allowed, datetime, name


def validate_input(asa_price: int,
                   reselling_allowed: bool,
                   max_sell_price: int,
                   reselling_end_date: date,
                   name: str) -> bool:
    if asa_price == 0:
        st.error("Selling price should not be 0.")
        return False

    if reselling_allowed and max_sell_price == 0:
        st.error("If reselling is allowed, you have to set maximum reselling price.")
        return False

    if reselling_end_date < date.today():
        st.error("If reselling is allowed, the end reselling date cannot be before today.")
        return False

    if name == "":
        st.error("Name cannot be empty.")
        return False

    return True


def show_ticket_info(ticket):
    if ticket.business_type == 'appointment':
        name = ticket.doctor_name
    else:
        name = ticket.name
    html_format = f"""
        <div class="card">
            <header>
                <time datetime="2018-05-15T19:00">{ticket.datetime}</time>
                <div class="id">ID: {ticket.asa_configuration.asa_id}</div>
        <div class="sponsor">{ticket.asa_configuration.initial_offering_configuration.asa_price} algos</div>
            </header>
        <div class="announcement">
            <h1>{name}</h1>
            <h3>{ticket.asa_configuration.economy_configuration.show_info_row1()}</h3>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row2()}</h4>
            <h4>{ticket.asa_configuration.economy_configuration.show_info_row3()}</h4>
            <h4>{ticket.show_info()}</h4>
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


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f)


def read_json(file_name: str) -> dict:
    with open(file_name) as fp:
        data = json.load(fp)

    return data


def load_concert_tickets() -> List[ConcertTicket]:
    json_data = read_json('concert_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['concert_tickets']:
        tickets.append(ConcertTicket(**ticket_data))

    return tickets


def load_cinema_tickets() -> List[CinemaTicket]:
    json_data = read_json('cinema_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['cinema_tickets']:
        tickets.append(CinemaTicket(**ticket_data))

    return tickets


def load_conference_tickets() -> List[ConferenceTicket]:
    json_data = read_json('conference_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['conference_tickets']:
        tickets.append(ConferenceTicket(**ticket_data))

    return tickets


def load_appointment_tickets() -> List[AppointmentTicket]:
    json_data = read_json('appointment_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['appointment_tickets']:
        tickets.append(AppointmentTicket(**ticket_data))

    return tickets


def load_restaurant_tickets() -> List[RestaurantTicket]:
    json_data = read_json('restaurant_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['restaurant_tickets']:
        tickets.append(RestaurantTicket(**ticket_data))

    return tickets


if __name__ == '__main__':
    all_sellers_dict = read_json('sellers_database.json')

    concert_tickets = load_concert_tickets()
    cinema_tickets = load_cinema_tickets()
    conference_tickets = load_conference_tickets()
    appointment_tickets = load_appointment_tickets()
    restaurant_tickets = load_restaurant_tickets()

    run_app()
