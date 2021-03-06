from src.models.asset_configurations import *
from src.models.ticket_models import *
from src.blockchain_utils.credentials import get_account_with_name
import random
import json
import uuid

FOO_FIGHTERS_ADDRESS = get_account_with_name(account_name="foo_fighters")[1]
U2_ADDRESS = get_account_with_name(account_name="U2")[1]


def save_json(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f)


def load_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
        return data


def micro_algo(algo):
    return int(algo * 1000000)


def generate_id():
    return uuid.uuid4().int & (1 << 32) - 1


def create_random_asa_configuration(creator_address: str,
                                    asset_name: str,
                                    price_range: (float, float) = (30.0, 200.0),
                                    tokility_fee_range: (float, float) = (1.0, 5.0),
                                    max_sell_price_range: (float, float) = (35.0, 300.0),
                                    owner_fee_range: (float, float) = (5.0, 40.0),
                                    reselling_end_date: int = 1668143794):
    reselling_allowed = 1 if random.randint(0, 10) > 3 else 0
    gifting_allowed = 1 if random.randint(0, 10) > 2 else 0

    def price(algo_range: (float, float)):
        return random.randint(micro_algo(algo_range[0]), micro_algo(algo_range[1]))

    initial_offering_config = ASAInitialOfferingConfiguration(asa_price=price(price_range),
                                                              tokiliy_fee=price(tokility_fee_range))
    economy_configuration = ASAEconomyConfiguration(max_sell_price=price(max_sell_price_range),
                                                    owner_fee=price(owner_fee_range),
                                                    reselling_allowed=reselling_allowed,
                                                    reselling_end_date=reselling_end_date,
                                                    gifting_allowed=gifting_allowed)

    return ASAConfiguration(asa_creator_address=creator_address,
                            unit_name="TOK",
                            asset_name=asset_name,
                            initial_offering_configuration=initial_offering_config,
                            economy_configuration=economy_configuration)


def create_random_concert_ticket(asa_configuration: ASAConfiguration,
                                 issuer: str,
                                 name: str,
                                 ipfs_image: str):
    return ConcertTicket(asa_configuration=asa_configuration,
                         business_type=Ticket.BusinessType.concert,
                         issuer=issuer,
                         ipfs_image=ipfs_image,
                         name=name,
                         type=random.choice(["VIP", "Standing", "Seating"]),
                         location=random.choice(["Amsterdam", "Skopje", "New York"]),
                         datetime=random.choice(["11.12.2021", "25.11.2022", "30.06.2022"]))


def create_random_cinema_ticket(asa_configuration: ASAConfiguration,
                                issuer: str,
                                ipfs_image: str,
                                movie_name: str):
    return CinemaTicket(asa_configuration=asa_configuration,
                        business_type=Ticket.BusinessType.cinema,
                        issuer=issuer,
                        ipfs_image=ipfs_image,
                        name=movie_name,
                        type=random.choice(["VIP", "Regular"]),
                        datetime=random.choice(["02.10.2021", "03.10.2021", "04.10.2021"]),
                        seat=random.randint(1, 100),
                        row=random.randint(1, 30))


def create_random_conference_ticket(asa_configuration: ASAConfiguration,
                                    issuer: str,
                                    name: str,
                                    ipfs_image: str):
    return ConferenceTicket(asa_configuration=asa_configuration,
                            business_type=Ticket.BusinessType.conference,
                            issuer=issuer,
                            ipfs_image=ipfs_image,
                            name=name,
                            type=random.choice(["VIP", "Regular"]),
                            duration=random.choice([1, 2, 3]),
                            datetime=random.choice(["11.12.2021", "25.11.2022", "30.06.2022"]))


def create_random_appointment_ticket(asa_configuration: ASAConfiguration,
                                     issuer: str,
                                     name: str,
                                     ipfs_image: str):
    return AppointmentTicket(asa_configuration=asa_configuration,
                             business_type=Ticket.BusinessType.appointment,
                             issuer=issuer,
                             ipfs_image=ipfs_image,
                             doctor_name=name,
                             duration=random.choice([1, 2]),
                             datetime=random.choice(["11.12.2021", "25.11.2022", "30.06.2022"]))


def create_random_restaurant_ticket(asa_configuration: ASAConfiguration,
                                    issuer: str,
                                    name: str,
                                    ipfs_image: str):
    return RestaurantTicket(asa_configuration=asa_configuration,
                            business_type=Ticket.BusinessType.restaurant,
                            issuer=issuer,
                            ipfs_image=ipfs_image,
                            name=name,
                            type=random.choice(["Food", "Drinks only"]),
                            datetime=random.choice(["11.12.2021", "25.11.2022", "30.06.2022"]))


def generate_concert_json_list():
    tickets_dummy = dict()
    tickets_dummy['concert_tickets'] = []

    for i in range(10):
        foo_fighters_config = create_random_asa_configuration(creator_address=FOO_FIGHTERS_ADDRESS,
                                                              asset_name="Foo Fighters")
        foo_fighters_config.asa_id = generate_id()

        foo_fighters_ticket = create_random_concert_ticket(foo_fighters_config,
                                                           issuer="Foo Fighters",
                                                           name="Foo Fighters - Sonic Highways Tour",
                                                           ipfs_image="https://gateway.pinata.cloud/ipfs/QmaXe7kVV2dAYTovruC8aBoReWC6peykvPS9FdYGqu4Qip")

        u2_fighters_config = create_random_asa_configuration(creator_address=U2_ADDRESS,
                                                             asset_name="U2")
        u2_fighters_config.asa_id = generate_id()

        u2_ticket = create_random_concert_ticket(u2_fighters_config,
                                                 issuer="U2",
                                                 name="U2 - The Joshua Tree Tour",
                                                 ipfs_image="https://gateway.pinata.cloud/ipfs/QmZdV3kWCAU9B6DvqP8McpdRngk111e1TNGykhttZbtCwe")

        tickets_dummy['concert_tickets'].append(foo_fighters_ticket.dict())
        tickets_dummy['concert_tickets'].append(u2_ticket.dict())

    save_json('../data/ui/concert_tickets_dummy.json', tickets_dummy)


def generate_movie_json_list():
    tickets_dummy = dict()
    tickets_dummy['cinema_tickets'] = []

    for i in range(10):
        primal_fear_config = create_random_asa_configuration(creator_address=FOO_FIGHTERS_ADDRESS,
                                                             asset_name="Primal Fear")
        primal_fear_config.asa_id = generate_id()

        primal_fear_config_ticket = create_random_cinema_ticket(asa_configuration=primal_fear_config,
                                                                issuer="Pathe",
                                                                ipfs_image="https://gateway.pinata.cloud/ipfs/QmY7Ywogdc2q6du8TyFjaCegpTpuZqZSpL9WiBJ5uLgV99",
                                                                movie_name="Primal Fear")

        gone_girl_config = create_random_asa_configuration(creator_address=U2_ADDRESS,
                                                           asset_name="Gone Girl")
        gone_girl_config.asa_id = generate_id()

        gone_girl_config_ticket = create_random_cinema_ticket(asa_configuration=primal_fear_config,
                                                              issuer="Pathe",
                                                              ipfs_image="https://gateway.pinata.cloud/ipfs/Qmb77e3kRjUFeMACs6twNKjgu2qdK7Xi4nL3aiTEonruAy",
                                                              movie_name="Gone Girl")

        tickets_dummy['cinema_tickets'].append(primal_fear_config_ticket.dict())
        tickets_dummy['cinema_tickets'].append(gone_girl_config_ticket.dict())

    save_json('../data/ui/cinema_tickets_dummy.json', tickets_dummy)


def generate_conference_json_list():
    tickets_dummy = dict()
    tickets_dummy['conference_tickets'] = []

    for i in range(10):
        algorand_conference_config = create_random_asa_configuration(creator_address=FOO_FIGHTERS_ADDRESS,
                                                                     asset_name="Foo Fighters")
        algorand_conference_config.asa_id = generate_id()

        algorand_conference_ticket = create_random_conference_ticket(algorand_conference_config,
                                                                     issuer="Algorand",
                                                                     name="Algorand Conference",
                                                                     ipfs_image="https://gateway.pinata.cloud/ipfs/QmaXe7kVV2dAYTovruC8aBoReWC6peykvPS9FdYGqu4Qip")

        tickets_dummy['conference_tickets'].append(algorand_conference_ticket.dict())

    save_json('../data/ui/conference_tickets_dummy.json', tickets_dummy)


def generate_appointment_json_list():
    tickets_dummy = dict()
    tickets_dummy['appointment_tickets'] = []

    for i in range(10):
        appointment_config = create_random_asa_configuration(creator_address=FOO_FIGHTERS_ADDRESS,
                                                             asset_name="Psychologist Appointment")
        appointment_config.asa_id = generate_id()

        appointment_ticket = create_random_appointment_ticket(appointment_config,
                                                              issuer="Medical Center",
                                                              name="Psychologist Appointment - Dr.Ana",
                                                              ipfs_image="https://gateway.pinata.cloud/ipfs/QmaXe7kVV2dAYTovruC8aBoReWC6peykvPS9FdYGqu4Qip")

        tickets_dummy['appointment_tickets'].append(appointment_ticket.dict())

    save_json('../data/ui/appointment_tickets_dummy.json', tickets_dummy)


def generate_restaurant_json_list():
    tickets_dummy = dict()
    tickets_dummy['restaurant_tickets'] = []

    for i in range(10):
        restaurant_config = create_random_asa_configuration(creator_address=FOO_FIGHTERS_ADDRESS,
                                                            asset_name="Jamie Oliver")
        restaurant_config.asa_id = generate_id()

        restaurant_ticket = create_random_restaurant_ticket(restaurant_config,
                                                            issuer="Jamie Oliver Inc",
                                                            name="Jamie Oliver",
                                                            ipfs_image="https://gateway.pinata.cloud/ipfs/QmaXe7kVV2dAYTovruC8aBoReWC6peykvPS9FdYGqu4Qip")

        tickets_dummy['restaurant_tickets'].append(restaurant_ticket.dict())

    save_json('../data/ui/restaurant_tickets_dummy.json', tickets_dummy)


if __name__ == '__main__':
    generate_concert_json_list()
    generate_restaurant_json_list()
    generate_appointment_json_list()
    generate_conference_json_list()
    generate_movie_json_list()
