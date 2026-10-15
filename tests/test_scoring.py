import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from fuelfam.models import FuelPrice, ParsedSign
from fuelfam.scoring import MissingGpsError, ScoringProvider, _distance_score, _haversine_m


def test_haversine_same_point_is_zero():
    assert _haversine_m(41.0, -87.0, 41.0, -87.0) == 0


def test_haversine_small_latitude_offset():
    distance = _haversine_m(41.0, -87.0, 41.001, -87.0)
    assert distance == pytest.approx(111.19, rel=0.01)


def test_distance_score_decreases_with_distance():
    assert _distance_score(0) == 1.0
    assert _distance_score(100) < _distance_score(10)


def test_score_places_skips_missing_coordinates_and_sorts_by_score():
    provider = ScoringProvider(MagicMock(), MagicMock())
    matches = provider._score_places(
        41.0,
        -87.0,
        [
            {
                "id": "far",
                "displayName": {"text": "Far"},
                "location": {"latitude": 41.01, "longitude": -87.0},
            },
            {"id": "skipped", "location": {}},
            {
                "name": "places/near",
                "location": {"latitude": 41.0001, "longitude": -87.0},
            },
            {
                "id": "mid",
                "name": "ignored",
                "displayName": {"text": "Mid"},
                "location": {"latitude": 41.001, "longitude": -87.0},
            },
        ],
    )

    assert [(match.id, match.name) for match in matches] == [
        ("places/near", "places/near"),
        ("mid", "Mid"),
        ("far", "Far"),
    ]
    assert matches[0].score > matches[1].score > matches[2].score


def test_score_image_without_gps_removes_temp_file(monkeypatch):
    seen = {}

    def fake_gps(path):
        seen["path"] = path
        return {}

    monkeypatch.setattr("fuelfam.scoring.gpsphoto.getGPSData", fake_gps)
    provider = ScoringProvider(MagicMock(), MagicMock())

    with pytest.raises(MissingGpsError, match="Image has no GPS data"):
        provider.score_image(b"not-a-real-image", filename="sign.jpg")

    assert not Path(seen["path"]).exists()
    provider.places.search_nearby.assert_not_called()


def test_score_image_uses_gps_and_returns_ranked_matches(monkeypatch):
    monkeypatch.setattr(
        "fuelfam.scoring.gpsphoto.getGPSData",
        lambda path: {"Latitude": 41.0, "Longitude": -87.0},
    )
    places = MagicMock()
    places.search_nearby.return_value = {
        "places": [
            {
                "id": "far",
                "displayName": {"text": "Far"},
                "location": {"latitude": 41.01, "longitude": -87.0},
            },
            {
                "id": "near",
                "displayName": {"text": "Near"},
                "location": {"latitude": 41.0001, "longitude": -87.0},
            },
        ]
    }
    parsed = ParsedSign(
        station_name="Near",
        fuel_prices=[FuelPrice(grade="regular", price_per_gallon=3.5)],
    )
    vision = MagicMock()
    vision.parse_station_sign.return_value = parsed
    provider = ScoringProvider(places, vision)
    image = b"jpeg-bytes"

    result_parsed, matches = provider.score_image(
        image, filename="sign.png", media_type="image/png"
    )

    places.search_nearby.assert_called_once_with(41.0, -87.0)
    vision.parse_station_sign.assert_called_once_with(image, media_type="image/png")
    assert result_parsed == parsed
    assert [match.id for match in matches] == ["near", "far"]


def test_jpeg_without_exif_raises_missing_gps():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="JPEG")
    provider = ScoringProvider(MagicMock(), MagicMock())

    with pytest.raises(MissingGpsError, match="Image has no GPS data"):
        provider.score_image(buffer.getvalue(), filename="plain.jpg")

    provider.places.search_nearby.assert_not_called()
    provider.vision.parse_station_sign.assert_not_called()
