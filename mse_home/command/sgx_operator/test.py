"""mse_home.command.sgx_operator.test module."""

import os
import subprocess
import sys
from pathlib import Path

from mse_cli_core.bootstrap import is_waiting_for_secrets
from mse_cli_core.conf import AppConf, AppConfParsingOption
from mse_cli_core.sgx_docker import SgxDockerConfig

from mse_home.command.helpers import get_client_docker, get_running_app_container


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("test", help="Test a deployed MSE app")

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--test",
        type=Path,
        required=True,
        help="The path of the test directory extracted from the MSE package",
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="The conf path extracted from the MSE package",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()
    container = get_running_app_container(client, args.name)

    docker = SgxDockerConfig.load(container.attrs, container.labels)

    if is_waiting_for_secrets(f"https://localhost:{docker.port}"):
        raise Exception(
            "Your application is waiting for secrets and can't be tested right now."
        )

    code_config = AppConf.load(args.config, option=AppConfParsingOption.SkipCloud)

    for package in code_config.tests_requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    subprocess.check_call(
        code_config.tests_cmd,
        cwd=args.test,
        env=dict(os.environ, TEST_REMOTE_URL=f"https://localhost:{docker.port}"),
    )
