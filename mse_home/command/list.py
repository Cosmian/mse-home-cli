"""mse_home.command.list module."""

from mse_home import DOCKER_LABEL
from mse_home.command.helpers import get_client_docker
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("list", help="List the running MSE applications")

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()

    containers = client.containers.list(filters={"label": DOCKER_LABEL})

    LOG.info("\n %s | %s [Image name] ", "Started at".center(29), "Application name")
    LOG.info(("-" * 65))

    for container in containers:
        LOG.info(
            "%s | %s [%s]",
            container.attrs["State"]["StartedAt"],
            container.name,
            container.image.tags[0],
        )
