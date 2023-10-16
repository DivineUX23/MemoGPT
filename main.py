from sqlalchemy.orm import Session
from fastapi import FastAPI, UploadFile, File, HTTPException,status, Depends
from fastapi.responses import StreamingResponse
from model.user_model import Audio, History, Summary
from llamaapi import LlamaAPI
from database.db import get_db
import json
from uuid import uuid4
import os
from io import BytesIO
import requests
import time
from sqlalchemy import func
import threading
import pyaudio
import wave
from decouple import config


app = FastAPI()

llama = LlamaAPI(config('LlamaAPI'))
YOUR_API_TOKEN = config("AssemblyAI")

transcripted = []
Audio_video = None


#Testing:

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    
    number = db.query(func.max(Audio.id)).scalar()
    
    #Debuggers:
    #text="We currently believe that the universe has been around for roughly 13.8 billion years. This estimation is based on a variety of data, including measurements of cosmic microwave background radiation left over from the Big Bang and observations of the rate at which galaxies are moving away from each other. Interestingly. To give a bit more color. While the matter and energy that make up the universe have been around for about 13.8 billion years, the universe itself as a concept may be much older or indeed timeless, depending on different interpretations of quantum gravity and string theories. And a little more info for the curious mind. Even though the universe is about 13.8 billion years old, we can see light from objects that are more than 13.8 billion light years away due to the constant expansion of the universe. Isn't that fascinating? In smile."
    #transcripted.append(text)
    Audio_no = db.query(Audio).filter(Audio.id == number).first()
    TEST = db.query(Audio).filter(Audio.transcript == Audio_no.transcript).first()
    print(TEST.transcript)

    return {"Message": number, "TEST": TEST.transcript}



#Recording audio:

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


@app.post("/start_recording")
def start_recording():
    global recording_thread, is_recording

    if is_recording:
        raise HTTPException(status_code=400, detail="Already recording")
    
    is_recording = True
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()
    
    return {'message': status.HTTP_201_CREATED, "Detail": "Recording..."}


@app.get("/stop_recording")
def stop_recording(db: Session = Depends(get_db)):
    global recording_thread, is_recording, frames
    global Audio_video

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
        
    transcription_result, summary_data = get_transcript(file, db)
    
    #Debugger:
    print(f"TRANSCRIPT: {transcription_result}") 
    print(f"SUMMARY: {summary_data}") 

    audio = Audio(data=audio_data,
                  transcript = transcription_result)

    db.add(audio)
    db.commit()

    frames.clear()

    number = db.query(func.max(Audio.id)).scalar()

    Audio_video = number

    os.remove(random_file_name_with_extension)

    return {'message': status.HTTP_201_CREATED, "Transcript": transcription_result, "Summary": summary_data}



#Generate summary:

def reply(audio: str, db: Session = Depends(get_db)):

    # Create the summary
    try:
        api_request_json = {
            "model": "llama-13b-chat",
            "messages": [
                {"role": "system", "content": f"Based solely on the transcript {audio}, summarize the content in a straightforward and concise manner, focusing only on relevant details from the transcript. Do not include any additional information, greetings, or irrelevant specifics. Ensure the summary directly addresses the core topics discussed in the transcript."},
            ]
        }
        
    except llama.exceptions.Error as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"llama-13b-chat failed: {str(e)}")    

    response = llama.run(api_request_json)
    
    print(json.dumps(response.json(), indent=2))

    response_data = response.json()
    summary = response_data['choices'][0]['message']['content']

    #Creating a titile:    
    api_request_json = {
        "model": "llama-13b-chat",
        "messages": [
            {"role": "system", "content": f"Provide a single-phrase or single-word title that accurately captures the main theme or subject of the summary {summary}. Ensure the response consists only of the title, without any additional text or explanation."},
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



#uplaod an audio file:

@app.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):

    global Audio_video

    allowed_extensions = {".mp3", ".wav"}
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

    transcription_result, summary_data = get_transcript(file, db)

    audio = Audio(data=audio_data,
                transcript = transcription_result)
    db.add(audio)
    db.commit()

    number = db.query(func.max(Audio.id)).scalar()

    Audio_video = number

    #Debugger:
    print(f"---AUDIO_CHECKING{Audio_video}---")
    
    os.remove(temp_file_path)

    return {'message': status.HTTP_201_CREATED, "Transcript": transcription_result, "Summary": summary_data}



#Play audio:

@app.get("/play_audio")
def play_audio(db: Session = Depends(get_db)):

    global Audio_video

    Audio_no = db.query(Audio).filter(Audio.id == Audio_video).first()
    number=Audio_no.data
    audio_data = BytesIO(number)

    #Debugger:
    print(f"AUDIO_RESPONSE{Audio_video}")

    return StreamingResponse(audio_data, media_type="audio/wav")



#Create transcript:

def get_transcript(file, db: Session = Depends(get_db)):

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

            else: time.sleep(3)  

    finally:
   
        print(f"TRANSCRIPT_DATA: {transcription_result['text']}") 

        transcripted.append(transcription_result['text'])

        summary_data = reply(transcription_result['text'], db)

        transcription_result = transcription_result['text']
        
        return (transcription_result, summary_data)



#Conversation Endpoint:

histories = {"message":[]}
@app.post("/response/")
def conversation(input: str, db: Session = Depends(get_db)):

    audio = transcripted

    llama2, history = conversations(input, audio, histories, db)

    db_history = storing_history(history, db)

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": db_history}



#Conversation 

def conversations(input: str, audio: str, history: str, db: Session = Depends(get_db)):

    while True:

        prompt=f"Based exclusively on the information within the transcript {audio}, provide an answer to the following question: {input}. Your response should be derived solely from the transcript."
        messages = f"Utilize the JSON object {history}, which contains your past interactions with me, to ensure continuity in the conversation while prioritizing responses to the current question posed in {prompt}."
        history["message"].append({"User question": {input}})
        
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

        response = llama.run(api_request_json)

        response_data = response.json()
        llama2 = response_data['choices'][0]['message']['content']

        #Debugger:
        print(llama2)

        history["message"].append({"Your answer": {llama2}})
        
        #Debugger:
        print(F"History: {history}")

        return (llama2, history)



#Store conversation history:

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

    record.chat_response = history_json
    db.commit()
    
    #Debugger:
    print(f"BABAD THIS FROM THE DB: {record.chat_response}")

    return {'Audio_id': number,
            'Conversation': record.chat_response}    



#Continue Conversation:

@app.put("/continue_chat/{Audio_id}")
def continue_chat(Audio_id: int, input: str, db: Session= Depends(get_db)):

    global Audio_video

    record = db.query(History).filter(History.Audio_id == Audio_id).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= f"{Audio_id} does not exist" )
    
    Audio_no = db.query(Audio).filter(Audio.id == Audio_id).first()

    Audio_video = Audio_no.id

    raw_history = json.loads(record.chat_response)

    llama2, history = conversations(input, Audio_no.transcript, raw_history, db)

    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    history_json = json.dumps(history, indent=2, cls=SetEncoder)

    record.chat_response = history_json
    db.commit()

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": record.chat_response}



#Delete conversation:

@app.delete("/delete_chat/{Audio_id}")
def delete_chat(Audio_id: int, db: Session= Depends(get_db)):

    record = db.query(Audio).filter(Audio.id == Audio_id).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"{record} not found")
    
    db.delete(record)
    db.commit()

    return {'message': status.HTTP_200_OK, 'detail': f'{Audio_id} deleted'}



#List of all chats

@app.get("/all_chats/")
def all_chats(db:Session= Depends(get_db)):
    results = db.query(Summary.Audio_id, Summary.title).all()
    return [{'id': id, 'Title': title} for (id, title) in results]
