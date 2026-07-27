"""FastAPI application entrypoint."""

import structlog
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from auth_service.infrastructure.config import get_settings
from auth_service.infrastructure.rate_limiting import limiter
from auth_service.interfaces.api.v1.routers import admin, auth, users

settings = get_settings()

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
)
app.state.limiter = limiter
# slowapi's handler is typed against `RateLimitExceeded` specifically, one
# level narrower than Starlette's generic `Exception` handler signature —
# a known, harmless mismatch between the two libraries' type stubs.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)


@app.get("/health", tags=["monitoring"])
async def health_check() -> dict[str, str]:
    """Liveness/readiness probe for orchestrators (Docker, k8s, load balancers)."""
    logger.info("health_check_called")
    return {"status": "ok"}
