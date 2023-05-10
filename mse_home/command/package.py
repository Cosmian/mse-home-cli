"""mse_home.command.package module."""

import shutil
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

from docker import from_env
from docker.client import DockerClient
from docker.errors import BuildError, DockerException
from mse_cli_utils.fs import tar, whilelist
from mse_lib_crypto.xsalsa20_poly1305 import encrypt_directory, random_key
from mse_home.command.helpers import get_client_docker

from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "package",
        help="Generate a package containing the docker image and the code to run on MSE",
    )

    # TODO: add a new argument: --name to give the name of the docker image?

    parser.add_argument(
        "--code", type=Path, required=True, help="The path to the code to include"
    )

    parser.add_argument(
        "--dockerfile", type=Path, required=True, help="The path to the Dockerfile"
    )

    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt the code directory inside the generated package",
    )

    parser.add_argument(
        "--output", type=Path, required=True, help="The directory to write the package"
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""

    code_path = args.code.resolve()
    if not code_path.is_dir():
        raise IOError(f"{code_path} does not exist")

    workspace = Path(tempfile.mkdtemp())

    package_path: Path = args.output.resolve()
    if not package_path.is_dir():
        raise IOError(f"{package_path} does not exist")

    app_name = code_path.name

    code_tar_path = workspace / "code.tar"
    image_tar_path = workspace / "image.tar"
    package_path = package_path / f"package_{app_name}_{time.time_ns()}.tar"

    LOG.info("A workspace has been created at: %s", str(workspace))

    create_code_tar(code_path, code_tar_path, args.encrypt)
    create_image_tar(args.dockerfile.resolve(), app_name, image_tar_path)

    create_package(code_tar_path, image_tar_path, package_path)
    # TODO: save the key and nounce in the context file

    LOG.info("Your package is now ready to be shared: %s", package_path)

    # Clean up the workspace
    shutil.rmtree(workspace)


def create_code_tar(
    code_path: Path, output_tar_path: Path, encrypt_code: bool
) -> Optional[Tuple[bytes, Dict[str, bytes]]]:
    """Create the tarball for the code directory."""
    if encrypt_code:
        LOG.info("Encrypting your code...")

        # Generate the key to encrypt the code
        secret_key = random_key()

        encrypted_path = output_tar_path.parent / "encrypted_code"

        # Encrypt the code directory
        nounces = encrypt_directory(
            dir_path=code_path,
            pattern="*",
            key=secret_key,
            nonces=None,
            exceptions=whilelist(),
            ignore_patterns=[],  # TODO
            out_dir_path=encrypted_path,
        )

        LOG.info("Your encryption key is: %s", bytes(secret_key).hex())
        LOG.info("Building the code archive...")

        # Generate the tarball
        tar(dir_path=encrypted_path, tar_path=output_tar_path)

        return (secret_key, nounces)
    else:
        LOG.info("Building the code archive...")

        # Generate the tarball
        tar(dir_path=code_path, tar_path=output_tar_path)
        # TODO: ignore files...

        return None


def create_image_tar(dockerfile: Path, image_name: str, output_tar_path: Path):
    """Build the docker image and export it into a tarball."""
    client = get_client_docker()

    try:
        LOG.info("Building your docker image...")

        # Build the docker
        (image, streamer) = client.images.build(
            path=str(dockerfile.parent),
            tag=image_name,  # TODO: put date in the tag name
        )

        # for chunk in streamer:
        #     if "stream" in chunk:
        #         for line in chunk["stream"].splitlines():
        #             LOG.info(line)

        LOG.info("Building the image archive...")

        # Save it as a tarball
        with open(output_tar_path, "wb") as f:
            for chunk in image.save(named=True):
                f.write(chunk)

    except BuildError as exc:
        LOG.error("Failed to build your docker: %s", exc)
        raise exc


def create_package(code_tar: Path, image_tar: Path, output_tar: Path):
    """Create the package containing the code and docker image tarballs."""
    LOG.info("Creating the final package...")

    with tarfile.open(output_tar, "w:") as tar_file:
        tar_file.add(code_tar, code_tar.name)
        tar_file.add(image_tar, image_tar.name)
