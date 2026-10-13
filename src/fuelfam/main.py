from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
import uuid

app = FastAPI()

class StationMatch(BaseModel):
    id: str
    name: str
    distance: float

class StationConfirmation(BaseModel):
    upload_id: str
    file_name: str
    matches: list[StationMatch]

@app.post("/uploadStationInfo", response_model=StationConfirmation)
def upload_station_info(file: UploadFile):
    return StationConfirmation(
        upload_id=str(uuid.uuid4()), 
        file_name=file.filename,
        matches=[StationMatch(id="12345", name="bp", distance=100.0)])

@app.post("/uploadStationInfo/{upload_id}/confirm")
def confirm_station_infor(upload_id):
    return {"upload_id": upload_id, "status": "success"}

