from ipaddress import IPv4Network
from typing import Annotated, List, Optional

from aiogram.webhook.security import DEFAULT_TELEGRAM_NETWORKS
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    FilePath,
    computed_field,
    field_validator,
    validator,
)
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    token: str

    app_id: int
    app_hash: str
    username: str

    owner_id: int
    operators: List[int]

    mongo_host: str = "mongodb://localhost"
    mongo_port: int = 27017
    mongo_db: str = "sophie"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_fsm: int = 1
    redis_db_states: int = 2
    redis_db_schedule: int = 3

    botapi_server: Optional[AnyHttpUrl] = None

    debug_mode: bool = False
    modules_load: List[str] = ["*"]
    modules_not_load: List[str] = []

    webhooks_enable: bool = False
    webhooks_listen: str = "127.0.0.1"
    webhooks_port: int = 8080
    webhooks_path: str = "/"
    webhooks_https_certificate: Optional[FilePath] = None
    webhooks_https_certificate_key: Optional[FilePath] = None

    webhooks_allowed_networks: Annotated[List[IPv4Network], Field(validate_default=True)] = [IPv4Network("127.0.0.0/8")]
    webhooks_secret_token: Optional[str] = None
    webhooks_handle_in_background: bool = True

    commands_prefix: str = "/!"
    commands_ignore_case: bool = True
    commands_ignore_mention: bool = False
    commands_ignore_forwarded: bool = True
    commands_ignore_code: bool = True

    sentry_url: Optional[AnyHttpUrl] = None

    devs_managed_languages: List[str] = ["en_US"]
    # A list of languages that are managed by developers; Will disable
    # showing percent of it and won't suggest to help to translate it on crowdin.
    translation_url: str = "https://google.com"
    support_link: str = "https://google.com"

    default_locale: str = "en_US"

    is_proxy: bool = False
    stable_instance_url: str = "http://host.container.internal:8071"
    beta_instance_url: str = "http://host.container.internal:8072"

    class Config:
        env_file = "data/config.env"
        env_file_encoding = "utf-8"

    @computed_field
    @property
    def bot_id(self) -> int:
        return int(self.token.split(":")[0])

    @validator("operators")
    def validate_operators(cls, value: List[int], values) -> List[int]:
        owner_id = values["owner_id"]
        if owner_id not in value:
            value.append(owner_id)
        return value

    @field_validator("webhooks_allowed_networks")
    @classmethod
    def add_telegram_networks(cls, v: List[IPv4Network]) -> List[IPv4Network]:
        v.extend(DEFAULT_TELEGRAM_NETWORKS)
        return v


class CacheTTL(BaseModel):
    default_ttl: int = 1800  # 30 minutes
    language_ttl: int = 86400  # 24 hours


CONFIG = Config()
CACHE_TTL = CacheTTL()
