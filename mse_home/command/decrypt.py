"""mse_home.command.decrypt module."""

from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "decrypt", help="Decrypt a file encrypted using the sealed key"
    )

    parser.add_argument(
        "--aes",
        type=str,
        metavar="KEY",
        required=True,
        help="Decrypt using AES-CBC and the given key (in hex)",
    )

    parser.add_argument(
        "encrypted_file",
        type=Path,
        help="The file to decrypt",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="The plaintext file",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    LOG.info("Decrypting your file...")

    key = bytes.fromhex(args.aes)
    encrypted_bytes = args.encrypted_file.read_bytes()
    iv = encrypted_bytes[:16]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    args.output.write_bytes(
        decryptor.update(encrypted_bytes[16:]) + decryptor.finalize()
    )

    LOG.info("Your file has been decrypted and saved at: %s", args.output)
