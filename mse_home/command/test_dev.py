"""mse_home.command.test_dev module."""

import os
import subprocess
import sys
import time
from pathlib import Path

from docker.errors import BuildError
from mse_cli_utils.clock_tick import ClockTick

from mse_home.command.helpers import get_client_docker, is_ready, is_spawned
from mse_home.log import LOGGER as LOG
from mse_home.model.code import CodeConfig
from mse_home.model.test_docker import TestDockerConfig


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
        "--sealed-secrets",
        type=Path,
        required=False,
        help="The secrets.json to seal file path (unsealed for the test purpose)",
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
    code_path = args.code.resolve()
    if not code_path.is_dir():
        raise IOError(f"{code_path} does not exist")

    test_path: Path = args.test.resolve()
    if not test_path.is_dir():
        raise IOError(f"{test_path} does not exist")

    dockerfile_path: Path = args.dockerfile.resolve()
    if not dockerfile_path.is_file():
        raise IOError(f"{dockerfile_path} does not exist")

    if args.secrets:
        secrets_path: Path = args.secrets.resolve()
        if not secrets_path.is_file():
            raise IOError(f"{secrets_path} does not exist")

    if args.sealed_secrets:
        sealed_secrets_path: Path = args.sealed_secrets.resolve()
        if not sealed_secrets_path.is_file():
            raise IOError(f"{sealed_secrets_path} does not exist")

    code_config = CodeConfig.load(args.config)
    now = time.time_ns()
    docker_name = f"{code_config.name}:{now}"
    container_name = f"{code_config.name}_{now}"

    client = get_client_docker()

    try:
        LOG.info("Building your docker image...")

        # Build the docker
        client.images.build(
            path=str(args.dockerfile.parent),
            tag=docker_name,
        )
    except BuildError as exc:
        raise Exception(f"Failed to build your docker: {exc}") from exc

    LOG.info("Starting the docker: %s...", docker_name)

    docker_config = TestDockerConfig(
        code=code_path,
        application=code_config.python_application,
        sealed_secrets=sealed_secrets_path,
        secrets=secrets_path,
        port=5000,
    )

    container = client.containers.run(
        docker_name,
        name=container_name,
        command=docker_config.cmd(),
        volumes=docker_config.volumes(),
        entrypoint=TestDockerConfig.entrypoint,
        ports=docker_config.ports(),
        detach=True,
        remove=False,  # We do not remove the container to be able to print the error (if some)
    )

    clock = ClockTick(
        period=5,
        timeout=10,
        message="Test application docker is unreachable!",
    )

    try:
        while clock.tick():
            # Note: container.status is not actualized. Get it again to have the current status
            if client.containers.get(container_name).status == "exited":
                raise Exception(
                    f"Application docker fails to start with the following error:\n{container.logs().decode('utf-8')}"
                )

            if is_ready(
                "http://localhost", docker_config.port, code_config.healthcheck_endpoint
            ):
                break

        LOG.info("Installing tests requirements...")
        for package in code_config.tests_requirements:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package],
                stdout=subprocess.DEVNULL,
            )

        LOG.info("Running tests...")
        env = dict(os.environ)
        if args.secrets:
            env["TEST_SECRET_JSON"] = str(secrets_path)

        if args.sealed_secrets:
            env["TEST_SEALED_SECRET_JSON"] = str(sealed_secrets_path)

        subprocess.check_call(code_config.tests_cmd, cwd=args.test, env=env)

        LOG.info("Tests succeed!")
    except subprocess.CalledProcessError:
        LOG.error("Tests failed! The docker logs are:")
        print(container.logs().decode("utf-8"))
    except Exception as exc:
        raise exc
    finally:
        container.stop(timeout=1)
        # We need to remove the container since we declare remove=False previously
        container.remove()
