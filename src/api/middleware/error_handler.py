from fastapi import Request
from fastapi.responses import JSONResponse

from src.common.logger import get_logger
from src.common.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)

    if settings.app_env == "local":
        message = str(exc)
    else:
        message = "Internal server error"

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": message,
            "data": None,
        },
    )