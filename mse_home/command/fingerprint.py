"""mse_home.command.fingerprint module."""


import tempfile
import uuid
from pathlib import Path

from mse_cli_utils.enclave import compute_mr_enclave

from mse_home.command.helpers import extract_package, load_docker_image
from mse_home.conf.args import ApplicationArguments
from mse_home.log import LOGGER as LOG


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

    app_args = ApplicationArguments.load(args.args)

    (code_tar_path, image_tar_path, _) = extract_package(workspace, args.package)
    image = load_docker_image(image_tar_path)

    mrenclave = compute_mr_enclave(
        image,
        app_args.size,
        app_args.host,
        uuid.UUID(app_args.app_id),
        app_args.application,
        code_tar_path,
        app_args.expiration_date,
        None,
        log_path,
    )

    LOG.info("Fingerprint is: %s", mrenclave)
