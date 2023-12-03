import googlemaps
from dotenv import load_dotenv

from os import getenv

load_dotenv()

gmaps = googlemaps.Client(key=getenv("GEOCODING_API_KEY"))


def get_port_name(lat: float, lng: float):
    geocode_results = gmaps.reverse_geocode((lat, lng))

    for part in geocode_results:
        for component in part["address_components"]:
            if "postal_town" in component["types"]:
                return component["long_name"]

    for part in geocode_results:
        for component in part["address_components"]:
            if "administrative_area_level_2" in component["types"]:
                return component["long_name"]

    return geocode_results[0]["formatted_address"]


if __name__ == "__main__":
    print(get_port_name(59.012605, 10.977027))
    print(get_port_name(59.214866, 3.397548))
    print(get_port_name(62.094867, 4.995103))
