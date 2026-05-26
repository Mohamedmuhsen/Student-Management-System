from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentBase(BaseModel):
    name: str
    email: EmailStr
    department: str
    gpa: float

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    gpa: Optional[float] = None

class Student(StudentBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class StudentPartialUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    gpa: Optional[float] = None