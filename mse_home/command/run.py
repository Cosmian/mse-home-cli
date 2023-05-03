"""mse_home.command.run module."""


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("run", help="TODO")

    parser.set_defaults(func=run)


def run(_args) -> None:
    """Run the subcommand."""
