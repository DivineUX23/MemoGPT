from pydantic import BaseModel

class user(BaseModel):
    #id: int
    name: str
    email: str
    password: str

class show_user(BaseModel):
    name: str
    email: str