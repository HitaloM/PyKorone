from fastapi import HTTPException, Request, status

from sophie_bot.services.redis import aredis


async def rate_limit(request: Request, limit: int = 50000000, window: int = 600000):
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{request.url.path}:{client_ip}"

    current = await aredis.get(key)
    if current and int(current) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    async with aredis.pipeline() as pipe:
        await pipe.incr(key)
        await pipe.expire(key, window)
        await pipe.execute()
