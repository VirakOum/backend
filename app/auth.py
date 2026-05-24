import hashlib
import hmac
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import AuthToken, User

_TOKEN_SCHEME = HTTPBearer(auto_error=False)
_HASH_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _HASH_ITERATIONS)
    return f"{_HASH_ITERATIONS}${urlsafe_b64encode(salt).decode()}${urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        iterations_text, salt_text, digest_text = password_hash.split("$", 2)
        iterations = int(iterations_text)
        salt = urlsafe_b64decode(salt_text.encode())
        expected_digest = urlsafe_b64decode(digest_text.encode())
    except (ValueError, TypeError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate_digest, expected_digest)


def issue_token(db: Session, user: User) -> str:
    token_value = secrets.token_urlsafe(32)
    auth_token = AuthToken(user_id=user.id, token=token_value)
    db.add(auth_token)
    db.commit()
    return token_value


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_TOKEN_SCHEME),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    auth_token = db.execute(
        select(AuthToken).where(AuthToken.token == credentials.credentials)
    ).scalar_one_or_none()
    if auth_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, auth_token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user
