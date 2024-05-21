"""Yaml parsing utility."""

import sys
import yaml
import logging

logger = logging.getLogger(__name__)

def load_config(config: str) -> dict:
    """
    Loads config file

    Args:
        config (str): path to config file

    Returns:
        data (dict): dictionary of the config file
    """
    try:
        with open(config, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            logger.debug("The %s file has successfully loaded", config)
    except FileNotFoundError as e:
        logger.error("Config file not found: %s", e)
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("An error occurred: %s", e)
        sys.exit(1)
    return data