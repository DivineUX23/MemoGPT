from sqlalchemy.orm import Session
from fastapi import FastAPI, UploadFile, File, HTTPException,status, Depends
from llamaapi import LlamaAPI
from database.db import get_db
import json
from decouple import config

import nltk
from nltk.tokenize import word_tokenize
from services.tokenizer_services import tokenizer

from services.storage_services import storing_history


from schema.users_shema import user
import oauth

llama = LlamaAPI(config('LlamaAPI'))

nltk.download('punkt')

transcripted = []
Audio_video = None




#Generate summary and title:

def reply(audio: str, db: Session = Depends(get_db)):
    global transcripted

    transcripted = audio

    # Create the summary
    try:
        api_request_json = {
            "model": "llama-70b-chat",
            "messages": [
            {"role": "system", "content": f"""System: Based solely on this transcript: {audio} which contains sentence timestamps, speakers, and text, do the following:\
            - Provide a short summary of the key points. Include timestamps in the summary to reference where details are derived from the transcript. Ensure the summary directly addresses the core topics discussed in the transcript.\
            - Provide a single-phrase or single-word title that accurately captures the main theme or subject of the transcript.\

            User: Provide your answer in JSON format with the following keys: title, summary.\

            System: If the transcript is empty then simply write "No transcript provided."\

            Example 1:
            Transcript: "Hi, this is John from XYZ company. I'm calling to follow up on your order of 100 widgets. We have shipped your order today and you should receive it by next week. Please let me know if you have any questions or concerns."\
            "title": "Order Confirmation", \n\n\
            "summary": "John from XYZ company called to follow up on an order of 100 widgets. (0-10)\n The order was shipped today and expected to arrive by next week. (11-19)"\
            """}
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





#Conversation Endpoint:

histories = {"message":[]}
def conversation(input: str, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):
    global histories, transcripted

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

    db_history = storing_history(history, db, current_user)

    return llama2, db_history



def conversations(input: str, audio: str, messages: str, db: Session = Depends(get_db)):

    prompt=f"""Based exclusively on the information within the transcript of an audio file delimited by triple backticks below, which contains sentence timestamps, speakers, and text, PROVIDE AN ANSWER TO THIS QUESTION: {input}. Your response should be derived solely from the transcript. Include timestamps in the answer to reference where details are sourced from the Transcript.

    Transcript: ```{audio}```"""

    messaging = f"Utilize this JSON object :{messages}, which contains your past interactions with me, to ensure continuity in the conversation while prioritizing responses to the current question delimited by the tripple hash ###{prompt}###."

    messages["message"].append({"role": "user", "content": input})


    message = [
                {"role": "system", "content": f"Deliver precise and concise responses without greetings or irrelevant details, ensuring that the answers are accurate and directly address the user's questions."},
                {"role": "user", "content": messaging},
            ]



    if input:
        api_request_json = {
            "model": "llama-70b-chat",
            "messages": message,
            "temperature": 0.3

        }
            
        response = llama.run(api_request_json)

        response_data = response.json()
        llama2 = response_data['choices'][0]['message']['content']
        messages["message"].append({"role": "assistant", "content": llama2})

        return llama2, messages
    
    else:

        return {'message': status.HTTP_204_NO_CONTENT, "Detail": "Shouldn't be empty"}

