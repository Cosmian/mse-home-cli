"""mse_home.command.evidence module."""

import socket
import ssl
from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding, load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from intel_sgx_ra.attest import retrieve_collaterals
from intel_sgx_ra.ratls import get_server_certificate, ratls_verify
from mse_cli_core.sgx_docker import SgxDockerConfig

from mse_home.command.helpers import get_app_container, get_client_docker
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
    container = get_app_container(client, args.name)

    docker = SgxDockerConfig.load(container.attrs, container.labels)

    # Get the certificate from the application
    try:
        ratls_cert = load_pem_x509_certificate(
            get_server_certificate(("localhost", docker.port)).encode("utf-8")
        )
    except (ssl.SSLZeroReturnError, socket.gaierror, ssl.SSLEOFError) as exc:
        raise ConnectionError(
            f"Can't reach localhost:{docker.port}. "
            "Are you sure the application is still running?"
        ) from exc

    quote = ratls_verify(ratls_cert)

    (tcb_info, tcb_cert, root_ca_crl, pck_platform_crl) = retrieve_collaterals(
        quote, args.pccs
    )

    signer_key = load_pem_private_key(
        docker.signer_key.read_bytes(),
        password=None,
    )

    evidence = ApplicationEvidence(
        ratls_certificate=ratls_cert,
        root_ca_crl=root_ca_crl,
        pck_platform_crl=pck_platform_crl,
        tcb_info=tcb_info,
        tcb_cert=tcb_cert,
        signer_pk=signer_key.public_key(),
    )

    evidence_path = args.output / "evidence.json"
    evidence.save(evidence_path)
    LOG.info("The evidence file has been generated at: %s", evidence_path)
    LOG.info("The evidence file can now be shared!")

    ratls_cert_path = args.output / "ratls.pem"
    ratls_cert_path.write_bytes(
        evidence.ratls_certificate.public_bytes(encoding=Encoding.PEM)
    )

    LOG.info("The ratls certificate has been saved at: %s", ratls_cert_path)
