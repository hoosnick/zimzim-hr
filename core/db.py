from loguru import logger
from piccolo.apps.user.tables import BaseUser
from piccolo.engine import engine_finder
from piccolo_admin.endpoints import TableConfig, create_admin
from piccolo_api.crud.endpoints import OrderBy
from piccolo_api.session_auth.tables import SessionsBase
from piccolo_api.token_auth.tables import TokenAuth

from apps.hr.tables import Area, Device, Group, Message, Person
from core.config import settings

area_table_config = TableConfig(
    table_class=Area,
    link_column=Area.area_id,
    exclude_visible_columns=[Area.id, Area.updated_at, Area.created_at],
    order_by=[OrderBy(column=Area.created_at, ascending=False)],
    menu_group="Hikvision",
)

device_table_config = TableConfig(
    table_class=Device,
    link_column=Device.device_id,
    exclude_visible_columns=[Device.id, Device.updated_at, Device.created_at],
    order_by=[OrderBy(column=Device.created_at, ascending=False)],
    menu_group="Hikvision",
)

group_table_config = TableConfig(
    table_class=Group,
    link_column=Group.group_id,
    exclude_visible_columns=[Group.id, Group.updated_at, Group.created_at],
    order_by=[OrderBy(column=Group.created_at, ascending=False)],
    menu_group="Hikvision",
)

message_table_config = TableConfig(
    table_class=Message,
    exclude_visible_columns=[
        Message.payload,
        Message.retry_count,
        Message.last_error,
        Message.updated_at,
        Message.created_at,
    ],
    order_by=[OrderBy(column=Message.created_at, ascending=False)],
    menu_group="Hikvision",
)

person_table_config = TableConfig(
    table_class=Person,
    link_column=Person.code,
    exclude_visible_columns=[
        Person.id,
        Person.updated_at,
        Person.created_at,
        Person.finger_data,
        Person.card_no,
        Person.pin_code,
        Person.face_data,
    ],
    order_by=[OrderBy(column=Person.created_at, ascending=False)],
    menu_group="Hikvision",
)

admin_panel = create_admin(
    tables=[
        BaseUser,
        SessionsBase,
        TokenAuth,
        area_table_config,
        device_table_config,
        group_table_config,
        message_table_config,
        person_table_config,
    ],
    debug=settings.DEBUG,
    page_size=settings.MAX_PAGE_SIZE,
    allowed_hosts=settings.ALLOWED_HOSTS,
    production=settings.PRODUCTION,
    sidebar_links={
        "Swagger UI": "/api/docs",
        "Redoc UI": "/api/redoc",
        "Home": "/",
        "Support": settings.OPENAPI_CONTACT["url"],
    },
    default_language_code="ru",
)


async def create_user(login: str, password: str) -> None:
    base_user = BaseUser(
        username=login,
        password=password,
        active=True,
        admin=True,
        superuser=True,
    )
    if not await base_user.exists():
        await base_user.save()
        return logger.debug("Created superuser: %s" % login)
    logger.debug("Superuser already exists: %s" % login)


async def database_connection(close: bool = False) -> None:
    db = engine_finder(settings.PICCOLO_CONF)
    if not db:
        return logger.warning("Database engine not found")

    if db.engine_type == "sqlite":
        return

    if close:
        await db.close_connection_pool()
    else:
        await db.start_connection_pool()

    logger.info("Database Connection %s" % ("Closed" if close else "Started"))
