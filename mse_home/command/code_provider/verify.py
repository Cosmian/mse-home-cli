"""mse_home.command.code_provider.verify module."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import Certificate, CertificateRevocationList
from mse_cli_core.enclave import compute_mr_enclave, verify_enclave

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

    evidence = ApplicationEvidence.load(args.evidence)

    LOG.info("Extracting the package at %s...", workspace)
    package = CodePackage.extract(workspace, args.package)

    LOG.info("A log file is generating at: %s", log_path)

    client = get_client_docker()
    image = load_docker_image(client, package.image_tar)
    mrenclave = compute_mr_enclave(
        client,
        image,
        evidence.input_args,
        workspace,
        log_path,
    )

    LOG.info("Fingerprint is: %s", mrenclave)

    try:
        collaterals: Optional[
            Tuple[
                bytes,
                bytes,
                Certificate,
                CertificateRevocationList,
                CertificateRevocationList,
            ]
        ] = None

        if evidence.collaterals is not None:
            collaterals = (
                evidence.collaterals.tcb_info,
                evidence.collaterals.qe_identity,
                evidence.collaterals.tcb_cert,
                evidence.collaterals.root_ca_crl,
                evidence.collaterals.pck_platform_crl,
            )
        verify_enclave(
            signer_pk=evidence.signer_pk,
            ratls_certificate=evidence.ratls_certificate,
            fingerprint=mrenclave,
            collaterals=collaterals,
            pccs_url=None,
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

    # Clean up the workspace
    LOG.info("Cleaning up the temporary workspace...")
    shutil.rmtree(workspace)
