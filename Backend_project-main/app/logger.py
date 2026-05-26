import sys
import os
import json
from loguru import logger

os.makedirs("logs", exist_ok=True)

logger.remove()

def json_formatter(record):
    log_record = {
        "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f"),
        "level": record["level"].name,
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
        "extra": record["extra"],
    }
    return json.dumps(log_record) + "\n"

logger.add(
    "logs/app.log",
    rotation="10 MB",
    level="INFO",
    format="{message}",
    serialize=False,
)

logger.add(
    "logs/audit.log",
    rotation="5 MB",
    level="INFO",
    format="{message}",
    filter=lambda record: record["extra"].get("audit") is True
)

logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
)

def audit_log(event: str, **kwargs):
    logger.bind(
        audit=True,
        event=event,
        **kwargs
    ).info(f"AUDIT: {event}")