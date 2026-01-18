import sys
from pathlib import Path

from loguru import logger

from core.config import settings


def setup_logger():
    log_dir = Path(settings.LOGGING.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        format="<level>{level: <5}</level> | <green>{time:DD.MM.YYYY HH:mm:ss}</green> | {function}:{line} - <level>{message}</level>",
        level=settings.LOGGING.LOG_STD_LEVEL,
        filter=lambda record: record["level"].name != "ERROR",
        colorize=True,
    )

    logger.add(
        log_dir / settings.LOGGING.LOG_ACCESS_FILENAME,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        filter=lambda record: record["level"].name != "ERROR",
        rotation="500 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
        diagnose=False,
    )

    logger.add(
        log_dir / settings.LOGGING.LOG_ERROR_FILENAME,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        filter=lambda record: record["level"].name == "ERROR",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        diagnose=False,
        backtrace=True,
    )
