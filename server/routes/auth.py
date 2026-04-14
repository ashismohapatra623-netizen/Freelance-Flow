"""
Authentication routes — register, login, and current user info.
"""
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from models.user import User
from schemas.auth import AuthRegister, AuthLogin, AuthResponse, TokenResponse
from middleware.auth import create_access_token, get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Rate limiter for login endpoint
limiter = Limiter(key_func=get_remote_address)


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (cost factor 12)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    data: AuthRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    Validates: password min 8 chars, email format, username 3-50 chars.
    Returns user info (never password_hash).
    """
    # Check for duplicate username
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # Check for duplicate email
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    # Create user with hashed password
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        id=user.id,
        username=user.username,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    data: AuthLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return JWT token.
    Returns generic 'Invalid credentials' on failure (no hint about what's wrong).
    """
    # Find user by username
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Generate JWT
    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        user=AuthResponse(
            id=user.id,
            username=user.username,
            email=user.email,
        ),
    )


@router.get("/me", response_model=AuthResponse)
def get_me(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Return current authenticated user's info."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return AuthResponse(
        id=user.id,
        username=user.username,
        email=user.email,
    )
