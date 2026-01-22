import sys
from pathlib import Path

from loguru import logger

from core.config import settings


def setup_logger(component: str = "app"):
    """
    Setup component-specific logging with separate log files.

    Args:
        component: Name of the component (e.g., 'worker', 'poller', 'api')
    """
    log_dir = Path(settings.LOGGING.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # Console output with component name and colorized formatting
    logger.add(
        sys.stdout,
        format="<cyan>[{extra[component]}]</cyan> | <level>{level: <8}</level> | <green>{time:DD.MM.YYYY HH:mm:ss.SSS}</green> | <blue>{name}</blue>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOGGING.LOG_STD_LEVEL,
        filter=lambda record: record["level"].name != "ERROR",
        colorize=True,
    )

    # Component-specific info/debug log file
    logger.add(
        log_dir / f"{component}_info.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | [{extra[component]}] | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        filter=lambda record: record["level"].name != "ERROR",
        rotation="500 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        diagnose=False,
    )

    # Component-specific error log file with full diagnostics
    logger.add(
        log_dir / f"{component}_error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | [{extra[component]}] | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
        level="ERROR",
        filter=lambda record: record["level"].name == "ERROR",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        diagnose=True,
        backtrace=True,
    )

    # Bind component name to all log records
    logger.configure(extra={"component": component.upper()})

    logger.info(f"Logger initialized for component: {component.upper()}")

    return logger
