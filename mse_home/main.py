"""mse_home.main module."""

import argparse
from warnings import filterwarnings  # noqa: E402

filterwarnings("ignore")  # noqa: E402

# pylint: disable=wrong-import-position
from mse_home import __version__
from mse_home.command import (
    decrypt,
    evidence,
    list_all,
    logs,
    package,
    restart,
    run,
    scaffold,
    seal,
    spawn,
    status,
    stop,
    test,
    test_dev,
    verify,
)
from mse_home.log import LOGGER as LOG
from mse_home.log import setup_logging


def main() -> int:
    """Entrypoint of the CLI."""
    parser = argparse.ArgumentParser(
        description="Microservice Encryption Home CLI" f" - {__version__}"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"{__version__}",
        help="version of %(prog)s binary",
    )

    subparsers = parser.add_subparsers(title="subcommands")

    decrypt.add_subparser(subparsers)
    evidence.add_subparser(subparsers)
    scaffold.add_subparser(subparsers)
    list_all.add_subparser(subparsers)
    logs.add_subparser(subparsers)
    package.add_subparser(subparsers)
    restart.add_subparser(subparsers)
    run.add_subparser(subparsers)
    status.add_subparser(subparsers)
    seal.add_subparser(subparsers)
    spawn.add_subparser(subparsers)
    stop.add_subparser(subparsers)
    test.add_subparser(subparsers)
    test_dev.add_subparser(subparsers)
    verify.add_subparser(subparsers)

    args = parser.parse_args()

    setup_logging()

    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")

    try:
        func(args)
        return 0
    # pylint: disable=broad-except
    except Exception as e:
        LOG.error(e)
        return 1


if __name__ == "__main__":
    main()
