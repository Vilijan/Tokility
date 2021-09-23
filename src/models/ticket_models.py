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

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

    asa_configuration: ASAConfiguration
    business_type: str
    issuer: str
    ipfs_image: Optional[str]
    datetime: Optional[str]

    @property
    def ticket_info(self):
        return NotImplemented

    @property
    def ticket_name(self):
        return NotImplemented


class ConcertTicket(Ticket):
    type: str
    name: str
    location: str

    @property
    def ticket_info(self):
        return f"{self.location}, {self.type}"

    @property
    def ticket_name(self):
        return self.name


class CinemaTicket(Ticket):
    type: str
    name: str
    seat: int
    row: int

    @property
    def ticket_info(self):
        return f"{self.type}, row: {self.row}, seat: {self.seat}"

    @property
    def ticket_name(self):
        return self.name


class ConferenceTicket(Ticket):
    type: str
    name: str
    duration: str

    @property
    def ticket_info(self):
        if self.duration == "1":
            unit = "day"
        else:
            unit = 'days'
        return f"{self.type}, {self.duration} {unit}"

    @property
    def ticket_name(self):
        return self.name


class AppointmentTicket(Ticket):
    duration: int
    doctor_name: str

    @property
    def ticket_info(self):
        return f"{self.duration}h"

    @property
    def ticket_name(self):
        return self.doctor_name


class RestaurantTicket(Ticket):
    type: str
    name: str

    @property
    def ticket_info(self):
        return f"{self.type}"

    @property
    def ticket_name(self):
        return self.name
