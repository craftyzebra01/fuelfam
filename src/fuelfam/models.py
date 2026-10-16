from pydantic import BaseModel


class StationMatch(BaseModel):
    id: str
    name: str
    distance: float
    score: float


class FuelPrice(BaseModel):
    grade: str
    price_per_gallon: float


class ParsedSign(BaseModel):
    station_name: str
    fuel_prices: list[FuelPrice]


class StationConfirmation(BaseModel):
    upload_id: str
    file_name: str
    parsed: ParsedSign
    matches: list[StationMatch]

# BACKEND MODELS
class Station(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float


class ExternalId(BaseModel):
    station_id: str
    source: str
    external_id: str


class PriceEntry(BaseModel):
    id: str
    station_id: str
    grade: str
    price_per_gallon: float


class UploadRequest(BaseModel):
    upload_id: str
    matches: list[StationMatch]
