from sqlalchemy.orm import Session
from fastapi import FastAPI, UploadFile, File, HTTPException,status, Depends
from fastapi.responses import StreamingResponse
from model.user_model import Audio, History, Summary
from database.db import get_db

from uuid import uuid4
import os
from io import BytesIO

from sqlalchemy import func
import threading
import pyaudio
import wave
from decouple import config

from pydub import AudioSegment
from typing import Union

from services.assemblyai_services import get_transcript
from services.history_services import Audio_numbering

from schema.users_shema import user
import oauth

from services.premium import check_audio_length


#Recording audio:

Audio_video = None


recording_thread = None
is_recording=None
frames = []

def record_audio(db: Session = Depends(get_db)):

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    
    while is_recording:
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()


def start_recording():
    global recording_thread, is_recording

    if is_recording:
        raise HTTPException(status_code=400, detail="Already recording")
    
    is_recording = True
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()
    
    return  "Recording..."


def stop_recording(db: Session, current_user: user = Depends(oauth.get_current_user)):
    global recording_thread, is_recording, frames
    global Audio_video
    try:
        if not is_recording:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not currently recording")
        
        is_recording = False
        recording_thread.join()

        random_uuid = uuid4()
        random_file_name = str(random_uuid).replace('-', '')

        file_extension = '.wav'  
        random_file_name_with_extension = random_file_name + file_extension

        with wave.open(random_file_name_with_extension, 'wb') as sound_file:
            sound_file.setnchannels(1)
            sound_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            sound_file.setframerate(44100)
            sound_file.writeframes(b''.join(frames))
            sound_file.close()
    
        with open(random_file_name_with_extension, 'rb') as f:
            audio_data = f.read()

        file = UploadFile(
            file=BytesIO(audio_data),
            filename=random_file_name_with_extension
        )
        
        transcription_result, summary_data = check_audio_length(random_file_name_with_extension, file, db, current_user)
        
        #Debugger:
        print(f"TRANSCRIPT: {transcription_result}") 
        print(f"SUMMARY: {summary_data}") 

        user_id = current_user.id

        audio = Audio(
            User_id = user_id,
            data=audio_data,
            transcript = transcription_result
            )

        db.add(audio)
        db.commit()

        frames.clear()

        number = db.query(func.max(Audio.id)).scalar()

        Audio_video = number

        os.remove(random_file_name_with_extension)
    
    finally:
        frames.clear()


    return transcription_result, summary_data




#uplaod an audio file:
#async def upload_audio(file: Union[UploadFile, str] = File(...), db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):
async def upload_audio(file: Union[UploadFile, str] = File(...), db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

#async def upload_audio( db: Session, file: UploadFile = File(...), current_user: user = Depends(oauth.get_current_user)):

    global Audio_video

    allowed_extensions = {".mp3", ".wav"}

    # Check if the input is a string (URL) or a file
    if isinstance(file, str):
        print(f"THIS IS IT------{file}")

        audio = AudioSegment.from_wav(file) 

        if not os.path.exists("tmp"):
            os.mkdir("tmp")

        output_file_path = "tmp/mp3_file.mp3"

        audio.export(output_file_path, format="mp3")

        print(f"THIS------------{audio}")
        
        temp_file_path = output_file_path
        #file_extension = os.path.splitext(file)[1]
    
    else:
        
        # It's a file, process as before

        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() not in allowed_extensions:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Invalid file format"})
        
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
    
        temp_file_path = f"tmp/{file.filename}"

        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
        
    with open(temp_file_path, "rb") as f:
        audio_data = f.read()

    file = UploadFile(
        file=BytesIO(audio_data),
        filename=temp_file_path
    )

    transcription_result, summary_data = check_audio_length(temp_file_path, file, db, current_user)

    user_id = current_user.id

    audio = Audio(
            User_id = user_id,
            data=audio_data,
            transcript = transcription_result
            )
    
    db.add(audio)
    db.commit()

    number = db.query(func.max(Audio.id)).scalar()

    Audio_video = number

    #Debugger:
    print(f"---AUDIO_CHECKING{Audio_video}---")
    
    os.remove(temp_file_path)

    return transcription_result, summary_data



#Play audio:

def play_audio(db: Session):

    global Audio_video

    if Audio_video is None:
        
        Audio_video = Audio_numbering()
        
        print(f"AUDIO_TEST_RESPONSE{Audio_video}")

        Audio_no = db.query(Audio).filter(Audio.id == Audio_video).first()
        number=Audio_no.data
        audio_data = BytesIO(number)

    else:    
        Audio_no = db.query(Audio).filter(Audio.id == Audio_video).first()
        number=Audio_no.data
        audio_data = BytesIO(number)

    #Debugger:
    print(f"AUDIO_RESPONSE{Audio_video}")

    #return StreamingResponse(audio_data, media_type="audio/wav")
    return audio_data


