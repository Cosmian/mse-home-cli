"""mse_home.command.spawn module."""


import socket
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from mse_home import DOCKER_LABEL
from mse_home.command.helpers import (
    extract_package,
    get_client_docker,
    is_spawned,
    is_waiting_for_secrets,
    load_docker_image,
)
from mse_home.conf.args import ApplicationArguments
from mse_home.conf.code import CodeConfig
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
        help="The MSE application package containing the docker images and the code",
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

    parser.add_argument(
        "--signer-key",
        type=Path,
        required=True,
        help="The enclave signer key",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="The directory to write the args file",
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

    workspace = args.output.resolve()

    (code_tar_path, image_tar_path, code_config_path) = extract_package(
        workspace, args.package
    )

    code_config = CodeConfig.load(code_config_path)

    image = load_docker_image(image_tar_path)

    cert_expiration_date = datetime.today() + timedelta(days=args.days)
    app_id = uuid4()

    run_docker_image(
        args.name,
        image,
        cert_expiration_date,
        args.host,
        args.port,
        args.size,
        app_id,
        code_config.python_application,
        code_config.healthcheck_endpoint,
        code_tar_path,
        args.signer_key,
    )

    wait_for_docker_to_spawn(args.port)

    app_args = ApplicationArguments(
        host=args.host,
        expiration_date=int(cert_expiration_date.timestamp()),
        size=args.size,
        app_id=str(app_id),
        application=code_config.python_application,
    )

    args_path = workspace / "args.toml"
    LOG.info("You can share '%s' with the other participants.", args_path)
    app_args.save(args_path)


def is_port_free(port: int):
    """Check whether a given `port` is free."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", port))
        sock.close()
    except OSError:
        return False

    return True


def run_docker_image(
    app_name: str,
    image: str,
    expiration_date: datetime,
    host: str,
    port: int,
    size: int,
    app_id: UUID,
    application: str,
    healthcheck: str,
    code_tar_path: Path,
    signer_key: Path,
):
    """Run the mse docker."""
    client = get_client_docker()

    # Run l'image
    command = [
        "--size",
        f"{size}M",
        "--code",
        "/tmp/app.tar",
        "--host",
        host,
        "--uuid",
        str(app_id),
        "--application",
        application,
        "--timeout",
        str(int(expiration_date.timestamp())),
        "--self-signed",
        str(int(expiration_date.timestamp())),
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
        ports={"443/tcp": ("127.0.0.1", str(port))},
        entrypoint="mse-run",
        labels={DOCKER_LABEL: "1", "healthcheck_endpoint": healthcheck},
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
    while not is_waiting_for_secrets(port):
        time.sleep(10)

    LOG.info("The application is now ready to receive the secrets!")
