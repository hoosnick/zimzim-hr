from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from piccolo_api.crud.endpoints import PiccoloCRUD
from starlette.exceptions import HTTPException


def validator_superuser(piccolo_crud: PiccoloCRUD, request: Request):
    if not request.user.user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a superuser can do this",
        )


def put_not_allowed(piccolo_crud: PiccoloCRUD, request: Request):
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="PUT method is not allowed for this endpoint",
    )


def handle_auth_exception(request: Request, exc: Exception):
    logger.debug("Authentication error: %s | %s" % (request.url, exc))
    return JSONResponse(
        content={"detail": "Invalid or missing authentication token"},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
