from datetime import datetime
from enum import Enum
from bson.objectid import ObjectId
from pydantic import BaseModel, Field, validator, computed_field

from helpers import string_to_object_id
from geocoding_service import get_port_name


class State(Enum):
    arrived_port = "arrived_port"
    at_port = "at_port"
    left_port = "left_port"
    sailing = "sailing"


class Voyage(BaseModel):
    port: str
    ata: int
    atd: int
    lat: float
    lng: float

    def with_atd(self, atd: int):
        return self.model_copy(update={"atd": atd})


class Vessel(BaseModel):
    mmsi: str
    name: str
    lat: float
    lng: float
    speed: float
    voyages: list[Voyage] = []

    def with_voyages(self, voyages: list[Voyage]):
        return self.model_copy(update={"voyages": voyages})

    def get_state(self):
        was_sailing = False
        if not self.voyages:
            was_sailing = True
        elif self.voyages[-1].atd > 0:
            was_sailing = True

        if was_sailing:
            if self.speed < 0.5:
                return State.arrived_port
            else:
                return State.sailing

        if self.speed < 0.5:
            return State.at_port
        else:
            return State.left_port

    def updated_voyages(self):
        now = int(datetime.now().timestamp())
        state = self.get_state()
        print(f"state: {state}")

        if state == State.arrived_port:
            return [
                *self.voyages,
                Voyage(
                    port=get_port_name(self.lat, self.lng),
                    lat=self.lat,
                    lng=self.lng,
                    ata=now,
                    atd=-1,
                ),
            ]

        if state == State.at_port:
            return [*self.voyages]

        if state == State.left_port:
            return [*self.voyages[:-1], self.voyages[-1].with_atd(now)]

        if state == State.sailing:
            return [*self.voyages]

        raise NotImplementedError(f"state {state} not implemented")

    class Config:
        arbitrary_types_allowed = True

    @computed_field()
    def _id(self) -> ObjectId:
        return string_to_object_id(self.mmsi)
