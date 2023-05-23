"""Test model/docker.py."""

from mse_home.model.sgx_docker import SgxDockerConfig


def test_load():
    """Test `load` function."""
    ref_conf = SgxDockerConfig(
        size=4096,
        host="localhost",
        app_id="test_id",
        timeout=123456789,
        self_signed=123456789,
        code="code.tar",
        application="app:app",
        port=1234,
    )

    conf = SgxDockerConfig.load(
        cmd=[
            "--size",
            "4096M",
            "--code",
            "code.tar",
            "--host",
            "localhost",
            "--uuid",
            "test_id",
            "--application",
            "app:app",
            "--timeout",
            "123456789",
            "--self-signed",
            "123456789",
        ],
        port={"443/tcp": [{"HostIp": "127.0.0.1", "HostPort": "1234"}]},
    )

    assert conf == ref_conf


def test_serialize():
    """Test `serialize` function."""
    docker = SgxDockerConfig(
        size=4096,
        host="localhost",
        app_id="test_id",
        timeout=123456789,
        self_signed=123456789,
        code="code.tar",
        application="app:app",
        port=1234,
    )

    assert docker.serialize() == [
        "--size",
        "4096M",
        "--code",
        "code.tar",
        "--host",
        "localhost",
        "--uuid",
        "test_id",
        "--application",
        "app:app",
        "--timeout",
        "123456789",
        "--self-signed",
        "123456789",
    ]
