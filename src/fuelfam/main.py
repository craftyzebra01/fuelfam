import os
import uuid

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile

from fuelfam.models import StationConfirmation
from fuelfam.places import GooglePlacesProvider
from fuelfam.scoring import MissingGpsError, ScoringProvider
from fuelfam.storage import InMemoryUploadRequestProvider
from fuelfam.vision import AnthropicComputerVisionProvider

load_dotenv()

places_provider = GooglePlacesProvider(os.getenv("GOOGLE_MAPS_API_KEY"))
vision_provider = AnthropicComputerVisionProvider(Anthropic())
scoring_provider = ScoringProvider(places_provider, vision_provider)
upload_requests = InMemoryUploadRequestProvider()

app = FastAPI()


@app.post("/uploadStationInfo", response_model=StationConfirmation)
def upload_station_info(file: UploadFile):
    image_bytes = file.file.read()
    media_type = file.content_type or "image/jpeg"
    try:
        parsed, matches = scoring_provider.score_image(
            image_bytes,
            filename=file.filename,
            media_type=media_type,
        )
    except MissingGpsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    upload_id = str(uuid.uuid4())
    upload_requests.create(upload_id, matches)
    return StationConfirmation(
        upload_id=upload_id,
        file_name=file.filename or "upload.jpg",
        parsed=parsed,
        matches=matches,
    )


@app.post("/uploadStationInfo/{upload_id}/confirm")
def confirm_station_info(upload_id):
    return {"upload_id": upload_id, "status": "success"}
