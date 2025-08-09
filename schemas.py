from pydantic import BaseModel
import string

class User(BaseModel):
    email: str
    passwd: str

class Guest(BaseModel):
    name: str
    lastname: str
    role: str
    email: str
    leader: str

class Group(BaseModel):
    email: str

class Error(BaseModel):
    name: str
    lastname: str
    email: str
    description: str

class EditGuest(BaseModel):
    id: str
    name: str
    lastname: str

class DeleteGuest(BaseModel):
    id: int

roles = ["leader", "companion"]
invalid_characters = tuple(string.punctuation + string.digits + "¨" + "´" + "`" + "¿")