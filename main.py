from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends

from database.db import get_db

#for testing
from model.user_model import Audio
from sqlalchemy import func
#===========================

from audio import app as audio
from llama import app as llama
from history import app as history
from user import app as user

app = FastAPI()

app.include_router(audio, tags=["Audio"])
app.include_router(llama, tags=["Llama"])
app.include_router(history, tags=["History"])
app.include_router(user, tags=["User"])


#Testing:
@app.get("/")
def read_root(db: Session = Depends(get_db)):
    
    Audio_no = db.query(func.max(Audio.id)).scalar()
    TEST = db.query(Audio).filter(Audio.transcript == Audio_no.transcript).first()
    print(TEST.transcript)

    return {"Message": "Debugger page"}