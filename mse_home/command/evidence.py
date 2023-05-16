"""mse_home.command.evidence module."""

import socket
import ssl
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import CertificateRevocationList, load_pem_x509_certificate
from docker.errors import NotFound
from intel_sgx_ra.pcs import get_pck_cert_crl, get_root_ca_crl
from intel_sgx_ra.ratls import get_server_certificate

from mse_home.command.helpers import get_client_docker
from mse_home.log import LOGGER as LOG
from mse_home.model.evidence import ApplicationEvidence


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "evidence",
        help="Collect the evidences to verify on offline mode "
        "the application and the enclave",
    )

    parser.add_argument(
        "--pccs",
        type=str,
        required=True,
        help="URL to the PCCS (ex: https://pccs.example.com)",
    )

    parser.add_argument(
        "--signer-key",
        type=Path,
        required=True,
        help="The enclave signer key",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="The directory to write the evidence file",
    )

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    client = get_client_docker()

    try:
        container = client.containers.get(args.name)
    except NotFound as exc:
        raise Exception(
            f"Can't find the mse docker for application '{args.name}'"
        ) from exc

    # Get the certificate from the application
    try:
        ratls_cert = load_pem_x509_certificate(
            get_server_certificate(("localhost", container.ports)).encode("utf-8")
        )
    except (ssl.SSLZeroReturnError, socket.gaierror, ssl.SSLEOFError) as exc:
        raise ConnectionError(
            f"Can't reach localhost:{container.ports}. "
            "Are you sure the application is still running?"
        ) from exc

    root_ca_crl: CertificateRevocationList = get_root_ca_crl(args.pccs)
    pck_platform_crl: CertificateRevocationList = get_pck_cert_crl(
        args.pccs, "platform"
    )
    pck_processor_crl: CertificateRevocationList = get_pck_cert_crl(
        args.pccs, "processor"
    )

    signer_key = load_pem_private_key(
        args.signer_key.read_bytes(),
        password=None,
    )

    evidence = ApplicationEvidence(
        ratls_certificate=ratls_cert,
        root_ca_crl=root_ca_crl,
        pck_platform_crl=pck_platform_crl,
        pck_processor_crl=pck_processor_crl,
        tcb_info=None,
        signer_pk=signer_key.public_key(),
    )

    evidence_path = args.output / "evidence.json"

    evidence.save(evidence_path)

    LOG.info("The evidence file has been generated at: %s", evidence_path)
