"""mse_home.log module."""

import logging
import sys


LOGGER = logging.getLogger("mse")


def setup_logging(debug: bool = False):
    """Configure basic logging."""
    format_msg = "%(message)s"

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    logging.basicConfig(format=format_msg, handlers=[stdout_handler])
    LOGGER.setLevel(logging.DEBUG if debug else logging.INFO)
