from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class AdminLogin(BaseModel):
    password: str

class TerminationSchema(BaseModel):
    user_id: str
    reason: str = Field(..., min_length=5)
    