"""mse_home.model.args module."""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional
from uuid import UUID

import toml
from pydantic import BaseModel

from mse_home.model.docker import DockerConfig


# TODO: can we use ApplicationArguments in DockerConfig to merge a bit the two classes
class ApplicationArguments(BaseModel):
    """Definition of an enclave args used to verify the app."""

    host: str
    expiration_date: Optional[int]
    app_cert: Optional[Path]
    size: int
    app_id: UUID
    application: str

    code_mountpoint: ClassVar[str] = "/tmp/app.tar"
    app_cert_mountpoint: ClassVar[str] = "/tmp/cert.pem"
    entrypoint: ClassVar[str] = "mse-run"

    def cmd(self) -> List[str]:
        """Serialize the docker command args."""
        command = [
            "--size",
            f"{self.size}M",
            "--code",
            ApplicationArguments.code_mountpoint,
            "--san",
            str(self.host),
            "--id",
            str(self.app_id),
            "--application",
            self.application,
            "--dry-run",
        ]

        if self.app_cert:
            command.append("--certificate")
            command.append(ApplicationArguments.app_cert_mountpoint)
        else:
            command.append("--ratls")
            command.append(str(self.expiration_date))

        return command

    def volumes(self, code_tar_path) -> Dict[str, Dict[str, str]]:
        v = {
            f"{code_tar_path}": {
                "bind": ApplicationArguments.code_mountpoint,
                "mode": "rw",
            }
        }

        if self.app_cert:
            v[f"{self.app_cert}"] = {
                "bind": ApplicationArguments.app_cert_mountpoint,
                "mode": "rw",
            }

        return v

    @staticmethod
    def load(path: Path):
        """Load the args from a toml file."""
        with open(path, encoding="utf8") as f:
            dataMap = toml.load(f)

            return ApplicationArguments(**dataMap)

    @staticmethod
    def from_docker_config(docker_config: DockerConfig):
        """Load from a DockerConfig object."""
        return ApplicationArguments(
            host=docker_config.host,
            expiration_date=docker_config.expiration_date,
            size=docker_config.size,
            app_id=docker_config.app_id,
            application=docker_config.application,
        )

    def save(self, path: Path) -> None:
        """Save the args into a toml file."""
        with open(path, "w", encoding="utf8") as f:
            dataMap: Dict[str, Any] = {
                "host": self.host,
                "expiration_date": self.expiration_date,
                "size": self.size,
                "app_id": str(self.app_id),
                "application": self.application,
            }

            toml.dump(dataMap, f)
