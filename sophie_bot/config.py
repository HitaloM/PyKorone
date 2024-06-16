from typing import List, Optional

from pydantic import validator, AnyHttpUrl, computed_field
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

    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db_fsm: int = 1
    redis_db_states: int = 2
    redis_db_schedule: int = 3

    botapi_server: Optional[AnyHttpUrl] = None

    debug_mode: bool = False
    modules_load: List[str] = []
    modules_not_load: List[str] = []

    webhooks_enable: bool = False
    webhooks_url: str = "/"
    webhooks_port: int = 8080

    commands_prefix: str = "/!"
    commands_ignore_case: bool = True
    commands_ignore_mention: bool = False
    commands_ignore_forwarded: bool = True
    commands_ignore_code: bool = True

    sentry_url: Optional[AnyHttpUrl] = None

    class Config:
        env_file = 'data/config.env'
        env_file_encoding = 'utf-8'

    @computed_field
    @property
    def bot_id(self) -> int:
        return int(self.token.split(':')[0])

    @validator('operators')
    def validate_operators(cls, value: List[int], values) -> List[int]:
        owner_id = values['owner_id']
        if owner_id not in value:
            value.append(owner_id)
        return value


CONFIG = Config()
