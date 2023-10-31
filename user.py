from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends, APIRouter
from hashing import hash
from database.db import get_db
from model.users_model import User
from schema.users_shema import user
from schema.users_shema import show_user
from hashing import hash
import services.user_services

from schema.users_shema import user
import oauth

app = APIRouter(tags= ["User"])


@app.post("/sign_up")
async def sign_up(user: user, db: Session = Depends(get_db)):

    new_users = services.user_services.sign_up(user=user, db=db)

    return {'message': status.HTTP_201_CREATED, 'detail': show_user.from_orm(new_users)}



@app.put("/update_data")
async def update(user: show_user, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    updating = services.user_services.update(current_user=current_user, user=user, db=db)

    return {'message': status.HTTP_201_CREATED, 'detail': updating}


@app.delete("/delete_account")
async def update(db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    deleting = services.user_services.delete(current_user=current_user, db=db)

    return {'message': status.HTTP_201_CREATED, 'detail': deleting}