"""Test command/*.py."""

import io
import os
import re
import time
from argparse import Namespace
from pathlib import Path

import pytest
from conftest import capture_logs

from mse_home.command.evidence import run as do_evidence
from mse_home.command.fingerprint import run as do_fingerprint
from mse_home.command.list_all import run as do_list
from mse_home.command.logs import run as do_logs
from mse_home.command.package import run as do_package
from mse_home.command.restart import run as do_restart
from mse_home.command.run import run as do_run
from mse_home.command.scaffold import run as do_scaffold
from mse_home.command.spawn import run as do_spawn
from mse_home.command.status import run as do_status
from mse_home.command.stop import run as do_stop
from mse_home.command.test import run as do_test
from mse_home.command.test_dev import run as do_test_dev
from mse_home.command.verify import run as do_verify

APP_NAME = f"app_{time.time_ns()}"


@pytest.mark.slow
@pytest.mark.incremental
def test_scaffold(workspace):
    """Test the scaffold subcommand."""
    # Go into a unique tmp directory
    os.chdir(workspace)

    # Run scaffold
    do_scaffold(Namespace(**{"app_name": APP_NAME}))

    # Check creation of files
    path = workspace / APP_NAME
    pytest.app_path = path

    assert path.exists()
    assert (path / "Dockerfile").exists()
    assert (path / "code.toml").exists()
    assert (path / "mse_src").exists()
    assert (path / "mse_src" / "app.py").exists()
    assert (path / "mse_src" / ".mseignore").exists()
    assert (path / "tests").exists()


@pytest.mark.slow
@pytest.mark.incremental
def test_test_dev(cmd_log: io.StringIO):
    """Test the test-dev subcommand."""
    do_test_dev(
        Namespace(
            **{
                "code": pytest.app_path / "mse_src",
                "dockerfile": pytest.app_path / "Dockerfile",
                "config": pytest.app_path / "code.toml",
                "secrets": None,
                "test": pytest.app_path / "tests",
            }
        )
    )

    # Check the tar generation
    assert "Tests succeed!" in capture_logs(cmd_log)


@pytest.mark.slow
@pytest.mark.incremental
def test_package(workspace: Path, cmd_log: io.StringIO):
    """Test the package subcommand."""
    do_package(
        Namespace(
            **{
                "code": pytest.app_path / "mse_src",
                "config": pytest.app_path / "code.toml",
                "dockerfile": pytest.app_path / "Dockerfile",
                "test": pytest.app_path / "tests",
                "encrypt": True,
                "output": workspace,
            }
        )
    )

    # Check the tar generation
    output = capture_logs(cmd_log)
    try:
        pytest.key_path = Path(
            re.search(
                "Your code secret key has been saved at: ([a-z0-9/._]+)", output
            ).group(1)
        )

        pytest.package_path = Path(
            re.search(
                "Your package is now ready to be shared: ([a-z0-9/._]+)", output
            ).group(1)
        )
    except AttributeError:
        print(output)
        assert False

    assert pytest.package_path.exists()


@pytest.mark.slow
@pytest.mark.incremental
def test_spawn(workspace: Path, cmd_log: io.StringIO):
    """Test the spawn subcommand."""
    do_spawn(
        Namespace(
            **{
                "name": APP_NAME,
                "package": pytest.package_path,
                "host": "localhost",
                "days": 2,
                "port": 5555,  # How to stop if an error occurs?
                "size": 4096,
                "signer_key": Path(
                    "/opt/cosmian-internal/cosmian-signer-key.pem"
                ),  # TODO
                "output": workspace,
            }
        )
    )

    output = capture_logs(cmd_log)
    try:
        pytest.args_path = Path(
            re.search(
                "You can share '([a-z0-9/._-]+)' with the other participants.", output
            ).group(1)
        )
    except AttributeError:
        print(output)
        assert False

    assert pytest.args_path.exists()


@pytest.mark.slow
@pytest.mark.incremental
def test_logs(cmd_log: io.StringIO):
    """Test the logs subcommand."""
    do_logs(
        Namespace(
            **{
                "name": APP_NAME,
            }
        )
    )

    output = capture_logs(cmd_log)
    try:
        pytest.fingerprint = re.search(
            "Measurement:\n[ ]*([a-z0-9]{64})", output
        ).group(1)
    except AttributeError:
        print(output)
        assert False

    assert "Starting the configuration server..." in output


@pytest.mark.slow
@pytest.mark.incremental
def test_status_conf_server(cmd_log: io.StringIO):
    """Test the status subcommand on the conf server."""
    do_status(
        Namespace(
            **{
                "name": APP_NAME,
            }
        )
    )

    output = capture_logs(cmd_log)

    assert f"App name = {APP_NAME}" in output
    assert "Enclave size = 4096M" in output
    assert "Common name = localhost" in output
    assert "Port = 5555" in output
    assert "Healthcheck = /health" in output
    assert "Status = waiting secret keys" in output  # TODO: test when waiting secrets


@pytest.mark.slow
@pytest.mark.incremental
def test_evidence(workspace: Path, cmd_log: io.StringIO):
    """Test the evidence subcommand."""
    do_evidence(
        Namespace(
            **{
                "name": APP_NAME,
                "pccs": "https://pccs.staging.mse.cosmian.com",  # TODO
                "signer_key": Path(
                    "/opt/cosmian-internal/cosmian-signer-key.pem"
                ),  # TODO
                "output": workspace,
            }
        )
    )

    output = capture_logs(cmd_log)
    try:
        pytest.evidence_path = Path(
            re.search(
                "The evidence file has been generated at: ([a-z0-9/._-]+)", output
            ).group(1)
        )
    except AttributeError:
        print(output)
        assert False

    assert pytest.evidence_path.exists()


@pytest.mark.slow
@pytest.mark.incremental
def test_fingerprint(cmd_log: io.StringIO):
    """Test the fingerprint subcommand."""
    do_fingerprint(
        Namespace(
            **{
                "package": pytest.package_path,
                "args": pytest.args_path,
            }
        )
    )

    output = capture_logs(cmd_log)
    try:
        assert pytest.fingerprint == re.search(
            "Fingerprint is: ([a-z0-9]+)", output
        ).group(1)

    except AttributeError:
        print(output)
        assert False


@pytest.mark.slow
@pytest.mark.incremental
def test_verify(cmd_log: io.StringIO):
    """Test the verify subcommand."""
    do_verify(
        Namespace(
            **{
                "fingerprint": pytest.fingerprint,
                "evidence": pytest.evidence_path,
            }
        )
    )

    assert "Verification succeed!" in capture_logs(cmd_log)


# TODO: test seal key


@pytest.mark.slow
@pytest.mark.incremental
def test_run(cmd_log: io.StringIO):
    """Test the run subcommand."""
    do_run(
        Namespace(
            **{
                "name": APP_NAME,
                "key": pytest.key_path,
                "secrets": None,
                "sealed_secrets": None,
            }
        )
    )

    assert "Application ready!" in capture_logs(cmd_log)


@pytest.mark.slow
@pytest.mark.incremental
def test_test():
    """Test the test subcommand."""
    do_test(
        Namespace(
            **{
                "name": APP_NAME,
                "test": pytest.app_path / "tests",
                "config": pytest.app_path / "code.toml",
            }
        )
    )

    assert True


@pytest.mark.slow
@pytest.mark.incremental
def test_status(cmd_log: io.StringIO):
    """Test the status subcommand."""
    do_status(
        Namespace(
            **{
                "name": APP_NAME,
            }
        )
    )

    output = capture_logs(cmd_log)

    assert f"App name = {APP_NAME}" in output
    assert "Enclave size = 4096M" in output
    assert "Common name = localhost" in output
    assert "Port = 5555" in output
    assert "Healthcheck = /health" in output
    assert "Status = running" in output  # TODO: test when waiting secrets


@pytest.mark.slow
@pytest.mark.incremental
def test_list(cmd_log: io.StringIO):
    """Test the list subcommand."""
    do_list(Namespace())

    output = capture_logs(cmd_log)

    assert f"running   | {APP_NAME}" in output


@pytest.mark.slow
@pytest.mark.incremental
def test_stop(cmd_log: io.StringIO):
    """Test the stop subcommand."""
    do_stop(Namespace(**{"name": APP_NAME, "remove": False}))

    output = capture_logs(cmd_log)

    assert f"Docker '{APP_NAME}' has been stopped!" in output
    assert f"Docker '{APP_NAME}' has been removed!" not in output

    do_status(
        Namespace(
            **{
                "name": APP_NAME,
            }
        )
    )

    output = capture_logs(cmd_log)

    assert "Status = exited" in output

    do_list(Namespace())

    output = capture_logs(cmd_log)

    assert f"exited   | {APP_NAME}" in output


@pytest.mark.slow
@pytest.mark.incremental
def test_restart(cmd_log: io.StringIO):
    """Test the restart subcommand."""
    do_restart(Namespace(**{"name": APP_NAME}))

    output = capture_logs(cmd_log)

    assert f"Docker '{APP_NAME}' is now restarted!" in output

    time.sleep(10)

    do_status(
        Namespace(
            **{
                "name": APP_NAME,
            }
        )
    )

    output = capture_logs(cmd_log)

    assert "Status = running" in output

    do_list(Namespace())

    output = capture_logs(cmd_log)

    assert f"running   | {APP_NAME}" in output


@pytest.mark.slow
@pytest.mark.incremental
def test_remove(cmd_log: io.StringIO):
    """Test the stop subcommand with removing."""
    do_stop(Namespace(**{"name": APP_NAME, "remove": True}))

    output = capture_logs(cmd_log)

    assert f"Docker '{APP_NAME}' has been stopped!" in output
    assert f"Docker '{APP_NAME}' has been removed!" in output

    with pytest.raises(Exception):
        do_status(
            Namespace(
                **{
                    "name": APP_NAME,
                }
            )
        )

    do_list(Namespace())

    output = capture_logs(cmd_log)

    assert f"{APP_NAME}" not in output


# TODO: verify error cases
