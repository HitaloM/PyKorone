import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
import structlog
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sophie_bot.config import CONFIG
from sophie_bot.db.models.chat import ChatModel

oauth2_scheme = HTTPBearer()
logger = structlog.get_logger(__name__)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CONFIG.api_jwt_secret, algorithm="HS256")
    return encoded_jwt


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _verify_telegram_data(data: dict, hash_value: str, secret_key: bytes) -> None:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()) if v is not None)
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, hash_value):
        raise HTTPException(status_code=403, detail="Invalid hash")

    # Check auth_date
    auth_date = int(data.get("auth_date", 0))
    now = time.time()
    if auth_date > now + 60:  # Allow 1 minute clock drift
        raise HTTPException(status_code=403, detail="Data is from the future")
    if now - auth_date > 86400:  # 1 day expiration
        raise HTTPException(status_code=403, detail="Data is outdated")


def verify_telegram_login_widget(data: dict) -> tuple[dict, str]:
    if "hash" not in data:
        raise HTTPException(status_code=400, detail="Missing hash")

    hash_value = data.pop("hash")
    secret_key = hashlib.sha256(CONFIG.token.encode()).digest()
    _verify_telegram_data(data, hash_value, secret_key)

    return data, hash_value


async def get_current_user(auth: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]) -> ChatModel:
    token = auth.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CONFIG.api_jwt_secret, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("JWT payload missing 'sub' claim")
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        raise credentials_exception

    try:
        user = await ChatModel.get_by_iid(PydanticObjectId(user_id))
    except (ValueError, Exception):
        logger.error("Failed to fetch user by iid from JWT", user_id=user_id)
        raise credentials_exception

    if user is None:
        logger.warning("User not found in database", user_id=user_id)
        raise credentials_exception

    return user


async def get_current_operator(
        user: Annotated[ChatModel, Depends(get_current_user)],
        auth: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> ChatModel:
    token = auth.credentials
    # Check if user is in operators list
    if user.chat_id in CONFIG.operators:
        return user

    # Check if the token claims contain scope "operator"
    try:
        payload = jwt.decode(token, CONFIG.api_jwt_secret, algorithms=["HS256"])
        scopes = payload.get("scopes", [])
        if "operator" in scopes:
            return user
    except jwt.InvalidTokenError:
        pass

    logger.warning("Unauthorized operator access attempt", user_id=user.chat_id)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )
