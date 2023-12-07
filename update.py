from datetime import datetime
from os import getenv
import dateutil.parser
from dotenv import load_dotenv
from pydantic import ValidationError
from pymongo import MongoClient
from mailer import send_mail

from vessel import Vessel
from barentswatch_service import get_historic_ais, vessel_from_ais
from helpers import read_html

load_dotenv()

client = MongoClient(getenv("MONGO_URI"))
db = client["tracker"]
vessels_collection = db["vessels"]

if __name__ == "__main__":
    for vessel_dict in vessels_collection.find():
        vessel = Vessel(**vessel_dict)
        old_vessel = vessel.model_copy()

        historic_ais = get_historic_ais(int(vessel.mmsi), duration=1)
        for ais in historic_ais:
            try:
                datetime_str = ais["msgtime"]
                dtg = int(dateutil.parser.isoparse(datetime_str).timestamp())
                vessel = vessel.with_ais(ais)
                vessel = vessel.with_voyages(vessel.updated_voyages(dtg))
            except ValidationError as e:
                print("Warning:", e)

        vessel = vessel.with_voyages(vessel.voyages[-20:])

        if vessel.notify_on_arrived and len(vessel.voyages) > len(old_vessel.voyages):
            port_name = vessel.voyages[-1].port
            ata = vessel.voyages[-1].ata
            ata_datetime = datetime.utcfromtimestamp(ata)
            ata_string = ata_datetime.strftime("%d %H%MZ %b %Y").upper()
            vessel_string = vessel.name
            if vessel.comment:
                vessel_string += f" ({vessel.comment})"

            send_mail(
                f"{vessel.name} - {vessel.mmsi}",
                read_html("arrival.html")
                .replace("{ATA}", ata_string)
                .replace("{PORT}", port_name)
                .replace("{VESSEL}", vessel_string),
                content_type="html",
            )

        elif (
            vessel.notify_on_left
            and vessel.voyages
            and vessel.voyages[-1].atd > old_vessel.voyages[-1].atd
        ):
            port_name = vessel.voyages[-1].port
            ata = vessel.voyages[-1].ata
            atd_datetime = datetime.utcfromtimestamp(ata)
            atd_string = atd_datetime.strftime("%d %H%MZ %b %Y").upper()
            vessel_string = vessel.name
            if vessel.comment:
                vessel_string += f" ({vessel.comment})"

            send_mail(
                f"{vessel.name} - {vessel.mmsi}",
                read_html("departure.html")
                .replace("{ATD}", atd_string)
                .replace("{PORT}", port_name)
                .replace("{VESSEL}", vessel_string),
                content_type="html",
            )

        updated_vessel_dict = vessel.dict()
        del updated_vessel_dict["_id"]
        vessels_collection.update_one(
            {"_id": vessel_dict["_id"]},
            {"$set": updated_vessel_dict},
        )

        print(vessel)
