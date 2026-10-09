import os
import requests
import json
from fuelfam.imp import imp
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

IMAGE_NAME = "IMG_9253.jpeg"

def main() -> None:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.name"
    }
    data = {
        "includedTypes": ["gas_station"],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": 41.968644,
                    "longitude": -87.649874,
                },
                "radius": 500.0
            }
        }
    }
    url = "https://places.googleapis.com/v1/places:searchNearby"
    response = requests.post(url, json=data, headers=headers)
    print(response)
    print(response.headers)
    response.raise_for_status

    with open("response.json", "w+") as f:
        json.dump(response.json(), f, indent=2)
