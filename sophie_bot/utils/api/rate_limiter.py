from fastapi import HTTPException, Request, status

from sophie_bot.services.redis import aredis


async def rate_limit(request: Request, limit: int = 100, window: int = 60) -> None:
    """
    Rate limit requests by IP address.

    Args:
        request: The incoming request
        limit: Maximum number of requests allowed in the window (default: 100)
        window: Time window in seconds (default: 60)
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{request.url.path}:{client_ip}"

    current = await aredis.get(key)
    if current and int(current) >= limit:
        ttl = await aredis.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": str(max(ttl, 1))},
        )

    async with aredis.pipeline() as pipe:
        await pipe.incr(key)
        await pipe.expire(key, window)
        await pipe.execute()
