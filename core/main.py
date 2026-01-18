from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.security.api_key import APIKeyHeader
from loguru import logger
from piccolo_api.crud.endpoints import PiccoloCRUD, Validators
from piccolo_api.fastapi.endpoints import FastAPIKwargs, FastAPIWrapper
from piccolo_api.token_auth.middleware import PiccoloTokenAuthProvider, TokenAuthBackend
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from apps.home.endpoints import HomeEndpoint
from apps.hr.tables import Area, Device, Group, Person
from apps.utils.hooks import handle_auth_exception, validator_superuser
from apps.utils.logger import setup_logger
from core.config import settings as config
from core.db import admin_panel, create_user, database_connection

setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database_connection()

    await create_user(config.LOGIN, config.PASSWORD)

    logger.info("Application startup complete")

    yield

    await database_connection(close=True)

    logger.info("Application shutdown complete")


app = FastAPI(
    debug=config.DEBUG,
    routes=[
        Route("/", HomeEndpoint),
        Mount("/super-admin/", admin_panel),
        Mount("/static/", StaticFiles(directory="apps/home/static")),
        Route("/favicon.ico", RedirectResponse(url="/static/favicon.ico")),
    ],
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

private_app = FastAPI(
    title=config.OPENAPI_TITLE,
    contact=config.OPENAPI_CONTACT,
    debug=config.DEBUG,
    dependencies=[Depends(APIKeyHeader(name="Authorization"))],
)

protected_app = AuthenticationMiddleware(
    private_app,
    backend=TokenAuthBackend(
        PiccoloTokenAuthProvider(),
        excluded_paths=[
            "/api/docs",
            "/api/openapi.json",
        ],
    ),
    on_error=handle_auth_exception,
)

VALIDATORS = Validators(
    put_single=[validator_superuser],
    patch_single=[validator_superuser],
    delete_single=[validator_superuser],
    post_single=[validator_superuser],
    delete_all=[validator_superuser],
)

FastAPIWrapper(
    root_url=config.API_V1_STR + "/areas/",
    fastapi_app=private_app,
    piccolo_crud=PiccoloCRUD(
        table=Area,
        read_only=False,
        validators=VALIDATORS,
    ),
    fastapi_kwargs=FastAPIKwargs(
        all_routes={"tags": ["Areas"]},
    ),
)

FastAPIWrapper(
    root_url=config.API_V1_STR + "/devices/",
    fastapi_app=private_app,
    piccolo_crud=PiccoloCRUD(
        table=Device,
        read_only=False,
        max_joins=1,
        validators=VALIDATORS,
    ),
    fastapi_kwargs=FastAPIKwargs(
        all_routes={"tags": ["Devices"]},
    ),
)

FastAPIWrapper(
    root_url=config.API_V1_STR + "/groups/",
    fastapi_app=private_app,
    piccolo_crud=PiccoloCRUD(
        table=Group,
        read_only=False,
        max_joins=1,
        validators=VALIDATORS,
    ),
    fastapi_kwargs=FastAPIKwargs(
        all_routes={"tags": ["Groups"]},
    ),
)

FastAPIWrapper(
    root_url=config.API_V1_STR + "/persons/",
    fastapi_app=private_app,
    piccolo_crud=PiccoloCRUD(
        table=Person,
        read_only=False,
        max_joins=1,
        validators=VALIDATORS,
    ),
    fastapi_kwargs=FastAPIKwargs(
        all_routes={"tags": ["Persons"]},
    ),
)


app.mount("/api/", protected_app)


app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_credentials=True,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
