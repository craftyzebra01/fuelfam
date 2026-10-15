import base64
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from fuelfam.models import FuelPrice, ParsedSign
from fuelfam.vision import AnthropicComputerVisionProvider, _SIGN_PROMPT


def test_parse_station_sign_sends_image_and_returns_parsed():
    parsed = ParsedSign(
        station_name="BP",
        fuel_prices=[FuelPrice(grade="regular", price_per_gallon=3.19)],
    )
    client = MagicMock()
    client.messages.parse.return_value = SimpleNamespace(parsed_output=parsed)
    image = b"\xff\xd8fake"

    result = AnthropicComputerVisionProvider(client).parse_station_sign(
        image, media_type="image/png"
    )

    assert result is parsed
    kwargs = client.messages.parse.call_args.kwargs
    assert kwargs["model"] == "claude-haiku-5-5"
    assert kwargs["max_tokens"] == 2048
    assert kwargs["output_format"] is ParsedSign
    content = kwargs["messages"][0]["content"]
    assert content[0]["source"]["media_type"] == "image/png"
    assert content[0]["source"]["data"] == base64.b64encode(image).decode("utf-8")
    assert content[1]["text"] == _SIGN_PROMPT


def test_parse_station_sign_raises_when_output_is_missing():
    client = MagicMock()
    client.messages.parse.return_value = SimpleNamespace(parsed_output=None)

    with pytest.raises(ValueError, match="Failed to parse station sign from image"):
        AnthropicComputerVisionProvider(client).parse_station_sign(b"x")
