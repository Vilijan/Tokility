from src.models.ticket_models import ConcertTicket
import json
from typing import List
import streamlit as st


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


def load_tickets(file_name) -> List[ConcertTicket]:
    json_data = load_json(file_name)

    tickets = []

    for ticket_data in json_data['concert_tickets']:
        tickets.append(ConcertTicket(**ticket_data))

    return tickets


concert_tickets = load_tickets('ticket_dummy.json')

for i in range(5):
    st.image(concert_tickets[i].ipfs_image, caption=concert_tickets[i].name, width=400)