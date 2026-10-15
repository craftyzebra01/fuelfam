import os
import tempfile
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path

from GPSPhoto import gpsphoto

from fuelfam.models import ParsedSign, StationMatch
from fuelfam.places import GooglePlacesProvider
from fuelfam.vision import ComputerVisionProvider

_EARTH_RADIUS_M = 6_371_000


class MissingGpsError(ValueError):
    pass


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * atan2(sqrt(a), sqrt(1 - a))


def _distance_score(distance_m: float) -> float:
    return 1.0 / (1.0 + distance_m)


class ScoringProvider:
    def __init__(
        self,
        places_provider: GooglePlacesProvider,
        vision: ComputerVisionProvider,
    ):
        self.places = places_provider
        self.vision = vision

    def score_image(
        self,
        image_bytes: bytes,
        *,
        filename: str | None = None,
        media_type: str = "image/jpeg",
    ) -> tuple[ParsedSign, list[StationMatch]]:
        suffix = Path(filename or "upload.jpg").suffix or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            gps = gpsphoto.getGPSData(tmp_path)
        finally:
            os.unlink(tmp_path)

        lat = gps.get("Latitude") if gps else None
        lon = gps.get("Longitude") if gps else None
        if lat is None or lon is None:
            raise MissingGpsError("Image has no GPS data")

        nearby = self.places.search_nearby(lat, lon)
        matches = self._score_places(lat, lon, nearby.get("places") or [])
        parsed = self.vision.parse_station_sign(image_bytes, media_type=media_type)
        return parsed, matches

    def _score_places(
        self, lat: float, lon: float, places: list[dict]
    ) -> list[StationMatch]:
        matches: list[StationMatch] = []
        for place in places:
            location = place.get("location") or {}
            place_lat = location.get("latitude")
            place_lon = location.get("longitude")
            if place_lat is None or place_lon is None:
                continue
            display = place.get("displayName") or {}
            name = display.get("text") or place.get("name") or ""
            place_id = place.get("id") or place.get("name") or ""
            distance = _haversine_m(lat, lon, place_lat, place_lon)
            matches.append(
                StationMatch(
                    id=place_id,
                    name=name,
                    distance=distance,
                    score=_distance_score(distance),
                )
            )
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches
