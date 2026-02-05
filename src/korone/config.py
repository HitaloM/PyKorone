from pydantic import AnyHttpUrl, ValidationInfo, computed_field, field_validator  # noqa: TC002
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    token: str = "12345:ABCDEFG"

    username: str | None = None

    owner_id: int | None = None
    operators: list[int] = []

    db_url: str = "sqlite+aiosqlite:///data/korone.db"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_fsm: int = 1
    redis_db_states: int = 2
    redis_db_schedule: int = 3

    botapi_server: AnyHttpUrl | None = None

    modules_load: list[str] = ["*"]
    modules_not_load: list[str] = []

    commands_prefix: str = "/!"
    commands_ignore_case: bool = True
    commands_ignore_mention: bool = False
    commands_ignore_forwarded: bool = True
    commands_ignore_code: bool = True

    devs_managed_languages: list[str] = ["en_US"]
    translation_url: str = "https://weblate.amanoteam.com/projects/korone/"
    news_channel: str = "https://t.me/PyKorone"
    privacy_link: str = "https://telegram.org/privacy-tpa"
    github_issues: str = "https://github.com/HitaloM/PyKorone/issues"

    default_locale: str = "en_US"

    cors_bypass_url: str = "localhost"

    lastfm_key: str | None = None

    class Config:
        env_file = "data/config.env"
        env_file_encoding = "utf-8"

    @computed_field
    @property
    def bot_id(self) -> int:
        return int(self.token.split(":")[0])

    @field_validator("operators", mode="before")
    @classmethod
    def validate_operators(cls, v: list[int] | None, info: ValidationInfo) -> list[int]:
        owner_id = info.data.get("owner_id")

        if not v:
            return [owner_id] if owner_id else []

        if owner_id and owner_id not in v:
            v.append(owner_id)
        return v


CONFIG = Config()
