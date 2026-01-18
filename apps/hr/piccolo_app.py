"""
Import all of the Tables subclasses in your app here, and register them with
the APP_CONFIG.
"""

import os

from piccolo.conf.apps import AppConfig, get_package, table_finder

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="hr",
    migrations_folder_path=os.path.join(
        CURRENT_DIRECTORY,
        "migrations",
    ),
    table_classes=table_finder(
        modules=[".tables"],
        package=get_package(__name__),
        exclude_imported=True,
    ),
    migration_dependencies=[],
    commands=[],
)
