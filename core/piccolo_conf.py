from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

from core.config import settings

DB = PostgresEngine(
    config={"dsn": str(settings.DATABASE.DATABASE_URI)},
    log_queries=settings.DEBUG,
)

APP_REGISTRY = AppRegistry(
    apps=[
        # piccolo apps
        "piccolo_api.session_auth.piccolo_app",
        "piccolo_api.token_auth.piccolo_app",
        "piccolo.apps.user.piccolo_app",
        # my apps
        "apps.hr.piccolo_app",
    ]
)
