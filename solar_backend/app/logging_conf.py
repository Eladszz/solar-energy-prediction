from logging.config import dictConfig
from pathlib import Path
import logging 
from app.config import DevConfig, config
CORRELATION_ID_LENGTH = 32
UUID_LENGTH = 8

def obfustcated(email: str, obfuscated_length: int = 2) -> str:
    characters = email[:obfuscated_length]
    first, last = email.split("@")
    return characters + "*" * (len(first) - obfuscated_length) + "@" + last


class EmailObfuscationFilter(logging.Filter):

    def __init__(self, name:str = "", obfuscated_length: int = 2) -> None:
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__:
            setattr(record, "email", obfustcated(getattr(record, "email"), self.obfuscated_length))

        return True

handlers = ["default", "rotating_file", "json_file"]
if isinstance(config, DevConfig):
    handlers.append("logtail")


def configure_logging() -> None:
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": "asgi_correlation_id.CorrelationIdFilter",
                "uuid_length": UUID_LENGTH if isinstance(config, DevConfig) else CORRELATION_ID_LENGTH,
                "default_value": "-"
            },
            "email_obfuscation": {
                "()": EmailObfuscationFilter,
                "obfuscated_length": 2
            }
        },
        "formatters": {
            "console":{
                "class": "logging.Formatter",
                "datetimefmt": "%Y-%m-%dT%H:%M:%S",
                "format": "(%(correlation_id)s) %(name)s - %(levelname)s - %(message)s"
            },
            "file":{
                "class": "logging.Formatter",
                "datetimefmt": "%Y-%m-%dT%H:%M:%S",
                "format": "%(asctime)s.%(msecs)03dZ %(name)-30s | %(levelname)-8s | [%(correlation_id)s] %(name)s:%(lineno)d - %(message)s"
            },
            "json_file":{
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(name)s %(levelname)s %(correlation_id)s %(message)s",
                "format": "%(asctime)s.%(msecs)03dZ %(name)-30s - %(levelname)-8s - [%(correlation_id)s] %(name)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "default":{
                "class": "rich.logging.RichHandler",
                "formatter": "console",
                "level": "DEBUG",
                "filters": ["correlation_id", "email_obfuscation"]
            },
            "rotating_file":{
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "file",
                "filename": "logs/solar_prediction_backend.log",
                "level": "DEBUG",
                "when": "midnight",
                "backupCount": 5,
                "encoding": "utf8",
                "filters": ["correlation_id"]
            },
            "json_file":{
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "json_file",
                "filename": "logs/solar_prediction_backend.jsonl",
                "level": "DEBUG",
                "when": "midnight",
                "backupCount": 5,
                "encoding": "utf8",
                "filters": ["correlation_id"]
            },
            "logtail":{
                "class": "logtail.LogtailHandler",
                "formatter": "console",
                "level": "DEBUG",
                "source_token": config.LOGTAIL_API_KEY,
                "filters": ["correlation_id", "email_obfuscation"]
            }

        },
        "loggers": {
            "app": {
                "handlers": ["default", "rotating_file", "json_file", "logtail"],
                "level": "DEBUG" if config.ENV_STATE == "dev" else "INFO",
                "propagate": False
            },
            "solar_prediction_backend": {
                "handlers": ["default", "rotating_file", "json_file", "logtail"],
                "level": "DEBUG" if config.ENV_STATE == "dev" else "INFO",
                "propagate": False
            },
            "uvicorn":{
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False
            },
            "databases": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False
            },
            "aiosqlite": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False
            }
        }
    })