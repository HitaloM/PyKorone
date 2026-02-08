from aiohttp import ClientSession


class HTTPClient:
    _session: ClientSession | None = None

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is None or cls._session.closed:
            cls._session = ClientSession()
        return cls._session

    @classmethod
    async def close(cls) -> None:
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
