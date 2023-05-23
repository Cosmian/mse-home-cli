"""mse_home.command.helpers module."""

from pathlib import Path

from docker import from_env
from docker.client import DockerClient
from docker.errors import DockerException, NotFound

from mse_home.log import LOGGER as LOG


def get_client_docker() -> DockerClient:
    """Create a Docker client or exit if daemon is down."""
    try:
        return from_env()
    except DockerException as exc:
        LOG.warning("Docker seems not running. Please enable Docker daemon.")
        LOG.info("MSE needs Docker to manage your app docker.")
        LOG.info("Please refer to the documentation for more details.")
        raise exc


def docker_container_exists(name: str) -> bool:
    """Check whether a mse docker is running based on its `name`."""
    client = get_client_docker()

    try:
        client.containers.get(name)
    except NotFound:
        return False

    return True


def load_docker_image(image_tar_path: Path) -> str:
    """Load the docker image from the image tarball."""
    LOG.info("Loading the docker image...")
    client = get_client_docker()

    with open(image_tar_path, "rb") as f:
        image = client.images.load(f.read())
        return image[0].tags[0]
