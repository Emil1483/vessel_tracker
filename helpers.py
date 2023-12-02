from math import pi, cos, asin, sqrt
import hashlib

from bson import ObjectId


def distance(pos1, pos2):
    lat1, lon1 = pos1
    lat2, lon2 = pos2

    r = 6371
    p = pi / 180

    a = (
        0.5
        - cos((lat2 - lat1) * p) / 2
        + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    )
    return 2 * r * asin(sqrt(a))


def hash_string(string: str, length=32):
    string_bytes = string.encode(encoding="utf8")
    hexdigest = hashlib.sha256(string_bytes).hexdigest()
    return hexdigest[:length]


def string_to_object_id(string: str) -> ObjectId:
    return ObjectId(hash_string(string, length=24))
