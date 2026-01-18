from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from sophie_bot.config import CONFIG

MAX_REQUEST_SIZE = 1_000_000  # 1MB default


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size to prevent DoS attacks."""

    def __init__(self, app: ASGIApp, max_size: int = MAX_REQUEST_SIZE) -> None:
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)


def create_app() -> FastAPI:
    app = FastAPI(title="Sophie API")

    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)  # type: ignore[arg-type]

    # Request size limit middleware
    app.add_middleware(RequestSizeLimitMiddleware, max_size=MAX_REQUEST_SIZE)  # type: ignore[arg-type]

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=CONFIG.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


def init_api_routers(app: FastAPI) -> None:
    from sophie_bot.modules import LOADED_API_ROUTERS

    for router in LOADED_API_ROUTERS:
        app.include_router(router)
