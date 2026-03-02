# Task: T-A001 (prerequisite — auth endpoints, Phase II baseline)
# Spec: §11.1 (Auth Endpoints — unchanged)
# Plan: §2.1 (Auth Endpoints)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.app.database import get_session
from backend.app.dependencies.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str = Field(max_length=255)
    password: str = Field(min_length=6, max_length=128)


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(body: SignupRequest, session: Session = Depends(get_session)):
    existing = session.exec(
        select(User).where(
            (User.username == body.username) | (User.email == body.email)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse(id=user.id, username=user.username, email=user.email)


@router.post("/token", response_model=TokenResponse)
def login(body: TokenRequest, session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.username == body.username)
    ).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
    )
