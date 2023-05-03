"""mse_home.command.fingerprint module."""


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("fingerprint", help="TODO")

    parser.set_defaults(func=run)


def run(_args) -> None:
    """Run the subcommand."""
