import uuid

from fuelfam.models import (
    ExternalId,
    FuelPrice,
    PriceEntry,
    Station,
    StationMatch,
    UploadRequest,
)
from fuelfam.scoring import _haversine_m

GOOGLE_PLACES = "google_places"
_MATCH_RADIUS_M = 100.0

BP_LINCOLN_ID = "station-bp-lincoln"
SHELL_ASHLAND_ID = "station-shell-ashland"
BP_WESTERN_ID = "station-bp-western"

BP_LINCOLN_PLACE_ID = "places/bp-lincoln"
SHELL_ASHLAND_PLACE_ID = "places/shell-ashland"
BP_WESTERN_PLACE_ID = "places/bp-western"

# About 41.97, -87.65. Shell is ~445 m north of the first BP.
# The second BP is ~1.1 km north, so the same brand is a separate station.
_BP_LINCOLN = (41.9700, -87.6500)
_SHELL_ASHLAND = (41.9740, -87.6500)
_BP_WESTERN = (41.9800, -87.6500)


def _prices(station_id: str, grades: list[tuple[str, float]]) -> list[PriceEntry]:
    return [
        PriceEntry(
            id=f"price-{station_id}-{grade}",
            station_id=station_id,
            grade=grade,
            price_per_gallon=price,
        )
        for grade, price in grades
    ]


class InMemoryStationRepository:
    def __init__(self) -> None:
        self.stations: list[Station] = [
            Station(
                id=BP_LINCOLN_ID,
                name="BP",
                latitude=_BP_LINCOLN[0],
                longitude=_BP_LINCOLN[1],
            ),
            Station(
                id=SHELL_ASHLAND_ID,
                name="Shell",
                latitude=_SHELL_ASHLAND[0],
                longitude=_SHELL_ASHLAND[1],
            ),
            Station(
                id=BP_WESTERN_ID,
                name="BP",
                latitude=_BP_WESTERN[0],
                longitude=_BP_WESTERN[1],
            ),
        ]
        self.external_ids: list[ExternalId] = [
            ExternalId(
                station_id=BP_LINCOLN_ID,
                source=GOOGLE_PLACES,
                external_id=BP_LINCOLN_PLACE_ID,
            ),
            ExternalId(
                station_id=SHELL_ASHLAND_ID,
                source=GOOGLE_PLACES,
                external_id=SHELL_ASHLAND_PLACE_ID,
            ),
            ExternalId(
                station_id=BP_WESTERN_ID,
                source=GOOGLE_PLACES,
                external_id=BP_WESTERN_PLACE_ID,
            ),
        ]
        self.price_entries: list[PriceEntry] = [
            *_prices(
                BP_LINCOLN_ID,
                [("regular", 3.19), ("midgrade", 3.59), ("premium", 3.89)],
            ),
            *_prices(
                SHELL_ASHLAND_ID,
                [("regular", 3.29), ("midgrade", 3.69), ("premium", 3.99)],
            ),
            *_prices(
                BP_WESTERN_ID,
                [("regular", 3.09), ("midgrade", 3.49), ("premium", 3.79)],
            ),
        ]

    def get_or_create_station(
        self,
        name: str,
        latitude: float,
        longitude: float,
        *,
        source: str | None = None,
        external_id: str | None = None,
    ) -> Station:
        if source is not None and external_id is not None:
            existing = self._station_for_external_id(source, external_id)
            if existing is not None:
                return existing

        nearest = self._nearest_same_name(name, latitude, longitude)
        if nearest is not None:
            self._link_external_id(nearest.id, source, external_id)
            return nearest

        station = Station(
            id=str(uuid.uuid4()),
            name=name,
            latitude=latitude,
            longitude=longitude,
        )
        self.stations.append(station)
        self._link_external_id(station.id, source, external_id)
        return station

    def add_prices(self, station_id: str, grades: list[FuelPrice]) -> list[PriceEntry]:
        if self._station_by_id(station_id) is None:
            raise KeyError(station_id)
        entries = [
            PriceEntry(
                id=str(uuid.uuid4()),
                station_id=station_id,
                grade=grade.grade,
                price_per_gallon=grade.price_per_gallon,
            )
            for grade in grades
        ]
        self.price_entries.extend(entries)
        return entries

    def prices_for(self, station_id: str) -> list[PriceEntry]:
        return [entry for entry in self.price_entries if entry.station_id == station_id]

    def _station_by_id(self, station_id: str) -> Station | None:
        for station in self.stations:
            if station.id == station_id:
                return station
        return None

    def _station_for_external_id(self, source: str, external_id: str) -> Station | None:
        for record in self.external_ids:
            if record.source == source and record.external_id == external_id:
                return self._station_by_id(record.station_id)
        return None

    def _nearest_same_name(
        self, name: str, latitude: float, longitude: float
    ) -> Station | None:
        nearest: Station | None = None
        nearest_distance: float | None = None
        for station in self.stations:
            if station.name != name:
                continue
            distance = _haversine_m(
                latitude, longitude, station.latitude, station.longitude
            )
            if distance > _MATCH_RADIUS_M:
                continue
            if nearest_distance is None or distance < nearest_distance:
                nearest = station
                nearest_distance = distance
        return nearest

    def _link_external_id(
        self, station_id: str, source: str | None, external_id: str | None
    ) -> None:
        if source is None or external_id is None:
            return
        for record in self.external_ids:
            if record.source == source and record.external_id == external_id:
                return
        self.external_ids.append(
            ExternalId(station_id=station_id, source=source, external_id=external_id)
        )


class InMemoryUploadRequestProvider:
    def __init__(self) -> None:
        self.requests: dict[str, UploadRequest] = {}

    def create(self, upload_id: str, matches: list[StationMatch]) -> UploadRequest:
        request = UploadRequest(upload_id=upload_id, matches=matches)
        self.requests[upload_id] = request
        return request

    def get(self, upload_id: str) -> UploadRequest | None:
        return self.requests.get(upload_id)
