from sqlalchemy.orm import Session
from fastapi import FastAPI, status, Depends, APIRouter
from llamaapi import LlamaAPI
from database.db import get_db

from decouple import config

from services.llama_services import conversation


from schema.users_shema import user
import oauth

app = APIRouter(tags = ["Llama"])


llama = LlamaAPI(config('LlamaAPI'))




#Conversation Endpoint:

histories = {"message":[]}
@app.post("/response/")
async def conversationing(input: str, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    llama2, db_history = conversation(input=input, db=db, current_user=current_user)

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": db_history}

