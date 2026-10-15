from unittest.mock import MagicMock

import pytest
import requests

from fuelfam.places import GooglePlacesProvider

PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"


def _mock_post(monkeypatch, payload=None):
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {"places": []}
    post = MagicMock(return_value=response)
    monkeypatch.setattr("fuelfam.places.requests.post", post)
    return post, response


def test_search_nearby_default_request(monkeypatch):
    post, response = _mock_post(monkeypatch)
    provider = GooglePlacesProvider("test-key")

    assert provider.search_nearby(41.9, -87.6) == {"places": []}

    post.assert_called_once_with(
        PLACES_URL,
        json={
            "includedTypes": ["gas_station"],
            "maxResultCount": 10,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": 41.9, "longitude": -87.6},
                    "radius": 500.0,
                }
            },
        },
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": "test-key",
            "X-Goog-FieldMask": "places.id,places.displayName,places.location",
        },
    )
    response.raise_for_status.assert_called_once()


def test_included_types_default_is_not_shared(monkeypatch):
    post, _response = _mock_post(monkeypatch, payload={})
    provider = GooglePlacesProvider("test-key")
    custom = ["convenience_store"]

    provider.search_nearby(1.0, 2.0, included_types=custom)
    first = list(post.call_args.kwargs["json"]["includedTypes"])
    custom.append("cafe")
    provider.search_nearby(1.0, 2.0)

    second = post.call_args.kwargs["json"]["includedTypes"]
    assert first == ["convenience_store"]
    assert second == ["gas_station"]


def test_search_nearby_raises_on_http_error(monkeypatch):
    _post, response = _mock_post(monkeypatch)
    response.raise_for_status.side_effect = requests.HTTPError("nope")

    with pytest.raises(requests.HTTPError):
        GooglePlacesProvider("test-key").search_nearby(1.0, 2.0)
