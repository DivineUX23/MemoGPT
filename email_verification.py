from fastapi import BackgroundTasks
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends, APIRouter
from database.db import get_db

from model.users_model import User

import asyncio


app = APIRouter(tags= ["Starup"])


@app.on_event("startup")
async def startup_event(background_tasks: BackgroundTasks):
    background_tasks.add_task(cleanup_unverified_users)

async def cleanup_unverified_users(db: Session = Depends(get_db)):
    while True:
        # Get the current time
        now = datetime.now()

        # Get all users whose email is not verified and who were created more than a day ago
        unverified_users = db.query(User).filter(User.is_verified == False, User.created_at < now - timedelta(days=1)).all()

        for user in unverified_users:
            # Delete the user
            db.delete(user)

        # Commit the changes to the database
        db.commit()

        # Sleep for a day
        await asyncio.sleep(60*60*24)