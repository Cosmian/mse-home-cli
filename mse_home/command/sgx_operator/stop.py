"""mse_home.command.stop module."""

from mse_home.command.helpers import get_app_container, get_client_docker
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "stop", help="Stop and optionally remove a running MSE docker"
    )

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the docker after being stopped, preventing it to be restarted later",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()
    container = get_app_container(client, args.name)

    LOG.info("Stopping your application docker...")
    container.stop(timeout=1)

    LOG.info("Docker '%s' has been stopped!", args.name)

    if args.remove:
        container.remove()
        LOG.info("Docker '%s' has been removed!", args.name)
