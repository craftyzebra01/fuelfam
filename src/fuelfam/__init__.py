import os
import base64
import requests
import json
# from fuelfam.imp import imp
from dotenv import load_dotenv
from anthropic import Anthropic
from PIL import Image
from pydantic import BaseModel
from decimal import Decimal
from fastapi import FastAPI
from GPSPhoto import gpsphoto
from fuelfam.storage import SqliteStationRepository

load_dotenv()


GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

GAS_IMAGE = "IMG_9252.jpeg"
IMAGE_NAME = "IMG_9253.jpeg"

# client = Anthropic(api_key="")

class FuelPrice(BaseModel):
    grade: str
    price_per_gallon: float

class GasStationImageInfo(BaseModel):
    station_name: str
    fuel_prices: list[FuelPrice]

def search_nearby(lat, long, radius=500.0, max_results=10, included_types=None):
    if included_types is None:
        included_types = ["gas_station"]
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
        max_tokens=2048,
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
                        "text": (
                            "Read the fuel price sign in this image. Return the station name "
                            "and every fuel grade shown, each with its price per gallon. "
                            "Include all grades visible on the sign."
                        ),
                    }
                ]
            }
        ],
        output_format=GasStationImageInfo
    )
    # text = next(block.text for block in response.content if block.type == "text")
    # return json.loads(text)
    return response

def _image_to_base64(image_path) -> str:
    with open(image_path, "rb") as image_file:
        base64_bytes = base64.b64encode(image_file.read())
        base64_string = base64_bytes.decode("utf-8")
        return base64_string

# @app.get("/")
# def read_root():
#     return {"Hello": "World!"}

# Flow
# 1. Accept an image
# 2. extract the gps data for that image
#   F: -> placeholder error for now

# def main() -> None:
#     # lat: 41.968644
#     # long: -87.649874
#     # with open("response.json", "w+") as f:
#         # json.dump(response.json(), f, indent=2)
#     db = SqliteStationRepository("db.sqlite")
#
#
#     client = Anthropic()
#     img64 = _image_to_base64(GAS_IMAGE)
#     response = get_station_details(img64, client)
#     print(response.parsed_output)
#
#     # extract gps data here
#     data = gpsphoto.getGPSData(IMAGE_NAME)
#     print(data)
#
#     places = search_nearby(data["Latitude"], data["Longitude"])
#     print(json.dumps(places))
#     # places = search_nearby(
#     # print(json.dumps(response))
#     # print(response.parsed_output)
#
#     print("Done!")





