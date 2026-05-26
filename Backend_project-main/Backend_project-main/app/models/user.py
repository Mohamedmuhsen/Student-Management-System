from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class Role(str,enum.Enum):
    admin = "admin"
    student = "student"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(Enum(Role), default=Role.student)
    student_id = Column(Integer, nullable=True)  # Link to student if role is student

    student = relationship("Student", back_populates="user", uselist=False)