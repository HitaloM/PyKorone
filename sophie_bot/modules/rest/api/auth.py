import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from init_data_py import InitData
from init_data_py.errors.errors import InitDataPyError
from pydantic import BaseModel

from sophie_bot.config import CONFIG
from sophie_bot.db.models.api_token import ApiTokenModel
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.refresh_token import RefreshTokenModel
from sophie_bot.utils.api.auth import (
    create_access_token,
    generate_token,
    hash_token,
    logger,
    verify_telegram_login_widget,
)
from sophie_bot.utils.api.rate_limiter import rate_limit
from sophie_bot.utils.logger import log

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TMALoginRequest(BaseModel):
    initData: str


class TelegramLoginWidgetData(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class OperatorLoginRequest(BaseModel):
    token: str


async def create_tokens(user: ChatModel, scopes: list[str] | None = None) -> dict:
    access_token_expires = timedelta(minutes=CONFIG.api_jwt_expire_minutes)
    data: dict[str, Any] = {"sub": str(user.iid)}
    if scopes:
        data["scopes"] = scopes
    access_token = create_access_token(data=data, expires_delta=access_token_expires)

    refresh_token_str = generate_token(64)
    token = RefreshTokenModel(
        token_hash=hash_token(refresh_token_str),
        user=user,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    await token.insert()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/login/tma", response_model=Token, dependencies=[Depends(rate_limit)])
async def login_tma(data: TMALoginRequest):
    try:
        init_data = InitData.parse(data.initData)
    except InitDataPyError:
        log.error("Invalid init data", init_data=data.initData)
        raise HTTPException(status_code=400, detail="Invalid init data")

    if not (init_data.validate(CONFIG.token)):
        log.error("Validation failed for init data", init_data=data.initData)
        raise HTTPException(status_code=403, detail="Invalid init data")

    if not (user := await ChatModel.get_by_tid(init_data.user.id)):
        raise HTTPException(status_code=403, detail="User not found in database")

    return await create_tokens(user)


@router.post("/login/widget", response_model=Token, dependencies=[Depends(rate_limit)])
async def login_widget(data: TelegramLoginWidgetData):
    verify_telegram_login_widget(data.model_dump())

    if not (user := await ChatModel.get_by_tid(data.id)):
        raise HTTPException(status_code=403, detail="User not found in database")

    return await create_tokens(user)


@router.post("/login/operator", response_model=Token, dependencies=[Depends(rate_limit)])
async def login_operator(data: OperatorLoginRequest):
    if CONFIG.api_operator_token and hmac.compare_digest(data.token, CONFIG.api_operator_token):
        if CONFIG.owner_id:
            user = await ChatModel.get_by_tid(CONFIG.owner_id)
            if not user:
                raise HTTPException(status_code=500, detail="Owner not found in database")
            logger.info("Operator logged in via static token", user_id=user.tid)
            return await create_tokens(user, scopes=["operator"])
        else:
            raise HTTPException(status_code=500, detail="Owner ID not configured")

    hashed = hash_token(data.token)
    api_token = await ApiTokenModel.get_by_hash(hashed)
    if api_token:
        user = api_token.user
        logger.info("Operator logged in via API token", user_id=user.tid, label=api_token.label)
        return await create_tokens(user, scopes=["operator"])

    logger.warning("Failed operator login attempt")
    raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/refresh", response_model=Token, dependencies=[Depends(rate_limit)])
async def refresh_token(data: RefreshRequest):
    hashed_token = hash_token(data.refresh_token)

    token = await RefreshTokenModel.get_by_hash(hashed_token)

    if not token:
        logger.warning("Invalid or expired refresh token used")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    expires_at = token.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        logger.warning("Refresh token expired", token_id=token.iid)
        await token.delete()  # Clean up expired token
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Store user reference before deleting the token
    user = token.user

    # Invalidate old refresh token to prevent replay attacks
    await token.delete()

    logger.info("Token refreshed", user_iid=user.id, user_tid=user.tid)
    return await create_tokens(user)
