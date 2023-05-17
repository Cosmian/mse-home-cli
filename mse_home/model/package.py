"""mse_home.model.package module."""

import tarfile
from pathlib import Path

from pydantic import BaseModel

CODE_TAR_NAME = "code.tar"
DOCKER_IMAGE_TAR_NAME = "image.tar"
CODE_CONFIG_NAME = "code.toml"
TEST_DIR_NAME = "tests"


class CodePackage(BaseModel):
    """Definition of a code package."""

    code_tar: Path
    image_tar: Path
    test_path: Path
    config_path: Path

    def create(
        self,
        output_tar: Path,
    ):
        """Create the package containing the code and docker image tarballs."""
        with tarfile.open(output_tar, "w:") as tar_file:
            tar_file.add(self.code_tar, CODE_TAR_NAME)
            tar_file.add(self.image_tar, DOCKER_IMAGE_TAR_NAME)
            tar_file.add(self.test_path, TEST_DIR_NAME)
            tar_file.add(self.config_path, CODE_CONFIG_NAME)

    @staticmethod
    def extract(workspace: Path, package: Path):
        """Extract the code and image tarballs from the mse package."""
        with tarfile.open(package, "r") as f:
            f.extractall(path=workspace)

        code_tar_path = workspace / CODE_TAR_NAME
        image_tar_path = workspace / DOCKER_IMAGE_TAR_NAME
        code_config_path = workspace / CODE_CONFIG_NAME
        test_dir_path = workspace / TEST_DIR_NAME

        if not code_tar_path.exists():
            raise Exception(f"'{CODE_TAR_NAME}' was not found in the mse package")

        if not image_tar_path.exists():
            raise Exception(
                f"'{DOCKER_IMAGE_TAR_NAME}' was not found in the mse package"
            )

        if not code_config_path.exists():
            raise Exception(f"'{CODE_CONFIG_NAME}' was not found in the mse package")

        if not test_dir_path.exists():
            raise Exception(f"'{TEST_DIR_NAME}' was not found in the mse package")

        return CodePackage(
            code_tar=code_tar_path,
            image_tar=image_tar_path,
            test_path=test_dir_path,
            config_path=code_config_path,
        )