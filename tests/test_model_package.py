"""Test model/package.py."""

import filecmp
from pathlib import Path
from tarfile import TarFile

import pytest

from mse_home.model.package import CodePackage


def test_create(workspace: Path):
    """Test `create` function."""
    package = CodePackage(
        code_tar=Path(__file__).parent / "data" / "package" / "code.tar",
        image_tar=Path(__file__).parent / "data" / "package" / "image.tar",
        test_path=Path(__file__).parent / "data" / "package" / "tests",
        config_path=Path(__file__).parent / "data" / "mse.toml",
    )

    package_tar_ref = Path(__file__).parent / "data" / "package" / "package.tar"
    package_tar = workspace / "package.tar"
    package.create(package_tar)

    assert TarFile(package_tar).getnames() == TarFile(package_tar_ref).getnames()


def test_extract(workspace: Path):
    """Test the `extract` method."""
    package_tar = Path(__file__).parent / "data" / "package" / "package.tar"
    package = CodePackage.extract(workspace, package_tar)

    assert package.code_tar == workspace / "code.tar"
    assert package.image_tar == workspace / "image.tar"
    assert package.test_path == workspace / "tests"
    assert package.config_path == workspace / "mse.toml"

    assert filecmp.cmp(
        Path(__file__).parent / "data" / "package" / "code.tar", package.code_tar
    )
    assert filecmp.cmp(
        Path(__file__).parent / "data" / "package" / "image.tar", package.image_tar
    )
    assert filecmp.cmp(
        Path(__file__).parent / "data" / "package" / "tests" / "test.py",
        package.test_path / "test.py",
    )
    assert filecmp.cmp(
        Path(__file__).parent / "data" / "mse.toml", package.config_path
    )


def test_extract_bad_tar(workspace: Path):
    """Test the `extract` method with errors."""
    # Not a tar
    package_tar = Path(__file__).parent / "data" / "args.toml"

    with pytest.raises(Exception):
        CodePackage.extract(workspace, package_tar)

    # Tar but without the expecting content
    package_tar = Path(__file__).parent / "data" / "package" / "code.tar"

    with pytest.raises(Exception):
        CodePackage.extract(workspace, package_tar)
