"""mse_home.command.spawn module."""


import datetime
import socket
import tarfile
import time
import uuid
from pathlib import Path
from typing import Tuple

import requests

from mse_home.command.helpers import get_client_docker, is_spawned
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("spawn", help="Spawn a MSE docker")

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="The MSE package containing the docker images and the code",
    )

    parser.add_argument(
        "--host",
        type=str,
        required=True,
        help="The common name of the generated certificate",
    )

    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="The number of days before the certificate expires",
    )

    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="The application port",
    )

    parser.add_argument(
        "--size",
        type=int,
        required=True,
        help="The enclave size to spawn",
    )

    parser.add_argument(  # TODO: Variable d'env?
        "--signer-key",
        type=Path,
        required=True,
        help="The enclave signer key",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""

    if is_spawned(args.name):
        raise Exception(
            f"Docker container {args.name} is already running. Stop it before restart it!"
        )

    if not is_port_free(args.port):
        raise Exception(f"Port {args.port} is already in-used!")

    workspace = Path(f"{args.name}_{time.time_ns()}").resolve()
    workspace.mkdir()

    (code_tar_path, image_tar_path) = extract_package(workspace, args.package)

    image = load_docker_image(image_tar_path)

    run_docker_image(
        args.name,
        image,
        args.days,
        args.host,
        args.port,
        args.size,
        code_tar_path,
        args.signer_key,
    )

    wait_for_docker_to_spawn(args.port)


def is_port_free(port: int):
    """Check whether a given `port` is free."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", port))
        sock.close()
    except OSError:
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


def run_docker_image(
    app_name: str,
    image: str,
    days: int,
    host: str,
    port: int,
    size: int,
    code_tar_path: Path,
    signer_key: Path,
):
    """Run the mse docker."""
    client = get_client_docker()

    cert_expiration_date = datetime.datetime.today() + datetime.timedelta(days=days)

    # Run l'image
    command = [
        "--size",
        f"{size}M",
        "--code",
        "/tmp/app.tar",
        "--host",
        host,
        "--uuid",
        "ee08d973-a58f-4944-ae12-2b105bc9a15c",
        # str(
        #     uuid.uuid4()
        # ),  # TODO: what to do with that: at the install save it in a env variable
        "--application",
        "app:app",
        "--timeout",
        str(int(cert_expiration_date.timestamp())),  # TODO: Remove that argument
        "--self-signed",
        str(int(cert_expiration_date.timestamp())),
    ]

    volumes = {
        f"{code_tar_path}": {"bind": "/tmp/app.tar", "mode": "rw"},
        "/var/run/aesmd": {"bind": "/var/run/aesmd", "mode": "rw"},
        f"{signer_key}": {
            "bind": "/root/.config/gramine/enclave-key.pem",
            "mode": "rw",
        },
    }

    LOG.info("Starting the docker...")

    container = client.containers.run(
        image,
        name=app_name,
        command=command,
        volumes=volumes,
        devices=[
            "/dev/sgx_enclave:/dev/sgx_enclave:rw",
            "/dev/sgx_provision:/dev/sgx_enclave:rw",
            "/dev/sgx/enclave:/dev/sgx_enclave:rw",
            "/dev/sgx/provision:/dev/sgx_enclave:rw",
        ],
        ports={f"443/tcp": ("127.0.0.1", str(port))},
        entrypoint="mse-run",
        remove=True,
        detach=True,
        stdout=True,
        stderr=True,
    )

    if container.status != "created":
        raise Exception(
            f"Can't create the container: {container.status} - {container.logs()}"
        )


def wait_for_docker_to_spawn(port: int):
    """Hold on until the configuration server is up and listing."""
    LOG.info("Waiting for configuration server to be ready...")
    while True:
        try:
            response = requests.get(f"https://localhost:{port}/", verify=False)

            if response.status_code == 200 and "Mse-Status" in response.headers:
                break
        except requests.exceptions.SSLError:
            pass

        time.sleep(10)

    LOG.info("The application is now ready to receive the secrets!")
