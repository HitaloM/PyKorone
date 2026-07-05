from typing import Annotated

from pydantic import AnyHttpUrl, Field, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

type PortNumber = Annotated[int, Field(ge=1, le=65535)]
type PositiveSeconds = Annotated[int, Field(gt=0)]
type RedisDatabase = Annotated[int, Field(ge=0)]
type WebhookConnections = Annotated[int, Field(ge=1, le=100)]


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="data/config.env", env_file_encoding="utf-8", extra="ignore", frozen=True, validate_default=True
    )

    token: str = "12345:ABCDEFG"
    debug_mode: bool = False

    owner_id: int | None = None
    operators: tuple[int, ...] = ()

    db_url: str = "postgresql+asyncpg://korone:korone@postgres:5432/korone"

    redis_host: str = "localhost"
    redis_port: PortNumber = 6379
    redis_db_fsm: RedisDatabase = 1
    redis_db_states: RedisDatabase = 2
    redis_db_schedule: RedisDatabase = 3
    redis_fsm_key_prefix: str = "korone:fsm"
    redis_fsm_state_ttl: PositiveSeconds | None = 24 * 60 * 60
    redis_fsm_data_ttl: PositiveSeconds | None = 24 * 60 * 60

    botapi_server: AnyHttpUrl | None = None
    botapi_local_storage_root: str = "/var/lib/telegram-bot-api"

    webhook_domain: str | None = None
    webhook_secret: str | None = None
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

    lastfm_key: str | None = None

    @computed_field
    @property
    def bot_id(self) -> int:
        return int(self.token.split(":")[0])

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
