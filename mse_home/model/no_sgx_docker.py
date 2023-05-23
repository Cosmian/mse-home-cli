"""mse_home.model.no_sgx_docker module."""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional
from uuid import UUID

import toml
from pydantic import BaseModel

from mse_home.model.sgx_docker import SgxDockerConfig


class NoSgxDockerConfig(BaseModel):
    """Definition of an mse docker running on a non-sgx hardware."""

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
            NoSgxDockerConfig.code_mountpoint,
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
            command.append(NoSgxDockerConfig.app_cert_mountpoint)
        else:
            command.append("--ratls")
            command.append(str(self.expiration_date))

        return command

    def volumes(self, code_tar_path) -> Dict[str, Dict[str, str]]:
        """Define the docker volumes."""
        v = {
            f"{code_tar_path}": {
                "bind": NoSgxDockerConfig.code_mountpoint,
                "mode": "rw",
            }
        }

        if self.app_cert:
            v[f"{self.app_cert}"] = {
                "bind": NoSgxDockerConfig.app_cert_mountpoint,
                "mode": "rw",
            }

        return v

    @staticmethod
    def load(path: Path):
        """Load the args from a toml file."""
        with open(path, encoding="utf8") as f:
            dataMap = toml.load(f)

            return NoSgxDockerConfig(**dataMap)

    @staticmethod
    def from_sgx(docker_config: SgxDockerConfig):
        """Load from a SgxDockerConfig object."""
        return NoSgxDockerConfig(
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
