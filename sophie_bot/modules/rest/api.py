from datetime import timedelta

import ujson
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sophie_bot.config import CONFIG
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.utils.api.auth import (
    create_access_token,
    verify_telegram_login_widget,
    verify_tma_init_data,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


class TMALoginRequest(BaseModel):
    initData: str


class WidgetLoginRequest(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class OperatorLoginRequest(BaseModel):
    token: str


class DummyUser:
    def __init__(self, id, first_name, last_name, username, is_bot):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot


@router.post("/login/tma", response_model=Token)
async def login_tma(data: TMALoginRequest):
    verified_data = verify_tma_init_data(data.initData)

    user_data_str = verified_data.get("user")
    if not user_data_str:
        raise HTTPException(status_code=400, detail="Missing user data in initData")

    try:
        user_data = ujson.loads(user_data_str)
        user_id = user_data["id"]
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid user data")

    dummy_user = DummyUser(
        id=user_id,
        first_name=user_data.get("first_name", "User"),
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
        is_bot=False,
    )

    await ChatModel.upsert_user(dummy_user)  # type: ignore

    access_token_expires = timedelta(minutes=CONFIG.api_jwt_expire_minutes)
    access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/widget", response_model=Token)
async def login_widget(data: WidgetLoginRequest):
    data_dict = data.model_dump(exclude_none=True)
    verify_telegram_login_widget(data_dict)

    user_id = data.id

    dummy_user = DummyUser(
        id=user_id,
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username,
        is_bot=False,
    )

    await ChatModel.upsert_user(dummy_user)  # type: ignore

    access_token_expires = timedelta(minutes=CONFIG.api_jwt_expire_minutes)
    access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/operator", response_model=Token)
async def login_operator(data: OperatorLoginRequest):
    sub = None
    scopes = []

    if CONFIG.api_operator_token and data.token == CONFIG.api_operator_token:
        if CONFIG.owner_id:
            sub = str(CONFIG.owner_id)
            scopes = ["operator"]
        else:
            raise HTTPException(status_code=500, detail="Owner ID not configured")
    else:
        # TODO: Implement ApiTokenModel check
        raise HTTPException(status_code=401, detail="Invalid token")

    access_token_expires = timedelta(minutes=CONFIG.api_jwt_expire_minutes)
    access_token = create_access_token(data={"sub": sub, "scopes": scopes}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
