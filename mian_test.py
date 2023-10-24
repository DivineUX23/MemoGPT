#TESTING CODE----NOT TO BE RAN

from typing import Union
from sqlalchemy.orm import Session
from fastapi import FastAPI, UploadFile, File, HTTPException,status, responses, exceptions, Depends
from model.user_model import Audio, History, Summary
import schema.transcript
#from schema import transcript
from llamaapi import LlamaAPI
from database.db import get_db
import json
from uuid import uuid4
#import assemblyai as aai
import os
#from starlette.requests import Request
import requests
import time
from sqlalchemy import func

import pyaudio
import wave
from decouple import config

# Replace 'Your_API_Token' with your actual API token
app = FastAPI()

llama = LlamaAPI(config('LlamaAPI'))
YOUR_API_TOKEN = config("AssemblyAI")

transcripted = []

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    
    number = db.query(func.max(Audio.id)).scalar()
    #text="We currently believe that the universe has been around for roughly 13.8 billion years. This estimation is based on a variety of data, including measurements of cosmic microwave background radiation left over from the Big Bang and observations of the rate at which galaxies are moving away from each other. Interestingly. To give a bit more color. While the matter and energy that make up the universe have been around for about 13.8 billion years, the universe itself as a concept may be much older or indeed timeless, depending on different interpretations of quantum gravity and string theories. And a little more info for the curious mind. Even though the universe is about 13.8 billion years old, we can see light from objects that are more than 13.8 billion light years away due to the constant expansion of the universe. Isn't that fascinating? In smile."
    #transcripted.append(text)

    return {"Message": number}


def record_audio(db: Session = Depends(get_db)):

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []

    try:
        while True:
            data = stream.read(1024)
            frames.append(data)
    except KeyboardInterrupt:
        pass

    stream.stop_stream()
    stream.close()
    audio.terminate()

    sound_file = wave.open('', 'wb')
    sound_file.setnchannels(1)
    sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    sound_file.setframerate(44100)
    sound_file.writeframes(b''+frames)
    sound_file.close()

    audio = Audio(

        audio = sound_file
    )

    db.add(audio)
    db.commit()



#@app.post("/summary")
def reply(audio: str, db: Session = Depends(get_db)):

    # Create the summary
    try:
        api_request_json = {
            "model": "llama-13b-chat",
            "messages": [
                {"role": "system", "content": f"Analyze the following transcript from an audio file and determine whether it's from a meeting or a podcast. Then, provide a straightforward summary of the content. Your response should only include the type of audio (meeting or podcast) and the summary, without any additional information. Here is the transcript: {audio}"},
            ]
        }
        
    except llama.exceptions.Error as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"llama-13b-chat failed: {str(e)}")    

    response = llama.run(api_request_json)
    
    print(json.dumps(response.json(), indent=2))

    response_data = response.json()
    summary = response_data['choices'][0]['message']['content']
    #print(content)
        
    #return {'message': status.HTTP_201_CREATED, "data": content}



    #Creating a titile:
    
    api_request_json = {
        "model": "llama-13b-chat",
        "messages": [
            {"role": "system", "content": f"Based on the following summary, generate a single-phrase title that accurately captures the main theme or subject. Ensure your response consists solely of the title, without any additional text or explanation. Here is the summary: {summary}"},
        ]
    }
    response = llama.run(api_request_json)
    
    print(json.dumps(response.json(), indent=2))

    response_data = response.json()
    tittle = response_data['choices'][0]['message']['content']
    
    audio_id = db.query(func.max(Audio.id)).scalar()

    Summarized = Summary(
        Audio_id = audio_id,
        title = tittle,
        summary = summary
    )
    db.add(Summarized)
    db.commit()

    return {'Audio_id': Summarized.Audio_id,
            'title': Summarized.title,
            'summary': Summarized.summary}




@app.post("/items/")
def read_item(file: UploadFile = File(...), db: Session = Depends(get_db)):

    allowed_extensions = {".mp3", ".wav"}
    file_extension = os.path.splitext(file.filename)[1]
    if file_extension.lower() not in allowed_extensions:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Invalid file format"})


    try:

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

        #FILE_URL = "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"


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
                print(transcription_result['text'])
                break

            elif transcription_result['status'] == 'error':

                raise RuntimeError(f"Transcription failed: {transcription_result['error']}")
                #raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Transcription failed: {str(transcript_result['error'])}") 

            else: time.sleep(3)  

        #save transcript to the database
        audio_transcript = Audio(
            #id = id.id,
            transcript = transcription_result['text']
        )

        db.add(audio_transcript)
        db.commit()
   

    finally:
   
        print(transcription_result['text']) 

        transcripted.append(transcription_result['text'])

        summary_data = reply(transcription_result['text'], db)

        return {'message': status.HTTP_201_CREATED, "Transcript": transcription_result['text'], "Summary": summary_data}





histories = {"message":[]}
@app.post("/response/")
def conversation(input: str, db: Session = Depends(get_db)):

    #histories = history
    audio = transcripted

    llama2, history = conversations(input, audio, histories, db)

    db_history = storing_history(history, db)

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": db_history}



def conversations(input: str, audio: str, history: str, db: Session = Depends(get_db)):
    while True:

        prompt=f"Based exclusively on the information within the transcript {audio}, provide an answer to the following question: {input}. Your response should be derived solely from the transcript."
        messages = f"Utilize the JSON object {history}, which contains your past interactions with me, to ensure continuity in the conversation while prioritizing responses to the current question posed in {prompt}."
        #history["message"].append({"User question": {input}})
        history["message"].append({"role": "user", "content": input})

        
        message = [
                    {"role": "system", "content": f"Deliver precise and concise responses without greetings or irrelevant details, ensuring that the answers are accurate and directly address the user's questions."},
                    {"role": "user", "content": messages},
                ]


        # API Request JSON Cell
        try:
            api_request_json = {
                "model": "llama-13b-chat",
                "messages": message
            }
            
        except llama.exceptions.Error as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"llama-13b-chat failed: {str(e)}")    

        # Make your request and handle the response
        response = llama.run(api_request_json)

        response_data = response.json()
        llama2 = response_data['choices'][0]['message']['content']

        print(llama2)

        history["message"].append({"Your answer": {llama2}})
        history["message"].append({"role": "assistant", "content": llama2})

        
        print(F"History: {history}")


        return (llama2, history)
        #return {'llama2': llama2, 'history': history}
        #db_history = storing_history(history, db)

        #return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": db_history}



def storing_history(history, db: Session = Depends(get_db)):
    
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    history_json = json.dumps(history, indent=2, cls=SetEncoder)


    number = db.query(func.max(Audio.id)).scalar()

    record = db.query(History).filter(History.Audio_id == number).first()

    if record is None:
        history_transcript = History(
            Audio_id = number,
            chat_response = history_json
        )
        db.add(history_transcript)
        db.commit()

    #chat_response = db.query(func.max(History.chat_response)).scalar()
    record.chat_response = history_json
    db.commit()
    print(f"BABAD THIS FROM THE DB: {record.chat_response}")

    return {'Audio_id': number,
            'Conversation': record.chat_response}    



@app.put("/continue_chat/{Audio_id}")
def continue_chat(Audio_id: int, input: str, db: Session= Depends(get_db)):

    record = db.query(History).filter(History.Audio_id == Audio_id).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"{Audio_id} does not exist" )
    
    Audio_id = db.query(Audio).filter(Audio.id == Audio_id).first()

    raw_history = json.loads(record.chat_response)

    llama2, history = conversations(input, Audio_id.transcript, raw_history, db)

    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    history_json = json.dumps(history, indent=2, cls=SetEncoder)

    record.chat_response = history_json
    db.commit()

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": record.chat_response}



@app.delete("/delete_chat/{Audio_id}")
def delete_chat(Audio_id: int, db: Session= Depends(get_db)):

    record = db.query(Audio).filter(Audio.id == Audio_id).first()
    #record = db.session.query(History, Summary).join(Audio, Audio.id == History.audio_id).filter(Audio.id == Audio_id).first()


    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"{record} not found")
    
    db.delete(record)
    db.commit()

    return {'message': status.HTTP_200_OK, 'detail': f'{Audio_id} deleted'}

