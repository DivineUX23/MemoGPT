#TEST CODE FOR THE MAIN CODE IN THE MAIN.PY FILE


import gradio as gr
import uvicorn
from sqlalchemy.orm import Session
from fastapi import FastAPI, UploadFile, File, HTTPException,status, Depends, Response
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
import mysql.connector
from typing import Union

from functools import partial

#testing purposes only
from sqlalchemy import create_engine
from database.db import SessionLocal

from pydub import AudioSegment

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from openai import OpenAI


app = FastAPI()

llama = LlamaAPI(config('LlamaAPI'))

M_API = config('MistrailAPI')


YOUR_API_TOKEN = config("AssemblyAI")

nltk.download('punkt')

transcripted = []
Audio_video = None


#Testing:
histories = {"message":[]}
@app.get("/")
def read_root(input: str, db: Session = Depends(get_db)):
    
    #number = db.query(func.max(Audio.id)).scalar()
    
    #Debuggers:
    audio="We currently believe that the universe has been around for roughly 13.8 billion years. This estimation is based on a variety of data, including measurements of cosmic microwave background radiation left over from the Big Bang and observations of the rate at which galaxies are moving away from each other. Interestingly. To give a bit more color. While the matter and energy that make up the universe have been around for about 13.8 billion years, the universe itself as a concept may be much older or indeed timeless, depending on different interpretations of quantum gravity and string theories. And a little more info for the curious mind. Even though the universe is about 13.8 billion years old, we can see light from objects that are more than 13.8 billion light years away due to the constant expansion of the universe. Isn't that fascinating? In smile."
    
    #llama2, history = conversations(input, audio, histories, db)

    #db_history = storing_history(history, db)

    #return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": db_history}
    #transcripted.append(text)
    #Audio_no = db.query(Audio).filter(Audio.id == number).first()
    #TEST = db.query(Audio).filter(Audio.transcript == Audio_no.transcript).first()
    #print(TEST.transcript)

    return {"Message": "Debugger page"}



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



#Generate summary and title:

def reply(audio: str, db: Session = Depends(get_db)):

        # gets API Key from environment variable OPENAI_API_KEY
        client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=M_API,
        )

        completion = client.chat.completions.create(
            extra_headers={
                #"HTTP-Referer": $YOUR_SITE_URL, # Optional, for including your app on openrouter.ai rankings.
                #"X-Title": $YOUR_APP_NAME, # Optional. Shows in rankings on openrouter.ai.
            },
                
            model="mistralai/mistral-7b-instruct",
            messages=[
                    {"role": "system", "content": f"""System: Based solely on this transcript: {audio} which contains sentence timestamps, speakers, and text, do the following:\
                    - Provide a short summary of the key points. Include timestamps in the summary to reference where details are derived from the transcript. Ensure the summary directly addresses the core topics discussed in the transcript.\
                    - Provide a single-phrase or single-word title that accurately captures the main theme or subject of the transcript.\

                    User: Provide your answer in JSON format with the following keys: title, summary.\

                    System: If the transcript is empty then simply write "No transcript provided."\

                    Example 1:
                    Transcript: "Hi, this is John from XYZ company. I'm calling to follow up on your order of 100 widgets. We have shipped your order today and you should receive it by next week. Please let me know if you have any questions or concerns."\
                    "title": "Order Confirmation", \n\n\
                    "summary": "John from XYZ company called to follow up on an order of 100 widgets. (0-10)\n The order was shipped today and expected to arrive by next week. (11-19)"\
                    """},
            ],

            #temperature: 0,

        )

        response = completion.choices[0].message.content
        responsing = completion


        print(response)
        print(responsing)

        #lines = response

        content = json.loads(response)

        title = content["title"]
        summary = content["summary"]

        print(f"Title: {title}")
        print(f"Summary: {summary}")

        return (title, summary)



"""
        Create the summary
        try:
            api_request_json = {
                "model": "llama-13b-chat",
                "messages": [
                {"role": "system", "content": f""System: Based solely on this transcript: {audio} which contains sentence timestamps, speakers, and text, do the following:\
                - Provide a short summary of the key points. Include timestamps in the summary to reference where details are derived from the transcript. Ensure the summary directly addresses the core topics discussed in the transcript.\
                - Provide a single-phrase or single-word title that accurately captures the main theme or subject of the transcript.\

                User: Provide your answer in JSON format with the following keys: title, summary.\

                System: If the transcript is empty then simply write "No transcript provided."\

                Example 1:
                Transcript: "Hi, this is John from XYZ company. I'm calling to follow up on your order of 100 widgets. We have shipped your order today and you should receive it by next week. Please let me know if you have any questions or concerns."\
                "title": "Order Confirmation", \n\n\
                "summary": "John from XYZ company called to follow up on an order of 100 widgets. (0-10)\n The order was shipped today and expected to arrive by next week. (11-19)"\
                ""}
                ],

                "temperature": 0,
            }
            
        except llama.exceptions.Error as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"llama-13b-chat failed: {str(e)}")    

        response = llama.run(api_request_json)
        
        print(json.dumps(response.json(), indent=2))
            
        response_data = response.json()

        content = response_data["choices"][0]["message"]["content"]

        lines = content.split("\n\n")

        title_line = next((line for line in lines if line.lower().startswith("title:")), None)
        summary_line = next((line for line in lines if line.lower().startswith("summary:")), None)

        # Extract the title and summary from these lines
        title = title_line.split(":")[1].strip() if title_line else None
        summary = summary_line.split(":")[1].strip() if summary_line else None

        print(f"Title: {title}")
        print(f"Summary: {summary}")

        return (title, summary)
"""
#uplaod an audio file:

@app.post("/upload_audio/")
async def upload_audio(file: Union[UploadFile, str] = File(...), db: Session = Depends(get_db)):

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

    finally:
   
        print(f"TRANSCRIPT_DATA: {extracted_data}") 

        transcripted.append(extracted_data)
        
        # Convert JSON to string if necessary
        extracted_data = json.dumps(extracted_data)
        print(f"THIS THE ONE IN LOOP{extracted_data}")


        if len(word_tokenize(extracted_data)) > 3000:

            #get the summary chuck by chuck:

            chunks = tokenizer(extracted_data)

            responses = []
            for chunk in chunks:
                tittle, summary = reply(chunk, db)

                print(f"TOKEN LENT OF CHUNK = \n\n{len(word_tokenize(str(summary)))}\n\n\n")

                responses.append(summary)

            joined_response = ' '.join(responses)
            tittle, summary = reply(joined_response, db)

            print(f"final response bove 4000 = {summary}\n")

        else:
            tittle, summary = reply(extracted_data, db)
        
        audio_id = db.query(func.max(Audio.id)).scalar()

        Summarized = Summary(
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



#Tokenizing Transcript to fit LLama
def tokenizer(extracted_data: str):

    if isinstance(extracted_data, dict):
        extracted_data = json.dumps(extracted_data)

    print("Token count more = ", len(word_tokenize(extracted_data)))

    chunk_size = 3000
    chucks = []
    sentences = sent_tokenize(extracted_data)
    current_chunk = ""

    for sentence in sentences:
        tokens = nltk.word_tokenize(sentence)

        if len(current_chunk.split()) + len(tokens) <= chunk_size:
            current_chunk += "" + sentence

        else:
            chucks.append(current_chunk.strip())
            current_chunk = sentence

        print(f"TOKEN LENT OF unsent CHUNK = \n\n{len(word_tokenize(str(current_chunk.strip())))}\n\n\n")

    if current_chunk:
        chucks.append(current_chunk.strip())
       
    print(chucks)
    return chucks


#Conversation Endpoint:

histories = {"message":[]}
@app.post("/response/")
def conversation(input: str, db: Session = Depends(get_db)):
    global histories

    audio = transcripted
    print(audio)
    print(f"Transcript{transcripted}")

    extracted_data = json.dumps(audio)
    print(f"THIS THE ONE IN LOOP{extracted_data}")

    #print(f"THIS THE ONE noooot IN LOOP{extracted_data}")

    if len(word_tokenize(extracted_data)) > 3000:

        #get the summary chuck by chuck:

        chunks = tokenizer(extracted_data)

        responses = []
        for chunk in chunks:
            #global histories
            histories = {"message":[]}

            llama2, historing = conversations(input, chunk, histories, db)
         
            print(f"deleted history = \n{histories}\n")

            print(f"TOKEN LENT OF CHUNK = \n\n{len(word_tokenize(str(llama2)))}\n\n\n")

            responses.append(llama2)

        print(f"deleted history 2nd = \n\n{histories}\n")
        
        joined_response = ' '.join(responses)
        llama2, history = conversations(input, joined_response, histories, db)
        print(f"final response bove 4000 = \n\n{llama2}\n")

    else:
        llama2, history = conversations(input, audio, histories, db)

    db_history = storing_history(history, db)

    return {'message': status.HTTP_200_OK, 'llama2': llama2, "Conversation": db_history}


def conversations(input: str, audio: str, messages: str, db: Session = Depends(get_db)):

    prompt=f"""Based exclusively on the information within the transcript of an audio file delimited by triple backticks below, which contains sentence timestamps, speakers, and text, provide an answer to the question, provide an answer to the following question: {input}. Your response should be derived solely from the transcript. Include timestamps in the answer to reference where details are sourced from the Transcript.

    Transcript: ```{audio}```"""

    messaging = f"Utilize this JSON object :{messages}, which contains your past interactions with me, to ensure continuity in the conversation while prioritizing responses to the current question delimited by the tripple hash ###{prompt}###."

    messages["message"].append({"role": "user", "content": input})


    message = [
                {"role": "system", "content": f"Deliver precise and concise responses without greetings or irrelevant details, ensuring that the answers are accurate and directly address the user's questions."},
                {"role": "user", "content": messaging},
            ]



    if input:
        
        """
        api_request_json = {
            "model": "llama-13b-chat",
            "messages": message,
            "temperature": 0

        }
            
        response = llama.run(api_request_json)

        response_data = response.json()
        llama2 = response_data['choices'][0]['message']['content']
        messages["message"].append({"role": "assistant", "content": llama2})
        """


        # gets API Key from environment variable OPENAI_API_KEY
        client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=M_API,
        )

        completion = client.chat.completions.create(
            extra_headers={
                #"HTTP-Referer": $YOUR_SITE_URL, # Optional, for including your app on openrouter.ai rankings.
                #"X-Title": $YOUR_APP_NAME, # Optional. Shows in rankings on openrouter.ai.
            },
                
            model="mistralai/mistral-7b-instruct",
            messages=message,

            #temperature: 0,

        )

        mistral = completion.choices[0].message.content

        llama2 = mistral

        return llama2, messages
    
    else:

        return {'message': status.HTTP_204_NO_CONTENT, "Detail": "Shouldn't be empty"}



#Store conversation history:

def storing_history(history, db: Session = Depends(get_db)):
    
    class SetEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    history_json = json.dumps(history, indent=2, cls=SetEncoder)
    print(f"History--------------------: {history_json}")

    number = db.query(func.max(Audio.id)).scalar()

    record = db.query(History).filter(History.Audio_id == number).first()

    if record is None:
        history_transcript = History(
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




def wrapper_function(input, history):
    # manually create a new session
    db = SessionLocal()

    try:
        result = conversation(input, db)
        return result['llama2']
    
    finally:
        db.close()



iface = gr.ChatInterface(wrapper_function)


@app.get("/demo")
async def demo():

    url = iface.launch()

    # Redirect to the Gradio interface URL source venv/Scripts/activate. uvicorn mian_test:app --reload --port 6060
    return Response(status_code=307, headers={"Location": url})


if __name__ == "__main__":

    app.mount("/demo", gr.App(iface))

    uvicorn.run(app, host="localhost", port=6060)
