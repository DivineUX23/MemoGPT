from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from model.user_model import Audio, Summary
from database.db import get_db
import json
import requests
import time
from sqlalchemy import func
from decouple import config

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

#===========================
from services.tokenizer_services import tokenizer
from services.llama_services import reply

from schema.users_shema import user
import oauth


YOUR_API_TOKEN = config("AssemblyAI")

transcripted = []
Audio_video = None


#Create transcript:

def get_transcript(file, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    #try:

        base_url = "https://api.assemblyai.com/v2"

        headers={
            "Authorization": YOUR_API_TOKEN,
            "Content-Type": "application/json"
        }

        
        file_content = file.file.read()

        response = requests.post(base_url + "/upload",
                                headers=headers,
                                files={"file": (file.filename, file_content)})
            
        upload_url = response.json()["upload_url"]

        print(upload_url)
        transcript_endpoint = "https://api.assemblyai.com/v2/transcript"

        data = {
            "audio_url": upload_url,
            "speaker_labels": True
        }

        response = requests.post(transcript_endpoint, 
                                 json=data, headers=headers)
        
        transcript_id = response.json()['id']

        print(transcript_id)

        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

        while True:
            transcription_result = requests.get(polling_endpoint, headers=headers).json()
            print(transcript_id)

            if transcription_result['status'] == 'completed':
                #print(transcription_result['text'])
                        
                sentences_endpoint = f"https://api.assemblyai.com/v2/transcript/{response.json()['id']}/sentences"
                sentences_result = requests.get(sentences_endpoint, headers=headers).json()
                utterances = sentences_result["sentences"]
                extracted_data = []

                for utterance in utterances:
                    data = {
                        "start": utterance["start"],
                        "end": utterance["end"],
                        "speaker": utterance["speaker"],
                        "text": utterance["text"]
                    }
                    extracted_data.append(data)
                print(extracted_data)
                break

            elif transcription_result['status'] == 'error':

                raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

            else: time.sleep(3)  

    #finally:
    
        print(f"TRANSCRIPT_DATA: {extracted_data}") 

        transcripted.append(extracted_data)
        
        # Convert JSON to string if necessary
        extracted_data = json.dumps(extracted_data)
        print(f"THIS THE ONE IN LOOP{extracted_data}")


        if len(word_tokenize(extracted_data)) > 3000: #problem with passing 3000 length to llama but not chatgpt3.5-turbo

            #get the summary chuck by chuck:

            chunks = tokenizer(extracted_data)

            responses = []
            for chunk in chunks:

                print(f"TESTING UNSENT CHUNK = \n\n{chunk}\n\n\n")

                tittle, summary = reply(chunk, db)

                print(f"TOKEN LENT OF CHUNK = \n\n{len(word_tokenize(str(summary)))}\n\n\n")

                responses.append(summary)

            joined_response = ' '.join(responses)
            tittle, summary = reply(joined_response, db)

            print(f"final response bove 4000 = {summary}\n")

        else:
            tittle, summary = reply(extracted_data, db)
        
        audio_id = db.query(func.max(Audio.id)).scalar()
    
        user_id = current_user.id

        Summarized = Summary(
            User_id = user_id,
            Audio_id = audio_id,
            title = tittle,
            summary = summary
        )
        db.add(Summarized)
        db.commit()

        summary_data = {'Audio_id': Summarized.Audio_id,
                'title': Summarized.title,
                'summary': Summarized.summary}
        
        transcription_result = extracted_data

        return (transcription_result, summary_data)
