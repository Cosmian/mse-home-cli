"""mse_home.command.helpers module."""


import tarfile
from pathlib import Path
from typing import Tuple

import requests
from docker import from_env
from docker.client import DockerClient
from docker.errors import DockerException, NotFound

from mse_home import (
    CODE_CONFIG_NAME,
    CODE_TAR_NAME,
    DOCKER_IMAGE_TAR_NAME,
    TEST_DIR_NAME,
)
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


def extract_package(workspace: Path, package: Path) -> Tuple[Path, Path, Path, Path]:
    """Extract the code and image tarballs from the mse package."""
    LOG.info("Extracting the package at %s...", workspace)

    with tarfile.open(package, "r") as f:
        f.extractall(path=workspace)

    code_tar_path = workspace / CODE_TAR_NAME
    image_tar_path = workspace / DOCKER_IMAGE_TAR_NAME
    code_config_path = workspace / CODE_CONFIG_NAME
    test_dir_path = workspace / TEST_DIR_NAME

    if not code_tar_path.exists():
        raise Exception(f"'{CODE_TAR_NAME}' was not found in the mse package")

    if not image_tar_path.exists():
        raise Exception(f"'{DOCKER_IMAGE_TAR_NAME}' was not found in the mse package")

    if not code_config_path.exists():
        raise Exception(f"'{CODE_CONFIG_NAME}' was not found in the mse package")

    if not test_dir_path.exists():
        raise Exception(f"'{TEST_DIR_NAME}' was not found in the mse package")

    return (code_tar_path, image_tar_path, test_dir_path, code_config_path)


def load_docker_image(image_tar_path: Path) -> str:
    """Load the docker image from the image tarball."""
    LOG.info("Loading the docker image...")
    client = get_client_docker()

    with open(image_tar_path, "rb") as f:
        image = client.images.load(f.read())
        return image[0].tags[0]
