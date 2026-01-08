import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from aiogram import Dispatcher

from sophie_bot.config import CONFIG
from sophie_bot.modules import load_modules
from sophie_bot.utils.logger import log


# We need to patch the databases in order to be able to run this in CI without them.
@patch("redis.asyncio.Redis")
@patch("redis.StrictRedis")
def generate_openapi(mock_redis, mock_aredis):
    mock_aredis.return_value = AsyncMock()

    log.info("Starting OpenAPI generation task...")
    dp = Dispatcher()

    CONFIG.mode = "nostart"

    # Initialize modules to populate LOADED_API_ROUTERS
    asyncio.run(load_modules(dp, ["*"], CONFIG.modules_not_load))

    from sophie_bot.services.rest import app, init_api_routers

    init_api_routers(app)

    openapi_data = app.openapi()

    output_path = Path("openapi.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(openapi_data, f, indent=2)

    log.info(f"OpenAPI documentation generated to {output_path}")


if __name__ == "__main__":
    generate_openapi()
