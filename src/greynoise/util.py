"""Utility functions."""

import logging
import os
import socket
import sys

import structlog
from six.moves.configparser import ConfigParser

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "greynoise", "config"))
LOGGER = structlog.get_logger()

DEFAULT_CONFIG = {
    "api_key": "",
    "api_server": "https://enterprise.api.greynoise.io",
    "timeout": 60,
}


def configure_logging():
    """Configure logging."""
    logging.basicConfig(stream=sys.stderr, format="%(message)s", level=logging.CRITICAL)
    logging.getLogger("greynoise").setLevel(logging.WARNING)
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def load_config():
    """Load configuration.

    :returns:
        Current configuration based on configuration file and environment variables.
    :rtype: dict

    """
    config_parser = ConfigParser(
        {key: str(value) for key, value in DEFAULT_CONFIG.items()}
    )
    config_parser.add_section("greynoise")

    if os.path.isfile(CONFIG_FILE):
        LOGGER.debug("Parsing configuration file: %s...", CONFIG_FILE, path=CONFIG_FILE)
        with open(CONFIG_FILE) as config_file:
            config_parser.readfp(config_file)
    else:
        LOGGER.warning(
            "Configuration file not found: %s", CONFIG_FILE, path=CONFIG_FILE
        )

    if "GREYNOISE_API_KEY" in os.environ:
        api_key = os.environ["GREYNOISE_API_KEY"]
        LOGGER.debug(
            "API key found in environment variable: %s", api_key, api_key=api_key
        )
        # Environment variable takes precedence over configuration file content
        config_parser.set("greynoise", "api_key", api_key)

    if "GREYNOISE_API_SERVER" in os.environ:
        api_server = os.environ["GREYNOISE_API_SERVER"]
        LOGGER.debug(
            "API server found in environment variable: %s",
            api_server,
            api_server=api_server,
        )
        # Environment variable takes precedence over configuration file content
        config_parser.set("greynoise", "api_server", api_server)

    if "GREYNOISE_TIMEOUT" in os.environ:
        timeout = os.environ["GREYNOISE_TIMEOUT"]
        try:
            int(timeout)
        except ValueError:
            LOGGER.error(
                "GREYNOISE_TIMEOUT environment variable "
                "cannot be converted to an integer: %r",
                timeout,
                timeout=timeout,
            )
        else:
            LOGGER.debug(
                "Timeout found in environment variable: %s", timeout, timeout=timeout
            )
            # Environment variable takes precedence over configuration file content
            config_parser.set("greynoise", "timeout", timeout)

    return {
        "api_key": config_parser.get("greynoise", "api_key"),
        "api_server": config_parser.get("greynoise", "api_server"),
        "timeout": config_parser.getint("greynoise", "timeout"),
    }


def save_config(config):
    """Save configuration.

    :param config: Data to be written to the configuration file.
    :type config:  dict

    """
    config_parser = ConfigParser()
    config_parser.add_section("greynoise")
    config_parser.set("greynoise", "api_key", config["api_key"])
    config_parser.set("greynoise", "api_server", config["api_server"])
    config_parser.set("greynoise", "timeout", str(config["timeout"]))

    config_dir = os.path.dirname(CONFIG_FILE)
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    with open(CONFIG_FILE, "w") as config_file:
        config_parser.write(config_file)


def validate_ip(ip_address, strict=True):
    """Check if the IPv4 address is valid.

    :param ip_address: IPv4 address value to validate.
    :type ip_address: str
    :param strict: Whether to raise exception if validation fails.
    :type strict: bool
    :raises ValueError: When validation fails and strict is set to True.

    """
    try:
        socket.inet_aton(ip_address)
        return True
    except socket.error:
        error_message = "Invalid IP address: {!r}".format(ip_address)
        LOGGER.warning(error_message, ip_address=ip_address)
        if strict:
            raise ValueError(error_message)
        return False
