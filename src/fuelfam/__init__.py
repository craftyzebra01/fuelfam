import os
import base64
import requests
import json
from fuelfam.imp import imp
from dotenv import load_dotenv
from anthropic import Anthropic
from PIL import Image
from pydantic import BaseModel
from decimal import Decimal

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

GAS_IMAGE = "IMG_9252.jpeg"
IMAGE_NAME = "IMG_9253.jpeg"

# client = Anthropic(api_key="")

class GasStationImageInfo(BaseModel):
    name: str
    prices: dict[str, Decimal]


def search_nearby(lat, long, radius=500.0, max_results=10, included_types=["gas_station"]):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.name"
    }
    data = {
        "includedTypes": included_types,
        "maxResultCount": max_results,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": long,
                },
                "radius": radius
            }
        }
    }
    url = "https://places.googleapis.com/v1/places:searchNearby"
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status
    return response.json()

def imp() -> None: 
    im = Image.open(IMAGE_NAME)
    exif = im.getexif()
    for k,v in exif.items():
        print(f"{k}: {v}")


def get_station_details(image_base_64, client: Anthropic):
    response = client.messages.parse(
        model="claude-haiku-5-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base_64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Return the name of the gas station along with each type of gas and the corresponding price."
                    }
                ]
            }
        ],
        output_format=GasStationImageInfo
    )
    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)

def _image_to_base64(image_path) -> str:
    with open(image_path, "rb") as image_file:
        base64_bytes = base64.b64encode(image_file.read())
        base64_string = base64_bytes.decode("utf-8")
        return base64_string

def main() -> None:
    # lat: 41.968644
    # long: -87.649874
    # with open("response.json", "w+") as f:
        # json.dump(response.json(), f, indent=2)
    client = Anthropic()
    img64 = _image_to_base64(GAS_IMAGE)
    response = get_station_details(img64, client)
    print(response)

    print("Done!")





