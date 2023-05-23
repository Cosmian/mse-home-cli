"""mse_home.command.fingerprint module."""


import re
import tempfile
import uuid
from pathlib import Path

from mse_home.command.helpers import get_client_docker, load_docker_image
from mse_home.log import LOGGER as LOG
from mse_home.model.args import ApplicationArguments
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

    app_args = ApplicationArguments.load(args.args)

    LOG.info("Extracting the package at %s...", workspace)
    package = CodePackage.extract(workspace, args.package)
    image = load_docker_image(package.image_tar)

    mrenclave = compute_mr_enclave(
        image,
        app_args,
        package.code_tar,
        log_path,
    )

    LOG.info("Fingerprint is: %s", mrenclave)


# TODO: merge with mse-cli
def compute_mr_enclave(
    image: str,
    app_args: ApplicationArguments,
    code_tar_path: Path,
    docker_path_log: Path,
) -> str:
    """Compute the MR enclave of an enclave."""
    client = get_client_docker()

    container = client.containers.run(
        image,
        command=app_args.cmd(),
        volumes=app_args.volumes(code_tar_path),
        entrypoint=ApplicationArguments.entrypoint,
        remove=True,
        detach=False,
        stdout=True,
        stderr=True,
    )

    # Save the docker output
    docker_path_log.write_bytes(container)

    # Get the mr_enclave from the docker output
    pattern = "Measurement:\n[ ]*([a-z0-9]{64})"
    m = re.search(pattern.encode("utf-8"), container)

    if not m:
        raise Exception(
            f"Fail to compute mr_enclave! See {docker_path_log} for more details."
        )

    return str(m.group(1).decode("utf-8"))
