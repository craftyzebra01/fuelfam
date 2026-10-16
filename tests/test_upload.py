import os
import uuid

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from fastapi.testclient import TestClient

import fuelfam.main as main
from fuelfam.main import app
from fuelfam.models import FuelPrice, ParsedSign, StationMatch
from fuelfam.scoring import MissingGpsError

client = TestClient(app)


def _parsed_sign():
    return ParsedSign(
        station_name="BP",
        fuel_prices=[FuelPrice(grade="regular", price_per_gallon=3.19)],
    )


def _matches():
    return [StationMatch(id="place-1", name="BP", distance=12.0, score=0.5)]


def test_upload_returns_confirmation(monkeypatch):
    parsed = _parsed_sign()
    matches = _matches()
    calls = []

    def fake_score(image_bytes, *, filename=None, media_type="image/jpeg"):
        calls.append((image_bytes, filename, media_type))
        return parsed, matches

    monkeypatch.setattr(main.scoring_provider, "score_image", fake_score)

    response = client.post(
        "/uploadStationInfo",
        files={"file": ("sign.jpg", b"img", "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    uuid.UUID(body["upload_id"])
    assert body["file_name"] == "sign.jpg"
    assert body["parsed"] == parsed.model_dump()
    assert body["matches"] == [match.model_dump() for match in matches]
    assert calls == [(b"img", "sign.jpg", "image/jpeg")]
    stored = main.upload_requests.get(body["upload_id"])
    assert stored is not None
    assert stored.upload_id == body["upload_id"]
    assert stored.matches == matches


def test_upload_defaults_missing_content_type_and_filename(monkeypatch):
    calls = []

    def fake_score(image_bytes, *, filename=None, media_type="image/jpeg"):
        calls.append((filename, media_type))
        return _parsed_sign(), _matches()

    monkeypatch.setattr(main.scoring_provider, "score_image", fake_score)
    body = (
        b"--boundary\r\n"
        b'Content-Disposition: form-data; name="file"; filename=""\r\n'
        b"\r\n"
        b"img\r\n"
        b"--boundary--\r\n"
    )

    response = client.post(
        "/uploadStationInfo",
        content=body,
        headers={"content-type": "multipart/form-data; boundary=boundary"},
    )

    assert response.status_code == 200
    assert response.json()["file_name"] == "upload.jpg"
    assert calls == [("", "image/jpeg")]


def test_upload_without_gps_is_bad_request(monkeypatch):
    def fake_score(image_bytes, *, filename=None, media_type="image/jpeg"):
        raise MissingGpsError("Image has no GPS data")

    monkeypatch.setattr(main.scoring_provider, "score_image", fake_score)
    before = dict(main.upload_requests.requests)

    response = client.post(
        "/uploadStationInfo",
        files={"file": ("sign.jpg", b"img", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Image has no GPS data"
    assert main.upload_requests.requests == before


def test_confirm_returns_success():
    response = client.post("/uploadStationInfo/abc-123/confirm")

    assert response.status_code == 200
    assert response.json() == {"upload_id": "abc-123", "status": "success"}
