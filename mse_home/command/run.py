"""mse_home.command.run module."""

import json
import time
from pathlib import Path
from typing import Any, Dict

import requests
from docker.errors import NotFound

from mse_home.command.helpers import get_client_docker, is_waiting_for_secrets
from mse_home.conf.docker import DockerConfig
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

    docker = DockerConfig.load(container.attrs["Config"]["Cmd"], container.ports)

    if not is_waiting_for_secrets(docker.port):
        raise Exception(
            "Your application is not waiting for secrets. Have you already set it?"
        )

    data: Dict[str, Any] = {
        "uuid": docker.app_id,
    }

    if args.secrets:
        data["app_secrets"] = json.loads(args.secrets.read_text())

    if args.sealed_secrets:
        data["app_sealed_secrets"] = json.loads(args.sealed_secrets.read_text())

    if args.key:
        data["code_secret_key"] = args.key.read_text()

    send_secrets(data, docker.port)

    wait_for_app_to_be_ready(docker.port, container.labels["healthcheck_endpoint"])


def send_secrets(data: Dict[str, Any], port: int):
    """Send the secrets to the configuration server."""
    LOG.info("Sending secrets to the application...")

    r = requests.post(
        url=f"https://localhost:{port}/",
        json=data,
        headers={"Content-Type": "application/json"},
        verify=False,
        timeout=60,
    )

    if not r.ok:
        raise Exception(r.text)

    LOG.info("Secrets sent!")


def wait_for_app_to_be_ready(port: int, healthcheck_endpoint: str):
    """Hold on until the configuration server is stopped and the app starts."""
    LOG.info("Waiting for your application to be ready...")
    while True:
        try:
            response = requests.get(
                f"https://localhost:{port}{healthcheck_endpoint}",
                verify=False,
                timeout=5,
            )

            if response.status_code != 503 and "Mse-Status" not in response.headers:
                break

        except requests.exceptions.SSLError:
            pass

        time.sleep(10)

    LOG.info("Application ready!")
