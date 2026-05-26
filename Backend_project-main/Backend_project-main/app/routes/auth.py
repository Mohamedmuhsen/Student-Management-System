from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.user import Token, UserCreate, UserResponse
from ..services.auth_service import authenticate_user, create_access_token, create_user
from ..logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    - **role**: `admin` or `student` (default: student)
    - If role is `student`, you may also pass a nested **student** object
    to create the student record in the same request.

    Returns the newly created user (no password in response).
    """
    # Duplicate check
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        logger.bind(event="register_failed", username=user.username).warning("Registration failed: duplicate")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    db_user = create_user(db, user)
    logger.bind(event="user_registered", user_id=db_user.id, role=db_user.role).info("User registered successfully")
    return db_user

@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate with **username** and **password** (form data).

    Returns a Bearer JWT token valid for
    `settings.access_token_expire_minutes` minutes.

    Use the token in the `Authorization: Bearer <token>` header for
    protected endpoints.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.bind(event="login_failed", username=form_data.username).warning("Login failed: invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    logger.bind(event="login_success", user_id=user.id, username=user.username).info("Login successful")
    return {"access_token": access_token, "token_type": "bearer"}
