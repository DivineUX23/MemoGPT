import librosa
from schema.users_shema import user
import oauth
from sqlalchemy.orm import Session
from fastapi import FastAPI, UploadFile, File, HTTPException,status, Depends
from model.user_model import Audio, History, Summary
from services.assemblyai_services import get_transcript
from model.users_model import User




def check_audio_length(temp_file_path, audio_file, db: Session, current_user: user = Depends(oauth.get_current_user)):
    
    #y, sr = librosa.load(audio_file)
    duration = librosa.get_duration(path=temp_file_path)

    print(duration)

    if duration > 300: # 300 seconds = 5 minutes

        if current_user.is_paid():
                            
            transcription_result, summary_data = get_transcript(audio_file, db, current_user)

            return transcription_result, summary_data

        else:
            #return "Apply for premium"
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Apply for premium to access unlimited")

    else:
    
        transcription_result, summary_data = get_transcript(audio_file, db, current_user)

        return transcription_result, summary_data
