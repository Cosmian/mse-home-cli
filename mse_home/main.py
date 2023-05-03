"""mse_home.main module."""

import argparse
from warnings import filterwarnings  # noqa: E402

filterwarnings("ignore")  # noqa: E402

# pylint: disable=wrong-import-position
from mse_home import __version__

from mse_home.command import (
    build,
    decrypt,
    encrypt,
    evidence,
    fingerprint,
    init,
    run,
    seal,
    spawn,
    stop,
    verify,
)
from mse_home.log import LOGGER as LOG


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

    build.add_subparser(subparsers)
    decrypt.add_subparser(subparsers)
    encrypt.add_subparser(subparsers)
    evidence.add_subparser(subparsers)
    fingerprint.add_subparser(subparsers)
    init.add_subparser(subparsers)
    run.add_subparser(subparsers)
    seal.add_subparser(subparsers)
    spawn.add_subparser(subparsers)
    stop.add_subparser(subparsers)
    verify.add_subparser(subparsers)

    args = parser.parse_args()

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
