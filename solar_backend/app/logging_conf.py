import logging
import sys

from loguru import logger

from app.config import config


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging() -> None:
    log_level = "DEBUG" if config.ENV_STATE == "dev" else "INFO"
    is_dev = config.ENV_STATE == "dev"

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        enqueue=True,
        backtrace=is_dev,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )

    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "app",
    ):
        stdlib_logger = logging.getLogger(logger_name)
        stdlib_logger.handlers = [intercept_handler]
        stdlib_logger.propagate = False
