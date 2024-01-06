from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends, APIRouter
from hashing import hash
from database.db import get_db
from model.users_model import User
from schema.users_shema import user
from schema.users_shema import show_user
from hashing import hash
import services.user_services
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType


from schema.users_shema import user
import oauth

from email_setup import conf, template
from model.users_model import User
from hashing import hash


app = APIRouter(tags= ["User"])


@app.post("/sign_up")
async def sign_up(user: user, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    new_users = services.user_services.sign_up(user=user, db=db)

    verification_token = str(uuid4())
    
    new_users.verification_token = verification_token
    db.commit()

    sent_email = template(verification_token)

    print(sent_email)

    message = MessageSchema(
        subject="AI from MeetingAI",
        recipients= [new_users.email], 
        body=sent_email,
        subtype= "html"
    )

    fm = FastMail(conf)

    #either use background_task or await depends on the scale of project:
    #corrently using await because of gradio interface:

    #background_tasks.add_task(fm.send_message, message)
    
    await fm.send_message(message)

    return {'message': "User created successfully. Verification email sent.", 'detail': show_user.from_orm(new_users)}



# Verify route
@app.get("/verify/{token}")
async def verify(token: str, db: Session = Depends(get_db)):

   user = db.query(User).filter(User.verification_token == token).first()
   
   if user:
      user.is_verified = True 
      db.commit()
   else:
      return {"error": "Invalid token"}
   
   return {"message": "Email verified successfully!"}




@app.put("/update_data")
async def update(user: show_user, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    updating = services.user_services.update(current_user=current_user, user=user, db=db)

    return {'message': status.HTTP_201_CREATED, 'detail': updating}


@app.delete("/delete_account")
async def update(db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    deleting = services.user_services.delete(current_user=current_user, db=db)

    return {'message': status.HTTP_201_CREATED, 'detail': deleting}