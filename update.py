from os import getenv
from dotenv import load_dotenv
from pymongo import MongoClient

from vessel import Vessel
from barentswatch_service import get_vessel

load_dotenv()

client = MongoClient(getenv("MONGO_URI"))
db = client["tracker"]
vessels_collection = db["vessels"]

if __name__ == "__main__":
    for vessel_dict in vessels_collection.find():
        old_vessel = Vessel(**vessel_dict)
        vessel = get_vessel(old_vessel.mmsi).with_voyages(old_vessel.voyages)
        updated_vessel = vessel.with_voyages(vessel.updated_voyages())
        updated_vessel_dict = updated_vessel.dict()
        del updated_vessel_dict["_id"]
        vessels_collection.update_one(
            {"_id": vessel_dict["_id"]},
            {"$set": updated_vessel_dict},
        )
        print(updated_vessel)
