"""mse_home.model.docker_cmd module."""

from pathlib import Path
from typing import Any, ClassVar, Dict, List
from uuid import UUID

from docker.models.containers import Container
from pydantic import BaseModel


class DockerConfig(BaseModel):
    """Definition of a running docker configuration."""

    size: int
    host: str
    port: int
    app_id: UUID
    expiration_date: int
    code: Path
    application: str
    healthcheck: str
    signer_key: Path

    signer_key_mountpoint: ClassVar[str] = "/root/.config/gramine/enclave-key.pem"
    code_mountpoint: ClassVar[str] = "/tmp/app.tar"
    docker_label: ClassVar[str] = "mse-home"
    entrypoint: ClassVar[str] = "mse-run"

    def cmd(self) -> List[str]:
        """Serialize the docker command args."""
        return [
            "--size",
            f"{self.size}M",
            "--code",
            DockerConfig.code_mountpoint,
            "--san",
            str(self.host),
            "--id",
            str(self.app_id),
            "--application",
            self.application,
            "--ratls",
            str(self.expiration_date),
        ]

    def ports(self) -> Dict[str, List[Dict[str, str]]]:
        return {"443/tcp": ("127.0.0.1", str(self.port))}

    def labels(self) -> Dict[str, str]:
        return {
            DockerConfig.docker_label: "1",
            "healthcheck_endpoint": self.healthcheck,
        }

    def volumes(self) -> Dict[str, Dict[str, str]]:
        return {
            f"{self.code}": {"bind": DockerConfig.code_mountpoint, "mode": "rw"},
            "/var/run/aesmd": {"bind": "/var/run/aesmd", "mode": "rw"},
            f"{self.signer_key}": {
                "bind": DockerConfig.signer_key_mountpoint,
                "mode": "rw",
            },
        }

    @staticmethod
    def devices() -> List[str]:
        return [
            "/dev/sgx_enclave:/dev/sgx_enclave:rw",
            "/dev/sgx_provision:/dev/sgx_enclave:rw",
            "/dev/sgx/enclave:/dev/sgx_enclave:rw",
            "/dev/sgx/provision:/dev/sgx_enclave:rw",
        ]

    @staticmethod
    def load(container: Container):
        """Load the the docker configuration from the command."""
        dataMap: Dict[str, Any] = {}

        cmd = container.attrs["Config"]["Cmd"]
        port = container.attrs["HostConfig"]["PortBindings"]
        signer_key = next(
            filter(
                lambda mount: mount["Destination"]
                == DockerConfig.signer_key_mountpoint,
                container.attrs["Mounts"],
            )
        )

        i = 0
        while i < len(cmd):
            key = cmd[i][2:]
            if i + 1 == len(cmd):
                dataMap[key] = True
                i += 1
                break

            if cmd[i + 1].startswith("--"):
                dataMap[key] = True
                i += 1
                continue

            dataMap[key] = cmd[i + 1]
            i += 2

        return DockerConfig(
            size=int(dataMap["size"][:-1]),
            host=dataMap["san"],
            app_id=UUID(dataMap["id"]),
            expiration_date=int(dataMap["ratls"]),
            code=Path(dataMap["code"]),
            application=dataMap["application"],
            port=int(port["443/tcp"][0]["HostPort"]),
            healthcheck=container.labels["healthcheck_endpoint"],
            signer_key=Path(signer_key["Source"]),
        )
