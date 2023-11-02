from sqlalchemy.orm import Session
from fastapi import status, Depends, APIRouter

from database.db import get_db

import services.history_services
from schema.users_shema import user

import oauth


app = APIRouter(tags = ["History"])


#Continue Conversation:

@app.put("/continue_chat/{Audio_id}")
async def continue_chat(Audio_id: int, input: str, db: Session= Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    llama2, response = services.history_services.continue_chat(Audio_id=Audio_id, input=input, db=db, current_user=current_user)

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": response}



#Delete conversation:

@app.delete("/delete_chat/{Audio_id}")
async def delete_chat(Audio_id: int, db: Session= Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    deleted_chat = services.history_services.delete_chat(Audio_id=Audio_id, db=db, current_user=current_user)

    return {'message': status.HTTP_200_OK, 'detail': deleted_chat}



#List of all chats

@app.get("/all_chats/")
async def all_chats(db:Session= Depends(get_db), current_user: user = Depends(oauth.get_current_user)):
    all_chat = services.history_services.all_chats(db=db, current_user=current_user)
    return [{'id': id, 'Title': title} for (id, title) in all_chat]
