"""mse_home.command.seal module."""

from pathlib import Path

from intel_sgx_ra.ratls import ratls_verification
from mse_lib_crypto.seal_box import seal

from mse_home.log import LOGGER as LOG
from mse_home.model.evidence import ApplicationEvidence


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "seal", help="Seal the secrets to be share with an MSE app"
    )

    parser.add_argument(
        "--secrets",
        type=Path,
        required=True,
        help="The secret file to seal",
    )

    # TODO: we just need the certificate
    parser.add_argument(
        "--evidence",
        required=True,
        type=Path,
        metavar="FILE",
        help="path to the evidence file",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="The directory to write the sealed secrets file",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    evidence = ApplicationEvidence.load(args.evidence)

    quote = ratls_verification(evidence.ratls_certificate)
    enclave_pk = quote.report_body.report_data[32:64]

    sealed_secrets = seal(args.secrets.read_bytes(), enclave_pk)

    sealed_secrets_path: Path = args.output / (args.secrets.name + ".sealed")

    sealed_secrets_path.write_bytes(sealed_secrets)

    LOG.info("Your sealed secrets has been saved at: %s", sealed_secrets_path)
