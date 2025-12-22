import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from urllib.parse import parse_qsl

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sophie_bot.config import CONFIG
from sophie_bot.db.models.chat import ChatModel

oauth2_scheme = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CONFIG.api_jwt_secret, algorithm="HS256")
    return encoded_jwt


def verify_tma_init_data(init_data: str) -> dict:
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    if "hash" not in parsed_data:
        raise HTTPException(status_code=400, detail="Missing hash")

    hash_value = parsed_data.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

    secret_key = hmac.new(b"WebAppData", CONFIG.token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_value:
        raise HTTPException(status_code=403, detail="Invalid hash")

    # Check auth_date
    auth_date = int(parsed_data.get("auth_date", 0))
    if time.time() - auth_date > 86400:  # 1 day expiration
        raise HTTPException(status_code=403, detail="Data is outdated")

    return parsed_data


def verify_telegram_login_widget(data: dict) -> dict:
    if "hash" not in data:
        raise HTTPException(status_code=400, detail="Missing hash")

    hash_value = data.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()) if v is not None)

    secret_key = hashlib.sha256(CONFIG.token.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_value:
        raise HTTPException(status_code=403, detail="Invalid hash")

    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=403, detail="Data is outdated")

    return data


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
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    try:
        # Assuming sub is chat_id (int)
        tid = int(user_id)
        user = await ChatModel.get_by_tid(tid)
    except ValueError:
        raise credentials_exception

    if user is None:
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

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )
