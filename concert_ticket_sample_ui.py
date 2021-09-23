from src.models.ticket_models import *
import json
from typing import List
import streamlit as st
import requests
from src.blockchain_utils.credentials import get_indexer


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


def load_concert_tickets() -> List[ConcertTicket]:
    json_data = load_json('concert_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['concert_tickets']:
        tickets.append(ConcertTicket(**ticket_data))

    return tickets


def load_concert_tickets_blockchain() -> List[ConcertTicket]:
    indexer = get_indexer()

    response = indexer.search_assets(creator="626IV5OUMGBBY3NHAZVSEVWYVJSR4E2RQZXNEYSTOXEG7CH45SUBEYOO5M")
    blockchain_tickets: List[ConcertTicket] = []

    for asset in response["assets"]:
        r = requests.get(asset["params"]["url"])
        concert_ticket = ConcertTicket(**r.json())
        concert_ticket.asa_configuration.asa_id = asset["index"]
        blockchain_tickets.append(concert_ticket)

    return blockchain_tickets


def load_cinema_tickets() -> List[CinemaTicket]:
    json_data = load_json('movie_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['concert_tickets']:
        tickets.append(CinemaTicket(**ticket_data))

    return tickets


# concert_tickets = load_concert_tickets()
concert_tickets = load_concert_tickets_blockchain()

for i in range(5):
    st.image(concert_tickets[i].ipfs_image, caption=concert_tickets[i].name, width=400)
#
# cinema_tickets = load_cinema_tickets()
# for i in range(5):
#     st.image(cinema_tickets[i].ipfs_image, caption=cinema_tickets[i].name, width=400)
