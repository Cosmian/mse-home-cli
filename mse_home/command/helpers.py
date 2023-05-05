"""mse_home.command.helpers module."""


from docker import from_env
from docker.client import DockerClient
from docker.errors import DockerException

from mse_home.log import LOGGER as LOG


def get_client_docker() -> DockerClient:
    """Create a Docker client or exit if daemon is down."""
    try:
        return from_env()
    except DockerException as exc:
        LOG.warning("Docker seems not running. Please enable Docker daemon.")
        LOG.info("MSE needs Docker to build your app docker.")
        LOG.info("Please refer to the documentation for more details.")
        raise exc
