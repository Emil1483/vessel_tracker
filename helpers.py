from math import pi, cos, asin, sqrt
import hashlib
import os

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


def path(file=None):
    return os.path.dirname(os.path.realpath(file or __file__))


def assert_extension(filename, required_extension):
    _, extension = os.path.splitext(filename)
    assert (
        extension == required_extension
    ), f"file {filename} must end in {required_extension}"


def read_html(file, fallback=None):
    assert_extension(file, ".html")

    if os.path.exists(f"{path()}/{file}"):
        with open(f"{path()}/{file}", "r", encoding="utf-8") as f:
            return f.read()

    with open(f"{path()}/{file}", "w") as f:
        string = fallback or ""
        f.write(string)
        return string
