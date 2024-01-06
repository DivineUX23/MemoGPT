from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends
from hashing import hash
from database.db import get_db
from model.users_model import User
from schema.users_shema import user
from hashing import hash

from schema.users_shema import user
import oauth


def sign_up(user: str, db: Session = Depends(get_db)):

    new_users = User(name = user.name, 
                            email = user.email,
                            password = hash.bcrypt(user.password))
    db.add(new_users)
    db.commit()
    db.refresh(new_users)
    return new_users


def update(user: str, db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):

    updating = db.query(User).filter(current_user.id == User.id).first()

    if not updating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hate to say but {id} does not exist")
    
    updating.name = user.name
    updating.email = user.email
    db.commit()

    return "updated succefully"


def delete(db: Session = Depends(get_db), current_user: user = Depends(oauth.get_current_user)):
        
    deleting = db.query(User).filter(current_user.id == User.id)

    if not deleting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hate to say but {id} does not exist")
    deleting.delete(synchronize_session = False)

    db.commit()

    return "Your account is deleted succefully"