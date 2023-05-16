"""mse_home.command.helpers module."""


from pathlib import Path

import requests
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


def is_spawned(name: str) -> bool:
    """Check whether a mse docker is spawned based on its `name`."""
    client = get_client_docker()

    try:
        client.containers.get(name)
    except NotFound:
        return False

    return True


def is_waiting_for_secrets(port: int) -> bool:
    """Check whether the configuration server is up."""
    try:
        response = requests.get(f"https://localhost:{port}/", verify=False, timeout=5)

        if response.status_code == 200 and "Mse-Status" in response.headers:
            return True
    except requests.exceptions.SSLError:
        return False

    return False


def is_ready(url: str, port: int, healthcheck_endpoint: str) -> bool:
    """Check whether the app server is up."""
    try:
        response = requests.get(
            f"{url}:{port}{healthcheck_endpoint}",
            verify=False,
            timeout=5,
        )

        if response.status_code != 503 and "Mse-Status" not in response.headers:
            return True
    except requests.exceptions.SSLError:
        return False
    except requests.exceptions.ConnectionError:
        return False

    return False


def load_docker_image(image_tar_path: Path) -> str:
    """Load the docker image from the image tarball."""
    LOG.info("Loading the docker image...")
    client = get_client_docker()

    with open(image_tar_path, "rb") as f:
        image = client.images.load(f.read())
        return image[0].tags[0]
