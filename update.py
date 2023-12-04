from os import getenv
import dateutil.parser
from dotenv import load_dotenv
from pydantic import ValidationError
from pymongo import MongoClient

from vessel import Vessel
from barentswatch_service import get_historic_ais, vessel_from_ais

load_dotenv()

client = MongoClient(getenv("MONGO_URI"))
db = client["tracker"]
vessels_collection = db["vessels"]

if __name__ == "__main__":
    for vessel_dict in vessels_collection.find():
        vessel = Vessel(**vessel_dict)

        historic_ais = get_historic_ais(int(vessel.mmsi), duration=1)
        for ais in historic_ais:
            try:
                datetime_str = ais["msgtime"]
                dtg = int(dateutil.parser.isoparse(datetime_str).timestamp())
                vessel = vessel_from_ais(vessel.mmsi, ais).with_voyages(vessel.voyages)
                vessel = vessel.with_voyages(vessel.updated_voyages(dtg))
            except ValidationError as e:
                print("Warning:", e)

        updated_vessel_dict = vessel.dict()
        del updated_vessel_dict["_id"]
        vessels_collection.update_one(
            {"_id": vessel_dict["_id"]},
            {"$set": updated_vessel_dict},
        )

        print(vessel)
