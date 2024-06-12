"""Logging utility."""

import logging.config


def configure_logging(log_level: str) -> None:
    """
    Configure application logging.

    Args:
        log_level (str): log level for logging

    Returns: 
        None
    """
    log_msg_fmt = (
        "%(asctime)s [%(name)s:%(filename)s:%(lineno)d] %(levelname)s: %(message)s"
    )
    log_config_dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "loggers": {
            "root": {
                "level": log_level,
                "handlers": ["console"],
            },
            "yoda": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
        },
        "formatters": {
            "standard": {"format": log_msg_fmt},
        },
    }

    logging.config.dictConfig(log_config_dict)