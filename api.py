import os

from flask import Flask, request
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError

from barentswatch_service import get_historic_positions_from_mmsi, get_vessel
from helpers import string_to_object_id
from vessel import Vessel

load_dotenv()

app = Flask(__name__)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)


@app.route("/vessels", methods=["POST"])
def create_vessel():
    data = request.get_json()
    mmsi = data.get("mmsi")
    comment = data.get("comment", None)

    vessel = get_vessel(mmsi)

    if comment:
        vessel = vessel.model_copy(update={"comment": comment})

    try:
        mongo.db.vessels.insert_one(vessel.dict())
    except DuplicateKeyError:
        return "This vessel is already added", 409

    return "OK", 201


@app.route("/vessel/<mmsi>", methods=["GET"])
def fetch_vessel(mmsi):
    result = mongo.db.vessels.find_one({"_id": string_to_object_id(mmsi)})
    if not result:
        return f"vessel with mmsi '{mmsi}' not found", 404
    del result["_id"]

    mmsi = result["mmsi"]
    historic = get_historic_positions_from_mmsi(mmsi)

    return {
        **result,
        "historic_ais": [{"lat": lat, "lng": lng} for lat, lng in historic],
    }


@app.route("/vessels", methods=["GET"])
def get_all_vessels():
    vessels = mongo.db.vessels.find()

    def gen():
        for vessel_dict in vessels:
            del vessel_dict["_id"]
            yield vessel_dict

    return [*gen()]


@app.route("/vessels/<mmsi>", methods=["DELETE"])
def delete_vessel(mmsi):
    result = mongo.db.vessels.delete_one({"_id": string_to_object_id(mmsi)})
    if result.deleted_count > 0:
        return "OK"
    else:
        return "Vessel not found", 404


@app.route("/vessels/<mmsi>", methods=["PATCH"])
def update_vessel(mmsi):
    _id = string_to_object_id(mmsi)
    result = mongo.db.vessels.find_one({"_id": _id})
    if not result:
        return f"vessel with mmsi '{mmsi}' not found", 404

    vessel = Vessel(**result).model_copy(update=request.get_json())

    mongo.db.vessels.update_one(
        {"_id": _id},
        {"$set": vessel.dict()},
    )

    return "OK"


@app.route("/lookup_mmsi/<mmsi>")
def lookup_mmsi(mmsi: str):
    vessel = get_vessel(mmsi)
    vessel_dict = vessel.dict()
    del vessel_dict["_id"]
    return vessel_dict


if __name__ == "__main__":
    app.run(debug=True, port=3000)
