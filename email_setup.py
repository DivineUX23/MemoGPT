from typing import List

from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse
from uuid import uuid4


from decouple import config
import jwt

from model.users_model import User

from dotenv import load_dotenv
load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME = config("MAIL_USERNAME"),
    MAIL_PASSWORD=config("MAIL_PASSWORD"),
    MAIL_FROM=config("MAIL_USERNAME"),
    MAIL_PORT= 587,
    MAIL_SERVER= "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
)

def template(verification_token):
    email= f"""
        <!DOCTYPE html>
        <html>
            <head>
            </head>
            <body>
                <div style = "display: flex; align-items: center; justify-content: center, flex-direction: column">
                
                    <h3>Account Verification</h3>
                    <br>

                    <p>Welcome to the future, please click on the button below to verify your account and contiune </p>

                    <a style = "margin-top: 1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem; test-decoration: none; background: #0275d8; color: White;"
                    href="http://localhost:8000/verify/{verification_token}">
                    Verify your email
                    </a>

                    <p>Please kindly ignore this email if you did not register. Thanks</p>

                </div>
            </body>
        </html>
        """
    return email