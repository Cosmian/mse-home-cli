"""mse_home.model.args module."""

from pathlib import Path
from typing import Any, Dict

import toml
from pydantic import BaseModel

from mse_home.model.docker import DockerConfig


class ApplicationArguments(BaseModel):
    """Definition of an enclave args used to verify the app."""

    host: str
    expiration_date: int
    size: int
    app_id: str
    application: str
    plaincode: bool

    @staticmethod
    def load(path: Path):
        """Load the args from a toml file."""
        with open(path, encoding="utf8") as f:
            dataMap = toml.load(f)

            return ApplicationArguments(**dataMap)

    @staticmethod
    def from_docker_config(docker_config: DockerConfig):
        return ApplicationArguments(
            host=docker_config.host,
            expiration_date=docker_config.expiration_date,
            size=docker_config.size,
            app_id=str(docker_config.app_id),
            application=docker_config.application,
            plaincode=docker_config.plaincode,
        )

    def save(self, path: Path) -> None:
        """Save the args into a toml file."""
        with open(path, "w", encoding="utf8") as f:
            dataMap: Dict[str, Any] = {
                "host": self.host,
                "expiration_date": self.expiration_date,
                "size": self.size,
                "app_id": self.app_id,
                "application": self.application,
                "plaincode": self.plaincode,
            }

            toml.dump(dataMap, f)
