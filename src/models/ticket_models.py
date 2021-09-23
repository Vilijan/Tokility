from pydantic import BaseModel
from src.models.asset_configurations import ASAConfiguration
from abc import ABC
from typing import Optional


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
    ipfs_image: Optional[str]


class ConcertTicket(Ticket):
    type: str
    name: str
    location: str
    datetime: str

    def show_info(self):
        return f"{self.location}, {self.type}"

class CinemaTicket(Ticket):
    type: str
    name: str
    datetime: str
    seat: int
    row: int

    def show_info(self):
        return f"{self.type}, row: {self.row}, seat: {self.seat}"


class ConferenceTicket(Ticket):
    type: str
    name: str
    duration: str
    datetime: str

    def show_info(self):
        if self.duration == "1":
            unit = "day"
        else:
            unit = 'days'
        return f"{self.type}, {self.duration} {unit}"


class AppointmentTicket(Ticket):
    duration: int
    datetime: str
    doctor_name: str

    def show_info(self):
        return f"{self.duration}h"


class RestaurantTicket(Ticket):
    type: str
    datetime: str
    name: str

    def show_info(self):
        return f"{self.type}"