from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends
from hashing import hash
from database.db import get_db
from model.users_model import User
from schema.users_shema import user
from hashing import hash


def sign_up(user: str, db: Session = Depends(get_db)):

    new_users = User(name = user.name, 
                            email = user.email,
                            password = hash.bcrypt(user.password))
    db.add(new_users)
    db.commit()
    db.refresh(new_users)
    return new_users


def update(id: int, user: str, db: Session = Depends(get_db)):

    updating = db.query(User).filter(id == User.id).first()

    if not updating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hate to say but {id} does not exist")
    
    updating.name = user.name
    updating.email = user.email
    db.commit()

    return "udated succefully"


def delete(id: int, db: Session = Depends(get_db)):
        
    deleting = db.query(User).filter(id == User.id)

    if not deleting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hate to say but {id} does not exist")
    deleting.delete(sychronize_session = False)
    db.commit()

    return "Your account is deleted succefully"