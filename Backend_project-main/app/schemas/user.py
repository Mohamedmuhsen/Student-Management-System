from pydantic import BaseModel, EmailStr
from typing import Optional
import enum
from .student import StudentCreate

class Role(str, enum.Enum):
    admin = "admin"
    student = "student"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: Role = Role.student

class UserCreate(UserBase):
    password: str
    student: Optional[StudentCreate] = None



class UserLogin(BaseModel):
    username: str
    password: str
    

class UserResponse(UserBase):
    id: int
    student_id: Optional[int] = None

    class Config:
        from_attributes = True

User = UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None