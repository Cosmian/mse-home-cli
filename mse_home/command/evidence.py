"""mse_home.command.evidence module."""


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("evidence", help="TODO")

    parser.set_defaults(func=run)


def run(_args) -> None:
    """Run the subcommand."""
