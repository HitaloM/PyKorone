import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from sophie_bot.utils.api.auth import (
    create_access_token,
    generate_token,
    get_current_operator,
    get_current_user,
    hash_token,
    verify_telegram_login_widget,
    verify_tma_launch_params,
)


@pytest.fixture
def mock_config():
    with patch("sophie_bot.utils.api.auth.CONFIG") as mock:
        mock.api_jwt_secret = "test_secret"
        mock.token = "12345:TEST_TOKEN"
        mock.operators = [12345]
        yield mock


def test_generate_token():
    token = generate_token(32)
    assert len(token) > 32  # token_urlsafe returns more than requested bytes as characters
    assert isinstance(token, str)


def test_hash_token():
    token = "test_token"
    expected_hash = hashlib.sha256(token.encode()).hexdigest()
    assert hash_token(token) == expected_hash


def test_create_access_token(mock_config):
    data = {"sub": "user_123"}
    token = create_access_token(data)
    decoded = jwt.decode(token, mock_config.api_jwt_secret, algorithms=["HS256"])
    assert decoded["sub"] == "user_123"
    assert "exp" in decoded


def test_create_access_token_with_delta(mock_config):
    data = {"sub": "user_123"}
    expires_delta = timedelta(hours=1)
    token = create_access_token(data, expires_delta=expires_delta)
    decoded = jwt.decode(token, mock_config.api_jwt_secret, algorithms=["HS256"])
    assert decoded["sub"] == "user_123"

    # Check expiration is roughly 1 hour from now
    expected_exp = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    assert abs(decoded["exp"] - expected_exp) < 5


def test_verify_tma_init_data_success(mock_config):
    # Prepare valid initData
    auth_date = int(time.time())
    parsed_data = {"auth_date": str(auth_date), "user": '{"id": 12345, "first_name": "Test"}'}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", mock_config.token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    init_data = "&".join(f"{k}={v}" for k, v in parsed_data.items()) + f"&hash={hash_value}"

    data, returned_hash = verify_tma_launch_params(init_data)
    assert data["auth_date"] == str(auth_date)
    assert returned_hash == hash_value


def test_verify_tma_init_data_invalid_hash(mock_config):
    init_data = "auth_date=12345&hash=wrong_hash"
    with pytest.raises(HTTPException) as excinfo:
        verify_tma_launch_params(init_data)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Invalid hash"


def test_verify_tma_init_data_missing_hash(mock_config):
    init_data = "auth_date=12345"
    with pytest.raises(HTTPException) as excinfo:
        verify_tma_launch_params(init_data)
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Missing hash"


def test_verify_tma_init_data_outdated(mock_config):
    auth_date = int(time.time()) - 90000  # More than 24 hours ago
    parsed_data = {"auth_date": str(auth_date)}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", mock_config.token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    init_data = f"auth_date={auth_date}&hash={hash_value}"

    with pytest.raises(HTTPException) as excinfo:
        verify_tma_launch_params(init_data)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Data is outdated"


def test_verify_tma_init_data_future(mock_config):
    auth_date = int(time.time()) + 120  # 2 minutes in the future
    parsed_data = {"auth_date": str(auth_date)}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", mock_config.token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    init_data = f"auth_date={auth_date}&hash={hash_value}"

    with pytest.raises(HTTPException) as excinfo:
        verify_tma_launch_params(init_data)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Data is from the future"


def test_verify_telegram_login_widget_success(mock_config):
    auth_date = int(time.time())
    data = {"id": "12345", "first_name": "Test", "auth_date": str(auth_date)}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(mock_config.token.encode()).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    data_with_hash = data.copy()
    data_with_hash["hash"] = hash_value

    returned_data, returned_hash = verify_telegram_login_widget(data_with_hash)
    assert returned_data["id"] == "12345"
    assert returned_hash == hash_value


def test_verify_telegram_login_widget_missing_hash(mock_config):
    data = {"id": "12345"}
    with pytest.raises(HTTPException) as excinfo:
        verify_telegram_login_widget(data)
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Missing hash"


def test_verify_telegram_login_widget_with_none_values(mock_config):
    auth_date = int(time.time())
    data = {"id": "12345", "first_name": "Test", "last_name": None, "auth_date": str(auth_date)}
    # Hash should be calculated excluding None values
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()) if v is not None and k != "hash")
    secret_key = hashlib.sha256(mock_config.token.encode()).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    data_with_hash = data.copy()
    data_with_hash["hash"] = hash_value

    returned_data, returned_hash = verify_telegram_login_widget(data_with_hash)
    assert returned_data["id"] == "12345"
    assert returned_data["last_name"] is None
    assert returned_hash == hash_value


@pytest.mark.asyncio
async def test_get_current_user_success(mock_config):
    user_id = "507f1f77bcf86cd799439011"
    token = jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}, mock_config.api_jwt_secret
    )
    auth_creds = MagicMock()
    auth_creds.credentials = token

    mock_user = MagicMock()

    with patch("sophie_bot.utils.api.auth.ChatModel.get_by_iid", new_callable=AsyncMock) as mock_get_by_iid:
        mock_get_by_iid.return_value = mock_user
        user = await get_current_user(auth_creds)
        assert user == mock_user
        mock_get_by_iid.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_user_expired(mock_config):
    user_id = "507f1f77bcf86cd799439011"
    token = jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) - timedelta(minutes=15)}, mock_config.api_jwt_secret
    )
    auth_creds = MagicMock()
    auth_creds.credentials = token

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(auth_creds)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Token expired"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_config):
    auth_creds = MagicMock()
    auth_creds.credentials = "invalid_token"

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(auth_creds)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_not_found(mock_config):
    user_id = "507f1f77bcf86cd799439011"
    token = jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}, mock_config.api_jwt_secret
    )
    auth_creds = MagicMock()
    auth_creds.credentials = token

    with patch("sophie_bot.utils.api.auth.ChatModel.get_by_iid", new_callable=AsyncMock) as mock_get_by_iid:
        mock_get_by_iid.return_value = None
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(auth_creds)
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_no_sub(mock_config):
    token = jwt.encode({"exp": datetime.now(timezone.utc) + timedelta(minutes=15)}, mock_config.api_jwt_secret)
    auth_creds = MagicMock()
    auth_creds.credentials = token

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(auth_creds)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_invalid_iid(mock_config):
    token = jwt.encode(
        {"sub": "invalid_iid", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}, mock_config.api_jwt_secret
    )
    auth_creds = MagicMock()
    auth_creds.credentials = token

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(auth_creds)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_db_error(mock_config):
    user_id = "507f1f77bcf86cd799439011"
    token = jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}, mock_config.api_jwt_secret
    )
    auth_creds = MagicMock()
    auth_creds.credentials = token

    with patch("sophie_bot.utils.api.auth.ChatModel.get_by_iid", new_callable=AsyncMock) as mock_get_by_iid:
        mock_get_by_iid.side_effect = Exception("DB Error")
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(auth_creds)
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_operator_by_id(mock_config):
    user = MagicMock()
    user.chat_id = 12345  # In mock_config.operators
    auth_creds = MagicMock()

    operator = await get_current_operator(user, auth_creds)
    assert operator == user


@pytest.mark.asyncio
async def test_get_current_operator_by_scope(mock_config):
    user = MagicMock()
    user.chat_id = 99999  # NOT in mock_config.operators
    token = jwt.encode({"scopes": ["operator"]}, mock_config.api_jwt_secret)
    auth_creds = MagicMock()
    auth_creds.credentials = token

    operator = await get_current_operator(user, auth_creds)
    assert operator == user


@pytest.mark.asyncio
async def test_get_current_operator_forbidden(mock_config):
    user = MagicMock()
    user.chat_id = 99999  # NOT in mock_config.operators
    token = jwt.encode({"scopes": ["user"]}, mock_config.api_jwt_secret)
    auth_creds = MagicMock()
    auth_creds.credentials = token

    with pytest.raises(HTTPException) as excinfo:
        await get_current_operator(user, auth_creds)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_current_operator_invalid_token(mock_config):
    user = MagicMock()
    user.chat_id = 99999  # NOT in mock_config.operators
    auth_creds = MagicMock()
    auth_creds.credentials = "invalid_token"

    with pytest.raises(HTTPException) as excinfo:
        await get_current_operator(user, auth_creds)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Not enough permissions"
