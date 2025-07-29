from pydantic import BaseModel

class User(BaseModel):
    email: str
    passwd: str

class Guest(BaseModel):
    name: str
    lastname: str
    menu: str
    role: str
    email: str
    leader: str

class Group(BaseModel):
    email: str

class Error(BaseModel):
    email: str
    description: str

class EditGuest(BaseModel):
    id: str
    name: str
    lastname: str
    menu: str

class DeleteGuest(BaseModel):
    id: int