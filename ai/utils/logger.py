import logging
import sys

import structlog


def get_logger(name: str) -> structlog.BoundLogger:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = logging.Formatter("%(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger(name)
    root_logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if logger is re-initialized
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    return structlog.get_logger(name)
