"""mse_home.command.test module."""

import os
import subprocess
import sys
from pathlib import Path

from docker.errors import NotFound

from mse_home.command.helpers import get_client_docker, is_waiting_for_secrets
from mse_home.model.code import CodeConfig
from mse_home.model.docker import DockerConfig


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("test", help="Test a deployed mse app")

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--test",
        type=Path,
        required=True,
        help="The path of the test directory extracted from the mse package",
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="The conf path extracted from the mse package",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()

    try:
        container = client.containers.get(args.name)
    except NotFound as exc:
        raise Exception(
            f"Can't find the mse docker for application '{args.name}'"
        ) from exc

    docker = DockerConfig.load(
        container.attrs["Config"]["Cmd"], container.attrs["HostConfig"]["PortBindings"]
    )

    if is_waiting_for_secrets(docker.port):
        raise Exception(
            "Your application is waiting for secrets and can't be tested right now."
        )

    code_config = CodeConfig.load(args.config)

    for package in code_config.tests_requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    subprocess.check_call(
        code_config.tests_cmd,
        cwd=args.test,
        env=dict(os.environ, TEST_REMOTE_URL=f"https://localhost:{docker.port}"),
    )
