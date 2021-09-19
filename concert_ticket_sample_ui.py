from src.models.ticket_models import *
import json
from typing import List
import streamlit as st


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


def load_cinema_tickets() -> List[CinemaTicket]:
    json_data = load_json('movie_tickets_dummy.json')

    tickets = []

    for ticket_data in json_data['concert_tickets']:
        tickets.append(CinemaTicket(**ticket_data))

    return tickets


concert_tickets = load_concert_tickets()
cinema_tickets = load_cinema_tickets()

concert_tickets[0].json()

for i in range(5):
    st.image(concert_tickets[i].ipfs_image, caption=concert_tickets[i].name, width=400)

for i in range(5):
    st.image(cinema_tickets[i].ipfs_image, caption=cinema_tickets[i].name, width=400)

concert_tickets[
