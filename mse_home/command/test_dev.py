"""mse_home.command.test_dev module."""

import subprocess
import sys
import time
from pathlib import Path

from docker.errors import BuildError

from mse_home.command.helpers import get_client_docker, is_ready
from mse_home.log import LOGGER as LOG
from mse_home.model.code import CodeConfig


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("test-dev", help="Test a mse app when developing it")

    parser.add_argument(
        "--code", type=Path, required=True, help="The path to the code to run"
    )

    parser.add_argument(
        "--dockerfile", type=Path, required=True, help="The path to the Dockerfile"
    )

    parser.add_argument(
        "--secrets",
        type=Path,
        required=False,
        help="The secrets.json file path",
    )

    parser.add_argument(
        "--tests",
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
    code_config = CodeConfig.load(args.config)
    docker_name = f"{code_config.name}:{time.time_ns()}"

    client = get_client_docker()

    try:
        LOG.info("Building your docker image...")

        # Build the docker
        client.images.build(
            path=str(args.dockerfile.parent),
            tag=docker_name,
        )

    except BuildError as exc:
        LOG.error("Failed to build your docker: %s", exc)
        raise exc

    LOG.info("Starting the docker: %s...", docker_name)

    command = ["--application", code_config.python_application, "--debug"]

    volumes = {
        f"{args.code.resolve()}": {"bind": "/mse-app", "mode": "rw"},
    }

    if args.secrets:
        volumes[f"{args.secrets.resolve()}"] = {
            "bind": "/root/.cache/mse/secrets.json",
            "mode": "rw",
        }

    port = 5000

    container = client.containers.run(
        docker_name,
        command=command,
        volumes=volumes,
        entrypoint="mse-test",
        ports={f"{port}/tcp": ("127.0.0.1", port)},
        remove=True,
        detach=True,
        stdout=True,
        stderr=True,
    )

    while not is_ready("http://localhost", port, code_config.healthcheck_endpoint):
        time.sleep(5)

    try:
        LOG.info("Installing tests requirements...")
        for package in code_config.tests_requirements:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

        LOG.info("Running tests...")
        subprocess.check_call(
            code_config.tests_cmd,
            cwd=args.tests,
        )

        LOG.error("Tests succeed!")
    except subprocess.CalledProcessError:
        LOG.error("Tests failed!")
    finally:
        container.stop(timeout=1)
