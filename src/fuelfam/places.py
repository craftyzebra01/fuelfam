import requests

class GooglePlacesProvider:
    def __init__(self, api_key):
        self.api_key = api_key

    def search_nearby(
        self,
        lat,
        long,
        *,
        radius=500.0,
        max_results=10,
        included_types=None,
        field_mask="places.id,places.displayName,places.location",
    ):
        if included_types is None:
            included_types = ["gas_station"]
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }
        data = {
            "includedTypes": included_types,
            "maxResultCount": max_results,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": long,
                    },
                    "radius": radius,
                }
            },
        }
        url = "https://places.googleapis.com/v1/places:searchNearby"
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
