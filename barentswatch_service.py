import requests
import os
from time import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from geocoding_service import get_country

import vessel as models
from helpers import distance


access_token_cache = {
    "token": None,
    "created_at": 0,
}


def get_access_token():
    token_age = time() - access_token_cache["created_at"]
    if token_age < 3600:
        return access_token_cache["token"]

    load_dotenv()

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    response = requests.post(
        "https://id.barentswatch.no/connect/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "ais",
            "grant_type": "client_credentials",
        },
    )

    access_token = response.json()["access_token"]

    access_token_cache["token"] = access_token
    access_token_cache["created_at"] = time()

    return access_token


def vessel_from_ais(mmsi: str, ais: dict):
    return models.Vessel(
        mmsi=mmsi,
        name=ais["name"],
        lat=ais["latitude"],
        lng=ais["longitude"],
        speed=ais["speedOverGround"],
    )


def get_vessel(mmsi: str):
    token = get_access_token()
    response = requests.post(
        "https://live.ais.barentswatch.no/v1/latest/combined",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "mmsi": [int(mmsi)],
        },
    )

    ais = response.json()[0]

    return vessel_from_ais(mmsi, ais)


def search_for_vessel(query: str):
    token = get_access_token()
    response = requests.get(
        "https://historic.ais.barentswatch.no/open/v2/historic/search",
        params={"q": query},
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    return response.json()


def get_historic_ais(mmsi: int, duration=36):
    token = get_access_token()

    from_date = datetime.now() - timedelta(hours=duration)
    to_date = datetime.now()

    response = requests.get(
        f"https://historic.ais.barentswatch.no/open/v1/historic/tracks/{mmsi}/{from_date}/{to_date}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    return response.json()[::-1]


def get_historic_positions_from_mmsi(mmsi: int, duration=36, interval=40):
    for ais in get_historic_ais(mmsi, duration)[0::interval]:
        yield ais["latitude"], ais["longitude"]


def get_historic_ports(mmsi: int, duration=8766):
    stopped = False
    stopped_pos = (0, 0)
    results = []
    for ais in get_historic_ais(mmsi, duration=duration):
        pos = ais["latitude"], ais["longitude"]
        speed = ais["speedOverGround"]

        if stopped:
            dist = distance((pos), stopped_pos)
            if dist > 5:
                stopped = False
                country = get_country(*pos)
                results.append(country)
                print("LEFT PORT", pos)
        else:
            if speed < 0.5:
                stopped = True
                stopped_pos = pos
                print("ARRIVED PORT", pos)

    if not results:
        print("Available ais data:", get_historic_ais(mmsi))

    return results


if __name__ == "__main__":
    print(get_historic_ports(636018343))
