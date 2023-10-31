from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends, APIRouter
from hashing import hash
from database.db import get_db
from model.users_model import User
from schema.users_shema import user
from schema.users_shema import show_user
from hashing import hash
import services.user_services

app = APIRouter(tags= ["User"])


@app.post("/sign_up")
async def sign_up(user: user, db: Session = Depends(get_db)):

    new_users = services.user_services.sign_up(user=user, db=db)

    return {'message': status.HTTP_201_CREATED, 'detail': show_user.from_orm(new_users)}