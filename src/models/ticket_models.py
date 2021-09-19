from pydantic import BaseModel
from src.models.asset_configurations import ASAConfiguration
from abc import ABC


class Ticket(ABC, BaseModel):
    class BusinessType:
        concert = "concert"
        conference = "conference"
        cinema = "cinema"
        restaurant = "restaurant"
        appointment = "appointment"

    asa_configuration: ASAConfiguration
    business_type: str
    issuer: str


class ConcertTicket(Ticket):
    type: str
    name: str
    location: str
    datetime: str


class CinemaTicket(Ticket):
    type: str
    name: str
    datetime: str
    seat: int
    row: int


class ConferenceTicket(Ticket):
    type: str
    name: str
    duration: str
    datetime: str


class AppointmentTicket(Ticket):
    duration: int
    datetime: str
    doctor_name: str


class RestaurantTicket(Ticket):
    type: str
    datetime: str
    name: str
