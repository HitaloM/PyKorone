from aiohttp import ClientSession, TCPConnector


class HTTPClient:
    _session: ClientSession | None = None
    _connector: TCPConnector | None = None

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is None or cls._session.closed:
            if cls._connector is None or cls._connector.closed:
                cls._connector = TCPConnector(
                    use_dns_cache=True,
                    limit=100,
                    limit_per_host=30,
                    ttl_dns_cache=300,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True,
                    force_close=False,
                )
            cls._session = ClientSession(connector=cls._connector)
        return cls._session

    @classmethod
    async def close(cls) -> None:
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None

        if cls._connector and not cls._connector.closed:
            await cls._connector.close()
            cls._connector = None
