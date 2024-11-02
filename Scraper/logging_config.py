import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import add_log_level
from structlog.processors import TimeStamper

structlog.configure(
    processors=[
        TimeStamper(fmt="iso"),
        add_log_level,
        ConsoleRenderer(),
    ]
)

logger = structlog.get_logger()