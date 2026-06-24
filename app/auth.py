import hashlib
import hmac
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import AuthToken, TrustedDevice, User, phnom_penh_now

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


def _hash_device_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def register_trusted_device(
    db: Session,
    *,
    user: User,
    device_id: str,
    device_platform: str,
    device_name: str | None,
) -> str:
    device_secret = secrets.token_urlsafe(32)
    device_id_hash = _hash_device_value(device_id)
    trusted_device = db.execute(
        select(TrustedDevice).where(TrustedDevice.device_id_hash == device_id_hash)
    ).scalar_one_or_none()
    if trusted_device is None:
        trusted_device = TrustedDevice(
            user_id=user.id,
            device_id_hash=device_id_hash,
            device_secret_hash=_hash_device_value(device_secret),
            device_platform=device_platform,
            device_name=device_name,
        )
        db.add(trusted_device)
    else:
        trusted_device.user_id = user.id
        trusted_device.device_secret_hash = _hash_device_value(device_secret)
        trusted_device.device_platform = device_platform
        trusted_device.device_name = device_name
    trusted_device.last_seen_at = phnom_penh_now()
    db.commit()
    return device_secret


def authenticate_trusted_device(
    db: Session,
    *,
    device_id: str,
    device_secret: str,
) -> User | None:
    trusted_device = db.execute(
        select(TrustedDevice).where(TrustedDevice.device_id_hash == _hash_device_value(device_id))
    ).scalar_one_or_none()
    if trusted_device is None:
        return None
    if not hmac.compare_digest(
        trusted_device.device_secret_hash,
        _hash_device_value(device_secret),
    ):
        return None

    user = db.get(User, trusted_device.user_id)
    if user is None:
        return None

    trusted_device.last_seen_at = phnom_penh_now()
    db.commit()
    return user


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
