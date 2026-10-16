import uuid

from fuelfam.models import FuelPrice
from fuelfam.scoring import _haversine_m
from fuelfam.storage import (
    BP_LINCOLN_ID,
    BP_LINCOLN_PLACE_ID,
    BP_WESTERN_ID,
    BP_WESTERN_PLACE_ID,
    GOOGLE_PLACES,
    SHELL_ASHLAND_ID,
    SHELL_ASHLAND_PLACE_ID,
    InMemoryStationRepository,
    InMemoryUploadRequestProvider,
)


def _repo():
    return InMemoryStationRepository()


def test_seed_has_three_stations_with_external_ids_and_prices():
    repo = _repo()

    assert [(station.id, station.name) for station in repo.stations] == [
        (BP_LINCOLN_ID, "BP"),
        (SHELL_ASHLAND_ID, "Shell"),
        (BP_WESTERN_ID, "BP"),
    ]
    assert [
        (record.station_id, record.source, record.external_id) for record in repo.external_ids
    ] == [
        (BP_LINCOLN_ID, GOOGLE_PLACES, BP_LINCOLN_PLACE_ID),
        (SHELL_ASHLAND_ID, GOOGLE_PLACES, SHELL_ASHLAND_PLACE_ID),
        (BP_WESTERN_ID, GOOGLE_PLACES, BP_WESTERN_PLACE_ID),
    ]

    lincoln = repo.stations[0]
    shell = repo.stations[1]
    western = repo.stations[2]
    assert _haversine_m(lincoln.latitude, lincoln.longitude, shell.latitude, shell.longitude) > 100
    assert _haversine_m(lincoln.latitude, lincoln.longitude, western.latitude, western.longitude) > 100

    assert [(entry.grade, entry.price_per_gallon) for entry in repo.prices_for(BP_LINCOLN_ID)] == [
        ("regular", 3.19),
        ("midgrade", 3.59),
        ("premium", 3.89),
    ]
    assert [(entry.grade, entry.price_per_gallon) for entry in repo.prices_for(SHELL_ASHLAND_ID)] == [
        ("regular", 3.29),
        ("midgrade", 3.69),
        ("premium", 3.99),
    ]
    assert [(entry.grade, entry.price_per_gallon) for entry in repo.prices_for(BP_WESTERN_ID)] == [
        ("regular", 3.09),
        ("midgrade", 3.49),
        ("premium", 3.79),
    ]


def test_new_station_gets_an_id():
    repo = _repo()

    station = repo.get_or_create_station("Mobil", 41.0, -87.0)

    uuid.UUID(station.id)
    assert station.id not in {BP_LINCOLN_ID, SHELL_ASHLAND_ID, BP_WESTERN_ID}
    assert station in repo.stations


def test_same_google_place_id_returns_same_station():
    repo = _repo()

    station = repo.get_or_create_station(
        "Other",
        40.0,
        -80.0,
        source=GOOGLE_PLACES,
        external_id=BP_LINCOLN_PLACE_ID,
    )

    assert station.id == BP_LINCOLN_ID
    assert len(repo.stations) == 3


def test_same_name_within_100m_links_external_id():
    repo = _repo()
    lincoln = repo.stations[0]

    station = repo.get_or_create_station(
        "BP",
        lincoln.latitude + 0.0004,
        lincoln.longitude,
        source=GOOGLE_PLACES,
        external_id="places/bp-nearby",
    )

    assert station.id == BP_LINCOLN_ID
    assert len(repo.stations) == 3
    assert any(
        record.station_id == BP_LINCOLN_ID and record.external_id == "places/bp-nearby"
        for record in repo.external_ids
    )


def test_same_name_beyond_100m_creates_a_station():
    repo = _repo()
    lincoln = repo.stations[0]

    station = repo.get_or_create_station(
        "BP",
        lincoln.latitude + 0.002,
        lincoln.longitude,
        source=GOOGLE_PLACES,
        external_id="places/bp-far",
    )

    assert station.id not in {BP_LINCOLN_ID, BP_WESTERN_ID}
    uuid.UUID(station.id)
    assert [(item.id, item.name) for item in repo.stations if item.name == "BP"][-1] == (
        station.id,
        "BP",
    )
    assert any(record.external_id == "places/bp-far" for record in repo.external_ids)


def test_nearest_same_name_within_100m_wins():
    repo = _repo()
    latitude = 42.0
    near = repo.get_or_create_station(
        "Exxon",
        latitude,
        -87.65,
        source=GOOGLE_PLACES,
        external_id="places/exxon-near",
    )
    far = repo.get_or_create_station(
        "Exxon",
        latitude + 0.0012,
        -87.65,
        source=GOOGLE_PLACES,
        external_id="places/exxon-far",
    )

    station = repo.get_or_create_station(
        "Exxon",
        latitude + 0.00035,
        -87.65,
        source=GOOGLE_PLACES,
        external_id="places/exxon-query",
    )

    assert station.id == near.id
    assert station.id != far.id
    assert any(
        record.station_id == near.id and record.external_id == "places/exxon-query"
        for record in repo.external_ids
    )


def test_different_name_within_100m_creates_a_station():
    repo = _repo()
    lincoln = repo.stations[0]

    station = repo.get_or_create_station(
        "Costco",
        lincoln.latitude,
        lincoln.longitude,
        source=GOOGLE_PLACES,
        external_id="places/costco",
    )

    assert station.id not in {BP_LINCOLN_ID, SHELL_ASHLAND_ID, BP_WESTERN_ID}
    assert station.name == "Costco"
    assert len(repo.stations) == 4


def test_add_prices_stores_one_row_per_grade():
    repo = _repo()

    added = repo.add_prices(
        BP_LINCOLN_ID,
        [
            FuelPrice(grade="diesel", price_per_gallon=4.09),
            FuelPrice(grade="regular", price_per_gallon=3.25),
        ],
    )

    assert [(entry.grade, entry.price_per_gallon) for entry in added] == [
        ("diesel", 4.09),
        ("regular", 3.25),
    ]
    stored = repo.prices_for(BP_LINCOLN_ID)
    assert stored[-2:] == added
    assert [entry.grade for entry in stored] == [
        "regular",
        "midgrade",
        "premium",
        "diesel",
        "regular",
    ]


def test_upload_request_get_missing_id():
    provider = InMemoryUploadRequestProvider()

    assert provider.get("missing") is None
