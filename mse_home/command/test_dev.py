"""mse_home.command.test_dev module."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from docker.errors import BuildError, NotFound
from docker.models.containers import Container
from mse_cli_core.bootstrap import is_ready
from mse_cli_core.clock_tick import ClockTick
from mse_cli_core.test_docker import TestDockerConfig

from mse_home.command.helpers import get_client_docker
from mse_home.log import LOGGER as LOG
from mse_home.model.code import CodeConfig


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "test-dev", help="Test a MSE app in development context"
    )

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
        "--sealed-secrets",
        type=Path,
        required=False,
        help="The secrets.json to seal file path (unsealed for the test purpose)",
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
    if not args.code.is_dir():
        raise IOError(f"{args.code} does not exist")

    if not args.test.is_dir():
        raise IOError(f"{args.test} does not exist")

    if not args.dockerfile.is_file():
        raise IOError(f"{args.dockerfile} does not exist")

    if args.secrets and not args.secrets.is_file():
        raise IOError(f"{args.secrets} does not exist")

    if args.sealed_secrets and not args.sealed_secrets.is_file():
        raise IOError(f"{ args.sealed_secrets} does not exist")

    code_config = CodeConfig.load(args.config)
    container_name = docker_name = f"{code_config.name}_test"

    client = get_client_docker()

    build_test_docker(client, args.dockerfile, docker_name)

    LOG.info("Starting the docker: %s...", docker_name)
    docker_config = TestDockerConfig(
        code=args.code,
        application=code_config.python_application,
        secrets=args.secrets,
        sealed_secrets=args.sealed_secrets,
        port=5000,
    )

    success = False
    try:
        container = run_app_docker(
            client,
            docker_name,
            container_name,
            docker_config,
            code_config.healthcheck_endpoint,
        )

        success = run_tests(
            code_config,
            args.test,
            args.secrets,
            args.sealed_secrets,
        )

    except Exception as exc:
        raise exc
    finally:
        try:
            container = client.containers.get(container_name)
            if not success:
                LOG.info("The docker logs are:\n%s", container.logs().decode("utf-8"))
            container.stop(timeout=1)
            # We need to remove the container since we declare remove=False previously
            container.remove()
        except NotFound:
            pass


def run_app_docker(
    client,
    docker_name,
    container_name: str,
    docker_config: TestDockerConfig,
    healthcheck_endpoint: str,
) -> Container:
    """Run the app docker to test."""
    container = client.containers.run(
        docker_name,
        name=container_name,
        command=docker_config.cmd(),
        volumes=docker_config.volumes(),
        entrypoint=TestDockerConfig.entrypoint,
        ports=docker_config.ports(),
        detach=True,
        # We do not remove the container to be able to print the error (if some)
        remove=False,
    )

    clock = ClockTick(
        period=5,
        timeout=10,
        message="Test application docker is unreachable!",
    )

    while clock.tick():
        # Note: container.status is not actualized.
        # Get it again to have the current status
        container = client.containers.get(container_name)

        if container.status == "exited":
            raise Exception("Application docker fails to start")

        if is_ready(f"http://localhost:{docker_config.port}", healthcheck_endpoint):
            break

    return container


def run_tests(
    code_config: CodeConfig,
    tests: Path,
    secrets: Optional[Path],
    sealed_secrets: Optional[Path],
) -> bool:
    """Run the tests."""

    LOG.info("Installing tests requirements...")
    for package in code_config.tests_requirements:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package],
            stdout=subprocess.DEVNULL,
        )

    LOG.info("Running tests...")
    env = dict(os.environ)
    if secrets:
        env["TEST_SECRET_JSON"] = str(secrets.resolve())

    if sealed_secrets:
        env["TEST_SEALED_SECRET_JSON"] = str(sealed_secrets.resolve())

    try:
        subprocess.check_call(code_config.tests_cmd, cwd=tests, env=env)

        LOG.info("Tests successful")
        return True
    except subprocess.CalledProcessError:
        LOG.error("Tests failed!")

    return False


def build_test_docker(client, dockerfile: Path, docker_name: str):
    """Build the test docker."""

    try:
        LOG.info("Building your docker image...")

        # Build the docker
        client.images.build(
            path=str(dockerfile.parent),
            tag=docker_name,
        )
    except BuildError as exc:
        raise Exception(f"Failed to build your docker: {exc}") from exc
