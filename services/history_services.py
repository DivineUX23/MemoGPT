from sqlalchemy.orm import Session
from fastapi import HTTPException,status, Depends
from model.user_model import Audio, History, Summary
from llamaapi import LlamaAPI
from database.db import get_db
import json
from sqlalchemy import func

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

#===========================

from services.tokenizer_services import tokenizer
from services.llama_services import conversations


from schema.users_shema import user
import oauth


nltk.download('punkt')

transcripted = []
Audio_video = None


#Continue Conversation:

def continue_chat(Audio_id: int, input: str, db: Session= Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    global Audio_video

    record = db.query(History).filter(History.Audio_id == Audio_id, History.User_id == current_user.id).first()

    #record = db.query(Summary).filter(Summary.Audio_id == Audio_id, Summary.User_id == current_user.id).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"{Audio_id} does not exist" )
    
    Audio_no = db.query(Audio).filter(Audio.id == Audio_id).first()

    Audio_video = Audio_no.id

    raw_history = json.loads(record.chat_response)


    extracted_data = json.dumps(Audio_no.transcript)
    print(f"THIS THE ONE IN LOOP{extracted_data}")


    if len(word_tokenize(extracted_data)) > 3000:

        chunks = tokenizer(extracted_data)

        responses = []

        for chunk in chunks:
            histories = {"message":[]}

            llama2, history = conversations(input, chunk, histories, db)
            
            responses.append(llama2)

        #print(f"deleted history 2nd = \n\n{histories}\n")
        
        joined_response = ' '.join(responses)
        
        llama2, history = conversations(input, joined_response, raw_history, db)

        print(f"final response bove 4000 = \n\n{llama2}\n")

    else:
        llama2, history = conversations(input, Audio_no.transcript, raw_history, db)

    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    history_json = json.dumps(history, indent=2, cls=SetEncoder)

    record.chat_response = history_json
    db.commit()
    response = record.chat_response
    return llama2, response


#just send latest audio to 
def Audio_numbering():
    
    global Audio_video

    Audio_number = Audio_video
    print(f"AUDIO_TEST_RESPONSE_______________{Audio_video}")

    return Audio_number



#Delete conversation:

def delete_chat(Audio_id: int, db: Session= Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    record = db.query(History).filter(History.Audio_id == Audio_id, History.User_id == current_user.id).first()

    #record = db.query(Audio).filter(Audio.id == Audio_id).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"{record} not found")
    
    db.delete(record)
    db.commit()

    return f'{Audio_id} deleted'



#List of all chats

def all_chats(db:Session= Depends(get_db), current_user: user = Depends(oauth.get_current_user)):


    #results = db.query(Summary.Audio_id, Summary.title).all(current_user)
    results = db.query(Summary.Audio_id, Summary.title).filter(Summary.User_id == current_user.id).all()

    #results = db.query(current_user.Audio_id, current_user.title).all()

    return results