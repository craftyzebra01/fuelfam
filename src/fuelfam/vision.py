import base64
from typing import Protocol

from anthropic import Anthropic

from fuelfam.models import ParsedSign

_SIGN_PROMPT = (
    "Read the fuel price sign in this image. Return the station name "
    "and every fuel grade shown, each with its price per gallon. "
    "Include all grades visible on the sign."
)


class ComputerVisionProvider(Protocol):
    def parse_station_sign(
        self, image_bytes: bytes, *, media_type: str = "image/jpeg"
    ) -> ParsedSign: ...


class AnthropicComputerVisionProvider:
    def __init__(self, client: Anthropic):
        self.client = client

    def parse_station_sign(
        self, image_bytes: bytes, *, media_type: str = "image/jpeg"
    ) -> ParsedSign:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = self.client.messages.parse(
            model="claude-haiku-5-5",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": _SIGN_PROMPT,
                        },
                    ],
                }
            ],
            output_format=ParsedSign,
        )
        parsed = response.parsed_output
        if parsed is None:
            raise ValueError("Failed to parse station sign from image")
        return parsed
