"""mse_home.command.stop module."""

from docker.errors import NotFound

from mse_home.command.helpers import get_client_docker
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("stop", help="Stop and remove a running MSE docker")

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the docker after stopped, preventing it to be restarted later",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()

    try:
        LOG.info("Stopping your application docker...")

        container = client.containers.get(args.name)
        container.stop(timeout=1)

        LOG.info("Docker '%s' has been stopped!", args.name)

        if args.remove:
            container.remove()
            LOG.info("Docker '%s' has been removed!", args.name)

    except NotFound as exc:
        raise Exception(f"Can't find mse docker '{args.name}'") from exc
