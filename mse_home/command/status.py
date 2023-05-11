"""mse_home.command.status module."""

from datetime import datetime

import requests
from docker.errors import NotFound

from mse_home.command.helpers import get_client_docker
from mse_home.conf.docker import DockerConfig
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("status", help="Print the MSE docker status")

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
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

    expires_at = datetime.fromtimestamp(docker.self_signed)
    remaining_days = expires_at - datetime.now()

    LOG.info("    App name = %s", args.name)
    LOG.info("Enclave size = %dM", docker.size)
    LOG.info(" Common name = %s", docker.host)
    LOG.info("        Port = %d", docker.port)
    LOG.info(" Healthcheck = %s", container.labels["healthcheck_endpoint"])
    LOG.info(
        "      Status = %s",
        app_state(docker.port, container.labels["healthcheck_endpoint"])
        if container.status == "running"
        else container.status,
    )
    LOG.info(
        "  Started at = %s",
        container.attrs["State"]["StartedAt"],
    )
    LOG.info(
        "  Expires at = %s (%d days remaining)",
        expires_at.astimezone(),
        remaining_days.days,
    )


def app_state(port: int, healthcheck_endpoint: str) -> str:
    """Determine the application state by querying it."""
    try:
        # Note: the configuration server allows any path
        # So: `healthcheck_endpoint`` does not exist but it's process as /
        # We can there do one query for the application and the configuration server
        response = requests.get(
            f"https://localhost:{port}{healthcheck_endpoint}",
            verify=False,
            timeout=60,
        )

        if response.status_code == 503:
            return "initializing"

        if response.status_code == 500:
            return "on error"

        if response.status_code == 200 and "Mse-Status" in response.headers:
            return "waiting secret keys"

        if response.status_code == 200:
            return "running"

        return "unknown"

    except requests.exceptions.SSLError:
        return "initializing"
