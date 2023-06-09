"""mse_home.command.test_dev module."""

import argparse
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

from mse_home.command.helpers import assert_is_dir, assert_is_file, get_client_docker
from mse_home.log import LOGGER as LOG
from mse_home.model.code import CodeConfig


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "test-dev", help="Test a MSE app in a development context"
    )

    parser.add_argument(
        "--project", type=Path, required=False, help="The path of the project to test"
    )

    parser.add_argument(
        "--code", type=Path, required=False, help="The path to the code to run"
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=False,
        help="The conf path extracted from the MSE package",
    )

    parser.add_argument(
        "--dockerfile", type=Path, required=False, help="The path to the Dockerfile"
    )

    parser.add_argument(
        "--test",
        type=Path,
        required=False,
        help="The path of the test directory extracted from the MSE package",
    )

    parser.add_argument(
        "--secrets",
        type=Path,
        required=False,
        help="The `secrets.json` file path",
    )

    parser.add_argument(
        "--sealed-secrets",
        type=Path,
        required=False,
        help="The secrets JSON to seal file path (unsealed for the test purpose)",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    code_path: Path
    test_path: Path
    config_path: Path
    dockerfile_path: Path
    secrets_path: Optional[Path]
    sealed_secrets_path: Optional[Path]

    if args.project:
        if any([args.code, args.config, args.dockerfile, args.test]):
            raise argparse.ArgumentTypeError(
                "[--project] and [--code & --config & --dockerfile & --test] "
                "are mutually exclusive"
            )

        assert_is_dir(args.project)

        code_path = args.project / "mse_src"
        test_path = args.project / "tests"
        config_path = args.project / "code.toml"
        dockerfile_path = args.project / "Dockerfile"
        secrets_path = args.project / "secrets.json"
        sealed_secrets_path = args.project / "secrets_to_seal.json"

    else:
        if not all([args.code, args.config, args.dockerfile, args.test]):
            raise argparse.ArgumentTypeError(
                "the following arguments are required: "
                "--code, --dockerfile, --test, --config\n"
                "the following arguments remain optional: "
                "[--secrets], [--sealed-secrets]"
            )

        code_path = args.code
        test_path = args.test
        config_path = args.config
        dockerfile_path = args.dockerfile
        secrets_path = args.secrets
        sealed_secrets_path = args.sealed_secrets

    assert_is_dir(code_path)
    assert_is_dir(test_path)
    assert_is_file(config_path)
    assert_is_file(dockerfile_path)
    if secrets_path:
        assert_is_file(secrets_path)
    if sealed_secrets_path:
        assert_is_file(sealed_secrets_path)

    code_config = CodeConfig.load(config_path)
    container_name = docker_name = f"{code_config.name}_test"

    client = get_client_docker()

    build_test_docker(client, dockerfile_path, docker_name)

    LOG.info("Starting the docker: %s...", docker_name)
    docker_config = TestDockerConfig(
        code=code_path,
        application=code_config.python_application,
        secrets=secrets_path,
        sealed_secrets=sealed_secrets_path,
        port=5000,
    )

    try_run(
        code_config,
        client,
        docker_name,
        container_name,
        docker_config,
        test_path,
        secrets_path,
        sealed_secrets_path,
    )


def try_run(
    code_config: CodeConfig,
    client,
    docker_name,
    container_name: str,
    docker_config: TestDockerConfig,
    test_path: Path,
    secrets_path: Optional[Path],
    sealed_secrets_path: Optional[Path],
):
    """Try to start the app docker to test"""
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
            test_path,
            secrets_path,
            sealed_secrets_path,
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
