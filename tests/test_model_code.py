"""Test model/code.py."""

import filecmp
from pathlib import Path

import pytest

from mse_home.model.code import CodeConfig


def test_load():
    """Test `load` function."""
    toml = Path(__file__).parent / "data/mse.toml"
    conf = CodeConfig.load(path=toml)

    ref_conf = CodeConfig(
        name="example",
        python_application="app:app",
        healthcheck_endpoint="/health",
        tests_cmd="pytest",
        tests_requirements=["intel-sgx-ra>=1.0.1,<1.1", "pytest==7.2.0"],
    )

    assert conf == ref_conf


def test_python_variable():
    """Test properties for `python_application` field."""
    conf = CodeConfig(
        name="example",
        python_application="app:ppa",
        healthcheck_endpoint="/health",
        tests_cmd="pytest",
        tests_requirements=["intel-sgx-ra>=1.0.1,<1.1", "pytest==7.2.0"],
    )

    assert conf.python_module == "app"
    assert conf.python_variable == "ppa"

    conf = CodeConfig(
        name="example",
        python_application="bad",
        healthcheck_endpoint="/health",
        tests_cmd="pytest",
        tests_requirements=["intel-sgx-ra>=1.0.1,<1.1", "pytest==7.2.0"],
    )

    with pytest.raises(Exception) as context:
        conf.python_variable
        conf.python_module


def test_save(workspace: Path):
    """Test the `save` method."""
    toml = Path(__file__).parent / "data/mse.toml"
    conf = CodeConfig.load(path=toml)

    tmp_toml = workspace / "mse.toml"
    conf.save(tmp_toml)

    assert filecmp.cmp(toml, tmp_toml)
