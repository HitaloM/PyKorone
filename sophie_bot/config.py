from ipaddress import IPv4Network
from typing import Annotated, List, Literal, Optional

from aiogram.webhook.security import DEFAULT_TELEGRAM_NETWORKS
from pydantic import (
    AnyHttpUrl,
    Field,
    FilePath,
    computed_field,
    field_validator,
    ValidationInfo,
)
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    token: str = "12345:ABCDEFG"

    username: str | None = None

    owner_id: int | None = None
    operators: List[int] = []

    mode: Literal["bot", "scheduler", "nostart", "rest"] = "bot"
    dev_reload: bool = False  # Enable hot-reload for development (watches file changes)

    mongo_host: str = "mongodb://localhost"
    mongo_port: int = 27017
    mongo_db: str = "sophie"
    mongo_allow_index_dropping: bool = True

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_fsm: int = 1
    redis_db_states: int = 2
    redis_db_schedule: int = 3

    botapi_server: Optional[AnyHttpUrl] = None

    # Debugging
    # off = no debug, normal = debug logging, high = debug + mongo logs + debug middlewares
    debug_mode: Literal["off", "normal", "high"] = "off"
    memory_debug: bool = False  # Memory leaks debugging

    modules_load: List[str] = ["*"]
    modules_not_load: List[str] = []
    legacy_modules_not_load: List[str] = []

    webhooks_enable: bool = False
    webhooks_listen: str = "127.0.0.1"
    webhooks_port: int = 8080
    webhooks_path: str = "/"
    webhooks_https_certificate: Optional[FilePath] = None
    webhooks_https_certificate_key: Optional[FilePath] = None
    webhooks_filter_ips: bool = False
    webhooks_allowed_networks: Annotated[List[IPv4Network], Field(validate_default=True)] = [IPv4Network("127.0.0.0/8")]
    webhooks_secret_token: Optional[str] = None
    webhooks_handle_in_background: bool = True

    api_listen: str = "0.0.0.0"
    api_port: int = 8075
    api_jwt_secret: str = "change_me_in_production"
    api_operator_token: Optional[str] = "test"
    api_jwt_expire_minutes: int = 720  # 12 hours
    api_cors_origins: List[str] = ["*"]

    commands_prefix: str = "/!"
    commands_ignore_case: bool = True
    commands_ignore_mention: bool = False
    commands_ignore_forwarded: bool = True
    commands_ignore_code: bool = True

    sentry_url: Optional[AnyHttpUrl] = None

    devs_managed_languages: List[str] = ["en_US"]
    # A list of languages that are managed by developers; Will disable
    # showing percent of it and won't suggest to help to translate it on crowdin.
    translation_url: str = "https://crowdin.com/project/sophiebot"
    support_link: str = "https://t.me/SophieSupport"
    news_channel: str = "https://t.me/SophieNEWS"
    wiki_link: str = "https://sophie-wiki.orangefox.tech/"
    wiki_modules_link: str = "https://sophie-wiki.orangefox.tech/modules/"
    privacy_link: str = "https://sophie-wiki.orangefox.tech/docs/Privacy%20policy"

    help_featured_module: str = "ai"

    default_locale: str = "en_US"

    environment: str = "production"

    proxy_enable: bool = False
    proxy_stable_instance_url: str = "http://host.container.internal:8071"
    proxy_beta_instance_url: str = "http://host.container.internal:8072"

    # OpenRouter API key for routing non-Mistral models via OpenAI-compatible API
    openrouter_api_key: str | None = None
    tavily_api_key: str = ""
    mistral_api_key: str | None = None

    ai_autotrans_lowmem: bool = False

    # Metrics configuration
    metrics_enable: bool = True
    metrics_backend: Literal["prometheus", "prometheus_pushgateway"] = "prometheus"
    metrics_listen_host: str = "127.0.0.1"
    metrics_listen_port: int = 9108
    metrics_path: str = "/metrics"
    metrics_env: str = "dev"  # const label
    metrics_instance_id: Optional[str] = None  # default to hostname
    metrics_enable_default_collectors: bool = True
    metrics_light_mode: bool = True  # disable some histograms if True
    metrics_sample_ratio: float = 1.0
    metrics_path_on_webhook: bool = False  # add /metrics to webhook server

    # Pushgateway configuration
    pushgateway_url: Optional[str] = None
    pushgateway_job: str = "sophie-bot"
    push_interval_seconds: int = 10

    class Config:
        env_file = "data/config.env"
        env_file_encoding = "utf-8"

    @computed_field
    @property
    def bot_id(self) -> int:
        return int(self.token.split(":")[0])

    @computed_field
    @property
    def security_log_file(self) -> str:
        return f"data/security.{self.mode}.{self.bot_id}.log.txt"

    @field_validator("operators", mode="before")
    @classmethod
    def validate_operators(cls, v: List[int] | None, info: ValidationInfo) -> List[int]:
        owner_id = info.data.get("owner_id")

        if not v:
            return [owner_id] if owner_id else []

        if owner_id and owner_id not in v:
            v.append(owner_id)
        return v

    @field_validator("api_jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("environment") == "production" and v == "change_me_in_production":
            raise ValueError("api_jwt_secret must be changed in production")
        return v

    @field_validator("api_operator_token")
    @classmethod
    def validate_operator_token(cls, v: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("environment") == "production" and v == "test":
            raise ValueError("api_operator_token must be changed in production")
        return v

    @field_validator("api_cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: List[str], info: ValidationInfo) -> List[str]:
        if info.data.get("environment") == "production" and "*" in v:
            raise ValueError("api_cors_origins must not contain '*' in production")
        return v

    @field_validator("webhooks_allowed_networks")
    @classmethod
    def add_telegram_networks(cls, v: List[IPv4Network]) -> List[IPv4Network]:
        v.extend(DEFAULT_TELEGRAM_NETWORKS)
        return v


CONFIG = Config()
