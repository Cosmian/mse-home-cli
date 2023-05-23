"""Test model/args.py."""

import filecmp
from pathlib import Path

from mse_home.model.no_sgx_docker import NoSgxDockerConfig


def test_load():
    """Test `load` function."""
    toml = Path(__file__).parent / "data/args.toml"
    conf = NoSgxDockerConfig.load(path=toml)

    ref_conf = NoSgxDockerConfig(
        host="localhost",
        expiration_date=1714058115,
        size=4096,
        app_id="63322f85-1ff8-4483-91ae-f18d7398d157",
        application="app:app",
    )

    assert conf == ref_conf


def test_save(workspace: Path):
    """Test the `save` method."""
    toml = Path(__file__).parent / "data/args.toml"
    conf = NoSgxDockerConfig.load(path=toml)

    tmp_toml = workspace / "args.toml"
    conf.save(tmp_toml)

    assert filecmp.cmp(toml, tmp_toml)
