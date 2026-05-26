from datetime import datetime, timedelta
from typing import Optional
 
from jose import jwt
import bcrypt
from sqlalchemy.orm import Session
 
from ..config import settings
from ..models.user import User
from ..schemas.user import UserCreate
 
# ── Password hashing ──────────────────────────────────────────────────────────
 
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
    )


def get_password_hash(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

 
# ── Token creation ────────────────────────────────────────────────────────────
 
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Encode a JWT token.
 
    Parameters
    ----------
    data : dict
        Payload to encode.  Must contain at least {"sub": username}.
    expires_delta : timedelta, optional
        Custom expiry.  Falls back to settings.access_token_expire_minutes.
    Returns
    -------
    str
        Signed JWT string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

# ── User helpers ──────────────────────────────────────────────────────────────

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Fetch user by username and verify the password.

    Returns the User ORM object on success, None on failure.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user(db: Session, user: UserCreate) -> User:
    """
    Persist a new user to the database.

    If the role is 'student' and a nested student payload is provided,
    the student record is also created and linked back to the user.
    """
    # Import here to avoid circular imports at module level
    from ..services.student_service import create_student

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # If registering as a student and student data was provided, create the record
    if user.role == "student" and user.student:
        student = create_student(db, user.student, db_user.id)
        db_user.student_id = student.id
        db.commit()
        db.refresh(db_user)

    return db_user
