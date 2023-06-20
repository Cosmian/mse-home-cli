"""mse_home.command.spawn module."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from docker.client import DockerClient
from docker.models.containers import Container
from mse_cli_core.bootstrap import wait_for_conf_server
from mse_cli_core.clock_tick import ClockTick
from mse_cli_core.sgx_docker import SgxDockerConfig
from mse_cli_core.spinner import Spinner

from mse_home.command.evidence import collect_evidence_and_certificate
from mse_home.command.helpers import (
    app_container_exists,
    get_app_container,
    get_client_docker,
    get_running_app_container,
    is_port_free,
    is_valid_enclave_size,
    load_docker_image,
)
from mse_home.log import LOGGER as LOG
from mse_home.model.code import CodeConfig
from mse_home.model.package import CodePackage


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
        help="The number of days before the certificate expires",
        default=365,
    )

    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="The application port",
    )

    parser.add_argument(
        "--size",
        type=is_valid_enclave_size,
        required=True,
        help="The enclave size to spawn (must be a power of 2)",
    )

    parser.add_argument(
        "--signer-key",
        type=Path,
        help="The enclave signer key",
        default=f"{os.getenv('HOME', '/root')}/.config/gramine/enclave-key.pem",
    )

    parser.add_argument(
        "--pccs",
        type=str,
        required=True,
        help="URL to the PCCS (ex: https://pccs.example.com)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        required=False,
        default=24 * 60,
        help="Stop the deployment if the application does not "
        "response after a delay (in min). (Default: 1440 min)",
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
    client = get_client_docker()

    if app_container_exists(client, args.name):
        raise Exception(
            f"Docker container `{args.name}` is already running. "
            "Stop and remove it before respawn it!"
        )

    if not is_port_free(args.port):
        raise Exception(f"Port {args.port} is already in-used!")

    workspace = args.output.resolve()

    LOG.info("Extracting the package at %s...", workspace)
    package = CodePackage.extract(workspace, args.package)
    code_config = CodeConfig.load(package.config_path)

    image = load_docker_image(client, package.image_tar)

    docker_config = SgxDockerConfig(
        size=args.size,
        host=args.host,
        port=args.port,
        app_id=uuid4(),
        expiration_date=int((datetime.today() + timedelta(days=args.days)).timestamp()),
        code=package.code_tar,
        application=code_config.python_application,
        healthcheck=code_config.healthcheck_endpoint,
        signer_key=args.signer_key,
    )

    run_docker_image(
        client,
        args.name,
        image,
        docker_config,
    )

    with Spinner("Waiting for the configuration server to be ready... "):
        wait_for_conf_server(
            ClockTick(
                period=5,
                timeout=args.timeout,
                message="The configuration server is unreachable!",
            ),
            f"https://localhost:{args.port}",
            False,
            get_running_app_container,
            (
                client,
                args.name,
            ),
        )
    LOG.info("The application is now ready to receive the secrets!")

    # Generate evidence and RA-TLS certificate files
    container: Container = get_app_container(client, args.name)

    collect_evidence_and_certificate(container, args.pccs, args.output)


def run_docker_image(
    client: DockerClient,
    app_name: str,
    image: str,
    docker_config: SgxDockerConfig,
):
    """Run the mse docker."""
    LOG.info("Starting the docker...")
    container = client.containers.run(
        image,
        name=app_name,
        command=docker_config.cmd(),
        volumes=docker_config.volumes(),
        devices=SgxDockerConfig.devices(),
        ports=docker_config.ports(),
        entrypoint=SgxDockerConfig.entrypoint,
        labels=docker_config.labels(),
        remove=False,
        detach=True,
        stdout=True,
        stderr=True,
    )

    if container.status != "created":
        raise Exception(
            f"Can't create the container: {container.status} - {container.logs()}"
        )