"""mse_home.command.helpers module."""

import socket
from pathlib import Path
from typing import Optional

from docker import from_env
from docker.client import DockerClient
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from mse_home.error import AppContainerNotFound
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


def app_container_exists(client: DockerClient, name: str) -> Optional[Container]:
    """Check whether an mse docker container exists based on its `name`."""
    try:
        return get_app_container(client, name)
    except AppContainerNotFound:
        return None


def get_app_container(client: DockerClient, name: str) -> Container:
    """Get an mse docker container based on its `name`."""
    try:
        return client.containers.get(name)
    except NotFound as exc:
        raise AppContainerNotFound(
            f"Can't find the mse docker for application '{name}'"
        ) from exc


def load_docker_image(client: DockerClient, image_tar_path: Path) -> str:
    """Load the docker image from the image tarball."""
    LOG.info("Loading the docker image...")
    with open(image_tar_path, "rb") as f:
        image = client.images.load(f.read())
        return image[0].tags[0]


def is_port_free(port: int):
    """Check whether a given `port` is free."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", port))
        sock.close()
    except OSError:
        return False

    return True


def assert_is_file(path: Path):
    """Ensure the given `path` is an existing file."""
    if not path.is_file():
        raise IOError(f"file `{path}` does not exist")


def assert_is_dir(path: Path):
    """Ensure the given `path` is an existing dir."""
    if not path.is_dir():
        raise IOError(f"dir `{path}` does not exist")
