"""mse_home.command.helpers module."""


from pathlib import Path
import tarfile
from typing import Tuple
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
        LOG.info("MSE needs Docker to build your app docker.")
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


def extract_package(workspace: Path, package: Path) -> Tuple[str, str]:
    """Extract the code and image tarballs from the mse package."""
    LOG.info("Extracting the package at %s...", workspace)

    with tarfile.open(package, "r") as package:
        package.extractall(path=workspace)

    code_tar_path = workspace / "code.tar"
    image_tar_path = workspace / "image.tar"

    if not code_tar_path.exists():
        raise Exception(f"{code_tar_path} was not find in the mse package")

    if not image_tar_path.exists():
        raise Exception(f"{image_tar_path} was not find in the mse package")

    return (code_tar_path, image_tar_path)


def load_docker_image(image_tar_path: Path) -> str:
    """Load the docker image from the image tarball."""
    LOG.info("Loading the docker image...")
    client = get_client_docker()

    with open(image_tar_path, "rb") as f:
        image = client.images.load(f.read())
        return image[0].tags[0]
