from sqlalchemy.orm import Session
from fastapi import Depends
from model.user_model import Audio, History, Summary
from llamaapi import LlamaAPI
from database.db import get_db
import json
from sqlalchemy import func

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

#===========================

from schema.users_shema import user
import oauth


nltk.download('punkt')

transcripted = []
Audio_video = None


#Store conversation history:

def storing_history(history, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):
    
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    history_json = json.dumps(history, indent=2, cls=SetEncoder)
    print(f"History--------------------: {history_json}")

    number = db.query(func.max(Audio.id)).scalar()

    record = db.query(History).filter(History.Audio_id == number).first()

    user_id = current_user.id

    if record is None:
        history_transcript = History(
            User_id = user_id,
            Audio_id = number,
            chat_response = history_json
        )
        db.add(history_transcript)
        db.commit()

    else:
        record.chat_response = history_json
        db.commit()
    
        #Debugger:
        print(f"BABAD THIS FROM THE DB: {record.chat_response}")

        return {'Audio_id': number,
                'Conversation': record.chat_response}    
