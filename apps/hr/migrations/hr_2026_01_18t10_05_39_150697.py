from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Text, Varchar

ID = "2026-01-18T10:05:39:150697"
VERSION = "1.30.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="hr", description=DESCRIPTION)

    manager.alter_column(
        table_class_name="Group",
        tablename="group",
        column_name="name",
        db_column_name="name",
        params={"length": 100},
        old_params={"length": None},
        column_class=Varchar,
        old_column_class=Text,
        schema=None,
    )

    return manager
