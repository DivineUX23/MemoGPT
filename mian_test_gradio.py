import gradio as gr
from fastapi import Response
from mian_test import conversation, upload_audio, conversations, all_chats
from database.db import SessionLocal
from werkzeug.datastructures import FileStorage


"""
from transformers import pipeline

import gradio as gr

asr = pipeline("automatic-speech-recognition", "facebook/wav2vec2-base-960h")
classifier = pipeline("text-classification")


def speech_to_text(speech):
    text = asr(speech)["text"]
    return text


def text_to_sentiment(text):
    return classifier(text)[0]["label"]


demo = gr.Blocks()

with demo:
    audio_file = gr.Audio(type="filepath")
    text = gr.Textbox()
    label = gr.Label()

    b1 = gr.Button("Recognize Speech")
    b2 = gr.Button("Classify Sentiment")

    b1.click(speech_to_text, inputs=audio_file, outputs=text)
    b2.click(text_to_sentiment, inputs=text, outputs=label)

demo.launch()
"""
 

#PUT THE UI in different pages JUst like this

#WRAPPER FOR AUDIO
async def wrapper_upload_audio(file_path):

    #with open(file_path, 'rb') as f:
        #audio_file = f.read()
        #audio_file = FileStorage(f)

    db = SessionLocal()

    try:
        result = await upload_audio(file_path, db)
        return result['Summary']
    
    finally:
        db.close()

#WRAPPER FOR CONVERSATION
def wrapper_conversation(input, history):

    db = SessionLocal()

    try:
        result = conversation(input, db)
        return result['llama2']
    
    finally:
        db.close()


def display_chats():
    db = SessionLocal()

    try:
        response = all_chats(db)

        #data = [{'id': id, 'Title': title} for (id, title) in response]
        
        # Convert the data to an HTML unordered list
        html_content  = '<ul>'
        for item in response:
            html_content += f"<li>ID: {item['id']}, Title: {item['Title']}</li>"
        html_content += '</ul>'

        
        html = f'<div style="max-height: 500px; overflow-y: auto;">{html_content}</div>'
        
        return html
    
    finally:
        db.close()




#Audio Infsce for uplosd, record and play
demo = gr.Blocks()

with demo:
    gr.Markdown("Flip text or image files using this demo.")
    
    with gr.Tab("Flip Text"):
            
        audio_file = gr.Audio(type="filepath")
        text = gr.Textbox(visible = True)

        b1 = gr.Button("upload audio")
        toggle_text = gr.Button("Collapse")

        b1.click(wrapper_upload_audio, inputs=audio_file, outputs=text,)
        toggle_text.click(lambda: not text.visible, inputs=[], outputs=text)
        #toggle_text.click(inputs=[], outputs=text)

        gr.ChatInterface(wrapper_conversation)


    with gr.Tab("Flip Text"):
        #gr.Interface(fn=all_chats, inputs="text", output="text")
        gr.Interface(fn=display_chats, inputs=None, outputs=gr.HTML())


demo.launch(share=True)


# Gradio chat interface for conversations endpoint
#iface = gr.ChatInterface(conversation)

"""
#@app.get("/gradio_demo")
async def gradio_demo():

    url = demo.launch()

    # Redirect to the Gradio interface URL
    return Response(status_code=307, headers={"Location": url})


#CONTINUE CONVERSATION
#Audio Infsce for uplosd, record and play
demo = gr.Blocks()

with demo:

    gr.ChatInterface(conversations(int))

demo.launch()



with demo:

    b1 = gr.Button("get all history")

    b1.click(all_chats)

demo.launch()
"""

