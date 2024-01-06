import gradio as gr
from fastapi import Response, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from starlette.responses import RedirectResponse

from database.db import SessionLocal
from services.llama_services import conversation
from services.audio_services import upload_audio
from services.llama_services import conversations
from services.history_services import all_chats
from services.history_services import continue_chat
from services.history_services import delete_chat

from user import sign_up
from user_login import login
from paystack import pay

from services.user_services import delete
from services.user_services import update


#remaining sign_up, sign_in, pay
from schema.users_shema import user, premium
from schema.users_shema import show_user
import json

import oauth

from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType


from schema.users_shema import user
import oauth



current_user = None


#WRAPPER FOR SIGN_UP
async def wrapper_sign_up(name, email, password):

    background_tasks = BackgroundTasks()

    db = SessionLocal()

    try:
        new_users = user(name=name, email=email, password=password)
        await sign_up(new_users, background_tasks, db)

        return "Congratulations!! Your account has been created. Verification email sent."

    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()




#WRAPPER FOR AUDIO
async def wrapper_user_login(email, password):

    global current_user


    request = OAuth2PasswordRequestForm

    db = SessionLocal()

    try:
        new_users = request(password=password, username=email)


        token = await login(new_users, db)

        print(type(token['access_token']))

        print(token['access_token'])

        actual_token = token['access_token']
        
        print(actual_token)

        current_user = actual_token

        return "You've signed in sucessfully"
    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()




#WRAPPER FOR UPDATE
async def wrapper_update(name, email):


    global current_user


    print(f"This is the current user = {current_user}")

    db = SessionLocal()

    try:
        new_data = show_user(name=name, email=email)

        user = oauth.get_current_user(current_user, db)


        result = update(new_data, db, user)

        return result

    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()



#WRAPPER FOR DELETE
async def wrapper_delete():


    global current_user


    print(f"This is the current user = {current_user}")

    db = SessionLocal()

    try:

        user = oauth.get_current_user(current_user, db)


        result = delete(db=db, current_user=user)

        return result
    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()


 

#PUT THE UI in different pages JUst like this


n = None

def continue_conversation(number): 

    global n

    n = number
    
    return n


#WRAPPER FOR AUDIO
async def wrapper_payment(request:gr.Request, amount):

    global current_user

    print(f"requesting---------{request}")

    
    if amount == 6500:

        premiums = premium.MONTHLY
    else:
        premiums = premium.YEARLY
    

    print(f"This si right{premiums}")
    print(f"This si right{type(premiums)}")

    print(f"This is the current user = {current_user}")

    db = SessionLocal()

    try:

        user = oauth.get_current_user(current_user, db)


        result = await pay(request=request, amount=premiums, db=db, current_user=user)

        print(result)

        return result
    
    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()




#WRAPPER FOR AUDIO
async def wrapper_upload_audio(file_path):


    global current_user

    global n

    n = None


    print(f"This is the current user = {current_user}")

    db = SessionLocal()

    try:

        user = oauth.get_current_user(current_user, db)


        transcription_result, summary_data = await upload_audio(file_path, db, user)
    

        title = summary_data["title"]
        summary = summary_data["summary"]

        # Convert the data to an HTML unordered list
        html_content  = '<ul>'
        html_content += f"<li><h2>{title}</h2><br><br><strong>{summary}</strong></li>"
        html_content += '</ul>'

        html = f'<div style="max-height: 500px; overflow-y: auto;">{html_content}</div>'

        

        print(html)
        return html
    
    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()



#WRAPPER FOR CONVERSATION
def wrapper_conversation(input, history):

    global n


    db = SessionLocal()

    try:

        user = oauth.get_current_user(current_user, db)


        if n is not None:
            print(f"Done{n}")

            llama2, response = continue_chat(Audio_id=n, input=input, db=db, current_user=user)
                        
            return llama2

        else:

            llama2, db_history = conversation(input, db, user)
            return llama2

    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()


def display_chats():
    db = SessionLocal()

    try:

        user = oauth.get_current_user(current_user, db)

        response = all_chats(db, user)
        
        # Convert the data to an HTML unordered list
        html_content  = '<ul>'
        for item in response:
            audio_id, title = item
            html_content += f"<li>ID: {audio_id}, Title: {title}</li>"
        html_content += '</ul>'

        
        html = f'<div style="max-height: 500px; overflow-y: auto;">{html_content}</div>'
        
        print(html)

        return html
    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    
    finally:
        db.close()




def wrapper_delete_chat(input):


    db = SessionLocal()

    try:

        user = oauth.get_current_user(current_user, db)


        result = delete_chat(input, db, user)
        return result
    
    except HTTPException as e:
        print(f"An error occurred: {e.detail}")
        return f"An error occurred: {e.detail}"
    
    finally:
        db.close()





#GRADIO UI:
        
demo = gr.Blocks()

with demo:
    gr.Markdown("PROJECT DEMO.")



    #login
    with gr.Tab("LOGIN PAGE"):
        inputs = [
            gr.Textbox(label="email"),
            gr.Textbox(label="password", type="password")
            ]
        output = gr.Markdown("")

        b1 = gr.Button("input number")

        b1.click(wrapper_user_login, inputs=inputs, outputs=output)


    #signup
    with gr.Tab("SIGNUP PAGE"):
        inputs = [
            gr.Textbox(label="name"),
            gr.Textbox(label="email"),
            gr.Textbox(label="password", type="password")
            ]
        output = gr.Markdown("")

        b1 = gr.Button("input number")

        b1.click(wrapper_sign_up, inputs=inputs, outputs=output)
        


    #chat and audio
    with gr.Tab("UPLOAD AUDIO AND CHAT"):
        
        #audio record/upload
        audio_file = gr.Audio(type="filepath")
        text = gr.HTML(visible = True)

        b1 = gr.Button("upload audio")
        toggle_text = gr.Button("Collapse")

        b1.click(wrapper_upload_audio, inputs=audio_file, outputs=text,)
        toggle_text.click(lambda: not text.visible, inputs=[], outputs=text)

        #chat
        gr.ChatInterface(wrapper_conversation)


    with gr.Tab("OPTIONS"):

        #all chats
        gr.Interface(fn=display_chats, inputs=None, outputs=gr.HTML(label="View chat history"))

        #continue chat
        audio_file = gr.Textbox(label="continue which chat?")

        output = gr.Markdown("")

        b1 = gr.Button("input number")

        b1.click(continue_conversation, inputs=audio_file, outputs=output)


        #Deleting UI
        audio_file = gr.Textbox(label="Delete which chat?")
        
        text = gr.Markdown("")

        b2 = gr.Button("input number")

        b2.click(wrapper_delete_chat, inputs=audio_file, outputs=text)


        
    
    with gr.Tab("SETTINGS"):

        #payments:
        inputs=gr.Radio(label="Choose plan and enjoy", choices=[66000, 6500])

        redirect_button = gr.Button("thank you!")

        link = gr.Markdown("click the url when is shows up to make payment")

        redirect_button.click(wrapper_payment, inputs=inputs, outputs=link)


        #update user
        inputs = [
            gr.Textbox(label="name"),
            gr.Textbox(label="email"),
            ]
        output = gr.Markdown("")

        b2 = gr.Button("update")

        b2.click(wrapper_update, inputs=inputs, outputs=output)


        #Deleting User
    
        text = gr.Markdown("Parmanently delete your account?")
    
        b3 = gr.Button("Delete your account")

        b3.click(wrapper_delete, inputs=None, outputs=text)




demo.launch(share=True)

