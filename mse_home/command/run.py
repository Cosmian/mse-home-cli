"""mse_home.command.run module."""

import json
from pathlib import Path
from typing import Any, Dict

from docker.errors import NotFound
from mse_cli_core.bootstrap import (
    ConfigurationPayload,
    is_waiting_for_secrets,
    send_secrets,
    wait_for_app_server,
)
from mse_cli_core.sgx_docker import SgxDockerConfig

from mse_home.command.helpers import get_client_docker
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "run",
        help="Finalise the configuration of the application "
        "docker and run the application code",
    )

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--secrets",
        type=Path,
        required=False,
        help="The secrets.json file path",
    )

    parser.add_argument(
        "--sealed-secrets",
        type=Path,
        required=False,
        help="The sealed secrets.json file path",
    )

    parser.add_argument(
        "--key",
        type=Path,
        required=False,
        help="The code decryption sealed key file path",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()

    try:
        container = client.containers.get(args.name)
    except NotFound as exc:
        raise Exception(
            f"Can't find the mse docker for application '{args.name}'"
        ) from exc

    docker = SgxDockerConfig.load(container.attrs, container.labels)

    if not is_waiting_for_secrets(f"https://localhost:{docker.port}", False):
        raise Exception(
            "Your application is not waiting for secrets. Have you already set it?"
        )

    data = ConfigurationPayload(
        app_id=docker.app_id,
        secrets=json.loads(args.secrets.read_text()) if args.secrets else None,
        sealed_secrets=args.sealed_secrets.read_bytes()
        if args.sealed_secrets
        else None,
        code_secret_key=args.key.read_bytes() if args.key else None,
    )

    LOG.info("Sending secrets to the application...")
    send_secrets(f"https://localhost:{docker.port}", data.payload(), False)
    LOG.info("Secrets sent!")

    LOG.info("Waiting for your application to be ready...")
    wait_for_app_server(f"https://localhost:{docker.port}", docker.healthcheck, False)
    LOG.info("Application ready!")
    LOG.info("Feel free to test it using the `msehome test` command")
