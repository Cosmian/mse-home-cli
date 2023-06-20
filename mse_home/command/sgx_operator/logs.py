"""mse_home.command.logds module."""

from mse_home.command.helpers import get_app_container, get_client_docker
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("logs", help="Print the MSE docker logs")

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Follow log output",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()
    container = get_app_container(client, args.name)

    if args.follow:
        LOG.info("skipping...")
        for line in container.logs(tail=10, stream=True):
            LOG.info(line.decode("utf-8").strip())
    else:
        LOG.info(container.logs().decode("utf-8"))
