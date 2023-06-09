"""mse_home.command.code_provider.decrypt module."""

from pathlib import Path

from cryptography.fernet import Fernet

from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "decrypt", help="Decrypt a file using Fernet symmetric encryption"
    )

    parser.add_argument(
        "--key",
        type=Path,
        required=True,
        help="Path to the file within a 32 bytes key URL Safe Base64 encoded",
    )

    parser.add_argument(
        "file",
        type=Path,
        help="File to decrypt",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output file within plaintext",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    LOG.info("Decrypting %s...", args.file)

    key: bytes = args.key.read_bytes()
    encrypted_data: bytes = args.file.read_bytes()

    args.output.write_bytes(Fernet(key).decrypt(encrypted_data))

    LOG.info("File sucessfully decrypted in %s", args.output)
