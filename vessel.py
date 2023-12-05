from datetime import datetime
from enum import Enum
from bson.objectid import ObjectId
from pydantic import BaseModel, computed_field
import barentswatch_service as barents
import dateutil.parser

from helpers import distance, string_to_object_id
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
    notify_on_arrived: bool = False
    notify_on_left: bool = False

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
                print("arrived port with speed", self.speed)
                return State.arrived_port
            else:
                return State.sailing

        prev_port = self.voyages[-1]
        distance_to_port = distance(
            (prev_port.lat, prev_port.lng),
            (self.lat, self.lng),
        )

        if distance_to_port > 0.1 and self.speed > 0.5:
            print("left port with distance", distance_to_port, "and speed", self.speed)
            return State.left_port
        else:
            return State.at_port

    def updated_voyages(self, dtg: int):
        state = self.get_state()

        if state == State.arrived_port:
            return [
                *self.voyages,
                Voyage(
                    port=get_port_name(self.lat, self.lng),
                    lat=self.lat,
                    lng=self.lng,
                    ata=dtg,
                    atd=-1,
                ),
            ]

        if state == State.at_port:
            return [*self.voyages]

        if state == State.left_port:
            return [*self.voyages[:-1], self.voyages[-1].with_atd(dtg)]

        if state == State.sailing:
            return [*self.voyages]

        raise NotImplementedError(f"state {state} not implemented")

    class Config:
        arbitrary_types_allowed = True

    @computed_field()
    def _id(self) -> ObjectId:
        return string_to_object_id(self.mmsi)
