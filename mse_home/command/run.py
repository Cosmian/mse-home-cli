"""mse_home.command.run module."""

import json
import time
from pathlib import Path
from typing import Any, Dict

import requests
from mse_home.conf.args import ApplicationArguments

from mse_home.log import LOGGER as LOG


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "run",
        help="Finalise the configuration of the application docker and run the application code",
    )

    parser.add_argument(
        "name",
        type=str,
        help="The name of the application",
    )

    parser.add_argument(
        "--args",
        type=str,
        required=True,
        help="The path to the enclave argument file generating when spawning the application (ex: args.toml)",
    )

    parser.add_argument(
        "--secrets",
        type=Path,
        required=False,
        help="The secrets.json file path",
    )

    parser.add_argument(
        "--sealed-secrets",
        type=Path,
        required=False,
        help="The sealed secrets.json file path",
    )

    parser.add_argument(
        "--key",
        type=Path,
        required=False,
        help="The code decryption sealed key file path",  # TODO: add unimplemented
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    app_args = ApplicationArguments.load(args.args)

    data: Dict[str, Any] = {
        "uuid": app_args.app_id,
    }

    if args.secrets:
        data["app_secrets"] = json.loads(args.secrets.read_text())

    if args.sealed_secrets:
        data["app_sealed_secrets"] = json.loads(args.sealed_secrets.read_text())

    if args.key:
        data["code_secret_key"] = args.key.read_text()

    send_secrets(data, app_args.port)
    wait_for_app_to_be_ready(app_args.port)


def send_secrets(data: Dict[str, Any], port: int):
    LOG.info("Sending secrets to the application...")

    r = requests.post(
        url=f"https://localhost:{port}/",
        json=data,
        headers={"Content-Type": "application/json"},
        verify=False,
        timeout=60,
    )

    if not r.ok:
        raise Exception(r.text)

    LOG.info("Secrets sent!")


def wait_for_app_to_be_ready(port: int):
    """Hold on until the configuration server is stopped and the app starts."""
    LOG.info("Waiting for your application to be ready...")
    while True:
        try:
            response = requests.get(f"https://localhost:{port}/", verify=False)

            if response.status_code != 503 and "Mse-Status" not in response.headers:
                break

        except requests.exceptions.SSLError:
            pass

        time.sleep(10)

    LOG.info("Application ready!")
