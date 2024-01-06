from fastapi import FastAPI, Request, Form, Depends, APIRouter
from fastapi.responses import RedirectResponse
import requests
from model.users_model import User
from database.db import get_db
from sqlalchemy.orm import Session
from decouple import config


from schema.users_shema import user, premium
import oauth



from datetime import datetime, timedelta


app = APIRouter(tags= ["User"])



# Paystack API credentials 
SECRET_KEY = config("Paystack")

@app.post("/pay")
async def pay(request: Request, amount: premium, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    print(f"This si right{type(amount)}")
    
    print(f"This si right{amount}")


    user = db.query(User).filter(current_user.id == User.id).first()


    url = "https://api.paystack.co/transaction/initialize"

    payload = {
        "email": user.email,
        "amount": amount * 100
    }
    headers = {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json" 
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        auth_url = data["data"]["authorization_url"]

        reference = data["data"]["reference"]

        client = request.headers.get('accept')

        if 'application/json' in client:
            
            return {"status": "redirect success", "auth_url": auth_url} #suppose to be redirective: will implement with frontend

        else:
            #return RedirectResponse(auth_url)
            return auth_url

    else:
        # Handle error case
        return {"status": "Error", "message": response.text}



#TO be edited with actual serveo url (run "ssh -R 80:localhost:[port] serveo.net" to get it) for paystack webhook:
#https://56ad129e1c13c7697d551f019cd665db.serveo.net/payment/webhook_verification

@app.post("/payment/webhook_verification")
async def handle_webhook(payload: dict, db: Session = Depends(get_db)):

    if payload["event"] == "charge.success":

        reference = payload["data"]["reference"]

        # Verify transaction with reference
        url = f"https://api.paystack.co/transaction/verify/" + reference
        
        headers = {"Authorization": f"Bearer {SECRET_KEY}",
                "Content-Type": "application/json"}
    
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            
            amount = data["data"]["amount"]

            if amount == 66000 * 100:
                days = 365
            else:
                days = 30

            print(amount)

            print(data)

            # Check status
            if data["data"]["status"] == "success":

                email = data["data"]["customer"]["email"]

                #debuger
                print(f"Something wrong here though---------------------------------YEAHHH{email}")

                duration= update_user_subscription(db, datetime.utcnow(), days, email)

                return {"request": "Done", "message": duration}

            else:
                
                return {"request": "request", "message": "Transaction failed"}

        else:
            print("Something wrong here though")

            return {"request": "request", "message": response.text}
                




def update_user_subscription(db: Session, paid_start: datetime, paid_duration: int, email):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.paid_start = paid_start
        user.paid_duration = paid_duration
        db.commit()

    return f"You have premuim access for {paid_duration} days starting today."
