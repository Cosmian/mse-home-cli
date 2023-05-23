"""mse_home.command.fingerprint module."""

import tempfile
from pathlib import Path

from mse_cli_core.enclave import compute_mr_enclave
from mse_cli_core.no_sgx_docker import NoSgxDockerConfig

from mse_home.command.helpers import get_client_docker, load_docker_image
from mse_home.log import LOGGER as LOG
from mse_home.model.package import CodePackage


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser("fingerprint", help="Compute the code fingerprint")

    parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="The MSE package containing the docker images and the code",
    )

    parser.add_argument(
        "--args",
        type=str,
        required=True,
        help="The path to the enclave argument file generating when "
        "spawning the application (ex: args.toml)",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    workspace = Path(tempfile.mkdtemp())
    log_path = workspace / "docker.log"

    app_args = NoSgxDockerConfig.load(args.args)

    LOG.info("Extracting the package at %s...", workspace)
    package = CodePackage.extract(workspace, args.package)
    image = load_docker_image(package.image_tar)

    client = get_client_docker()

    mrenclave = compute_mr_enclave(
        client,
        image,
        app_args,
        package.code_tar,
        log_path,
    )

    LOG.info("Fingerprint is: %s", mrenclave)
