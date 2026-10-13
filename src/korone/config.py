from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, Field, SecretStr, ValidationInfo, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

type PortNumber = Annotated[int, Field(ge=1, le=65535)]
type PositiveSeconds = Annotated[int, Field(gt=0)]
type RedisDatabase = Annotated[int, Field(ge=0)]
type WebhookConnections = Annotated[int, Field(ge=1, le=100)]
type MediaConcurrency = Annotated[int, Field(ge=1, le=32)]


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="data/config.env", env_file_encoding="utf-8", extra="ignore", frozen=True, validate_default=True
    )

    token: SecretStr = SecretStr("12345:ABCDEFG")
    debug_mode: bool = False

    owner_id: int | None = None
    operators: tuple[int, ...] = ()

    db_url: str = "postgresql+asyncpg://korone:korone@postgres:5432/korone"

    redis_host: str = "localhost"
    redis_port: PortNumber = 6379
    redis_db_states: RedisDatabase = 2
    redis_db_schedule: RedisDatabase = 3

    media_max_concurrent_downloads: MediaConcurrency = 8
    media_max_concurrent_transforms: MediaConcurrency = 4
    media_max_concurrent_posts: MediaConcurrency = 2
    media_local_download_timeout_seconds: PositiveSeconds = 1800
    media_local_send_timeout_seconds: PositiveSeconds = 1800

    botapi_server: AnyHttpUrl | None = None
    botapi_local_storage_root: str = "/var/lib/telegram-bot-api"
    botapi_server_storage_root: str = "/var/lib/telegram-bot-api"
    botapi_upload_root: Path | None = None

    @model_validator(mode="after")
    def validate_botapi_paths(self) -> Config:
        local_root = Path(self.botapi_local_storage_root)
        server_root = Path(self.botapi_server_storage_root)
        if not local_root.is_absolute() or not server_root.is_absolute():
            msg = "Bot API storage roots must be absolute paths"
            raise ValueError(msg)
        if self.botapi_upload_root is not None:
            if self.botapi_server is None or not self.botapi_upload_root.is_absolute():
                msg = "BOTAPI_UPLOAD_ROOT requires a local Bot API server and an absolute path"
                raise ValueError(msg)
            if not self.botapi_upload_root.resolve().is_relative_to(local_root.resolve()):
                msg = "BOTAPI_UPLOAD_ROOT must be inside BOTAPI_LOCAL_STORAGE_ROOT"
                raise ValueError(msg)
        return self

    webhook_domain: str | None = None
    webhook_secret: SecretStr | None = None
    webhook_path: str = "/"
    webhook_max_connections: WebhookConnections = 40
    web_server_port: PortNumber = 8080

    modules_load: tuple[str, ...] = ("*",)
    modules_not_load: tuple[str, ...] = ()

    sentry_url: AnyHttpUrl | None = None

    devs_managed_languages: tuple[str, ...] = ("en_US",)
    translation_url: str = "https://weblate.amanoteam.com/projects/korone/"
    news_channel: str = "https://t.me/PyKorone"
    source_code: str = "https://github.com/HitaloM/PyKorone"
    privacy_link: str = "https://telegram.org/privacy-tpa"
    github_issues: str = "https://github.com/HitaloM/PyKorone/issues"

    default_locale: str = "en_US"

    cors_bypass_url: AnyHttpUrl | None = None

    lastfm_key: SecretStr | None = None

    @computed_field
    @property
    def bot_id(self) -> int:
        return int(self.token.get_secret_value().split(":")[0])

    @field_validator("operators")
    @classmethod
    def validate_operators(cls, operators: tuple[int, ...], info: ValidationInfo) -> tuple[int, ...]:
        owner_id = info.data.get("owner_id")

        if owner_id and owner_id not in operators:
            return (*operators, owner_id)
        return operators

    @field_validator("db_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "postgresql://")):
            msg = "db_url must be a PostgreSQL URL"
            raise ValueError(msg)
        return v

    @field_validator("cors_bypass_url", mode="before")
    @classmethod
    def validate_cors_bypass_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        if "://" not in value:
            return f"http://{value}"
        return value

    @field_validator("webhook_path")
    @classmethod
    def validate_webhook_path(cls, v: str) -> str:
        if not v.startswith("/"):
            return f"/{v}"
        return v


CONFIG = Config()
