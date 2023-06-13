"""mse_home.command.verify module."""

import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding
from mse_cli_core.enclave import compute_mr_enclave, verify_enclave
from mse_cli_core.no_sgx_docker import NoSgxDockerConfig

from mse_home.command.helpers import get_client_docker, load_docker_image
from mse_home.log import LOGGER as LOG
from mse_home.model.evidence import ApplicationEvidence
from mse_home.model.package import CodePackage


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "verify",
        help="Verify the trustworthiness of a running MSE web application "
        "and get the RA-TLS certificate",
    )

    parser.add_argument(
        "--evidence",
        required=True,
        type=Path,
        metavar="FILE",
        help="The path to the evidence file",
    )

    parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="The MSE package containing the Docker images and the code",
    )

    parser.add_argument(
        "--args",
        type=str,
        required=True,
        help="The path to the enclave argument file generating when "
        "spawning the application (ex: `args.toml`)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path of the verified RA-TLS certificate",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    if not args.output.is_dir():
        raise NotADirectoryError(f"{args.output} does not exist")

    workspace = Path(tempfile.mkdtemp())
    log_path = workspace / "docker.log"

    app_args = NoSgxDockerConfig.load(args.args)

    LOG.info("Extracting the package at %s...", workspace)
    package = CodePackage.extract(workspace, args.package)

    client = get_client_docker()
    image = load_docker_image(client, package.image_tar)
    mrenclave = compute_mr_enclave(
        client,
        image,
        app_args,
        package.code_tar,
        log_path,
    )

    evidence = ApplicationEvidence.load(args.evidence)

    try:
        verify_enclave(
            evidence.signer_pk,
            evidence.ratls_certificate,
            fingerprint=mrenclave,
            collaterals=evidence.collaterals,
        )
    except Exception as exc:
        LOG.error("Verification failed!")
        raise exc

    LOG.info("Verification successful")

    ratls_cert_path = args.output.resolve() / "ratls.pem"
    ratls_cert_path.write_bytes(
        evidence.ratls_certificate.public_bytes(encoding=Encoding.PEM)
    )

    LOG.info("The RA-TLS certificate has been saved at: %s", ratls_cert_path)
