from datetime import datetime
from os import getenv
import dateutil.parser
from dotenv import load_dotenv
from pydantic import ValidationError
from pymongo import MongoClient
from mailer import send_mail

from vessel import Vessel
from barentswatch_service import get_historic_ais, vessel_from_ais

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
                vessel = vessel_from_ais(vessel.mmsi, ais).with_voyages(vessel.voyages)
                vessel = vessel.with_voyages(vessel.updated_voyages(dtg))
            except ValidationError as e:
                print("Warning:", e)

        if len(vessel.voyages) > len(old_vessel.voyages):
            port_name = vessel.voyages[-1].port
            ata = vessel.voyages[-1].ata
            ata_datetime = datetime.utcfromtimestamp(ata)
            ata_string = ata_datetime.strftime("%d %H%MZ %b %Y").upper()
            send_mail(
                f"{vessel.name} - {vessel.mmsi}",
                f"The vessel {vessel.name} has arrived at port {port_name}"
                f"With ATA {ata_string}",
            )

        elif vessel.voyages and vessel.voyages[-1].atd > old_vessel.voyages[-1].atd:
            port_name = vessel.voyages[-1].port
            ata = vessel.voyages[-1].ata
            atd_datetime = datetime.utcfromtimestamp(ata)
            atd_string = atd_datetime.strftime("%d %H%MZ %b %Y").upper()

        updated_vessel_dict = vessel.dict()
        del updated_vessel_dict["_id"]
        vessels_collection.update_one(
            {"_id": vessel_dict["_id"]},
            {"$set": updated_vessel_dict},
        )

        print(vessel)
