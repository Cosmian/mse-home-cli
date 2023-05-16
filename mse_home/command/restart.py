"""mse_home.command.stop module."""

from docker.errors import NotFound

from mse_home.command.helpers import get_client_docker
from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("restart", help="Restart an stopped MSE docker")

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
        LOG.info("Restarting your application docker...")

        container = client.containers.get(args.name)
        container.restart()

        LOG.info("Docker '%s' is now restarted!", args.name)
    except NotFound as exc:
        raise Exception(f"Can't find mse docker '{args.name}'") from exc
