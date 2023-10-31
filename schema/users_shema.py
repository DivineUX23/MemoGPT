from pydantic import BaseModel

class user(BaseModel):
    #id: int
    name: str
    email: str
    password: str

class show_user(BaseModel):
    name: str
    email: str
    
    class Config:
        from_attributes = True

class login(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None