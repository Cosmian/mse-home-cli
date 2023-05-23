"""mse_home.command.verify module."""


from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding
from intel_sgx_ra.attest import remote_attestation
from intel_sgx_ra.ratls import ratls_verification
from intel_sgx_ra.signer import mr_signer_from_pk

from mse_home.log import LOGGER as LOG
from mse_home.model.evidence import ApplicationEvidence


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "verify",
        help="Verify the trustworthiness of a running MSE web application and get the ratls certificate",
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
        help="The verified certificate",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    evidence = ApplicationEvidence.load(args.evidence)

    # TODO: we can probably merge this function
    # somehow with `mse_cli.subcommand.helpers.verify_app`

    # Compute MRSIGNER value from public key
    mrsigner = mr_signer_from_pk(evidence.signer_pk)

    # Check certificate's public key in quote's user report data
    quote = ratls_verification(evidence.ratls_certificate)

    # Check MRSIGNER
    if quote.report_body.mr_signer != mrsigner:
        LOG.error("Verification failed!")
        raise Exception(
            "Enclave signer is wrong "
            f"(read {bytes(quote.report_body.mr_signer).hex()} "
            f"but should be {bytes(mrsigner).hex()})"
        )

        # Check enclave certificates and information
        # try:
        #     remote_attestation(quote=quote)  # TODO: PCC_URL to change here
        # except Exception as exc:
        #     LOG.error("Verification failed!")
        #     raise exc

    if quote.report_body.mr_enclave != bytes.fromhex(args.fingerprint):
        LOG.error("Verification failed!")
        raise Exception(
            "Code fingerprint is wrong "
            f"(read {bytes(quote.report_body.mr_enclave).hex()} "
            f"but should be {args.fingerprint})"
        )

    LOG.info("Verification succeed!")

    ratls_cert_path = args.output / "ratls.pem"
    ratls_cert_path.write_bytes(
        evidence.ratls_certificate.public_bytes(encoding=Encoding.PEM)
    )

    LOG.info("The ratls certificate has been saved at: %s", ratls_cert_path)
