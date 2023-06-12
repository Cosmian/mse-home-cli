"""mse_home.command.verify module."""

from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding
from mse_cli_core.enclave import verify_enclave

from mse_home.log import LOGGER as LOG
from mse_home.model.evidence import ApplicationEvidence


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "verify",
        help="Verify the trustworthiness of a running MSE web application "
        "and get the ratls certificate",
    )

    parser.add_argument(
        "--fingerprint",
        required=True,
        type=str,
        metavar="HEXDIGEST",
        help="Check the code fingerprint against specific SHA-256 hexdigest",
    )

    parser.add_argument(
        "--evidence",
        required=True,
        type=Path,
        metavar="FILE",
        help="The path to the evidence file",
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

    evidence = ApplicationEvidence.load(args.evidence)

    try:
        verify_enclave(
            evidence.signer_pk,
            evidence.ratls_certificate,
            args.fingerprint,
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

    LOG.info("The ratls certificate has been saved at: %s", ratls_cert_path)
