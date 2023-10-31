from sqlalchemy.orm import Session
from fastapi import UploadFile, File,status, Depends, APIRouter

from database.db import get_db

import services.audio_services
import oauth



app = APIRouter(tags = ["Audio"],
                dependencies=[Depends(oauth.get_current_user)])

#Recording audio:


@app.post("/audio/start")
async def start_recording():

    recording=services.audio_services.start_recording()
    
    return {'message': status.HTTP_201_CREATED, "Transcript": recording}



@app.get("/audio/data")
async def stop_recording(db: Session = Depends(get_db)):

    stoped_strecording=services.audio_services.stop_recording(db=db)


    return {'message': status.HTTP_201_CREATED, "Detail": stoped_strecording}




#uplaod an audio file:

@app.post("/audio")
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):

    transcription_result, summary_data = await services.audio_services.upload_audio(file=file, db=db)


    return {'message': status.HTTP_201_CREATED, "Transcript": transcription_result, "Summary": summary_data}



#Play audio:

@app.get("/audio")
async def play_audio(db: Session = Depends(get_db)):

    Watching_audio=services.audio_services.play_audio(db=db)


    return Watching_audio