"""mse_home.command.logds module."""

from docker.errors import NotFound

from mse_home.command.helpers import get_client_docker
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

    try:
        container = client.containers.get(args.name)
        if args.follow:
            LOG.info("skipping...")
            for line in container.logs(tail=10, stream=True):
                LOG.info(line.decode("utf-8").strip())
        else:
            LOG.info(container.logs().decode("utf-8"))
    except NotFound as exc:
        raise Exception(f"Can't find mse docker '{args.name}'") from exc
