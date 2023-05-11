"""mse_home.conf.docker_cmd module."""

from typing import Any, Dict, List

from pydantic import BaseModel


class DockerConfig(BaseModel):
    """Definition of a running docker configuration."""

    size: int
    host: str
    app_id: str
    timeout: int
    self_signed: int
    code: str
    application: str
    port: int

    def serialize(self) -> List[str]:
        """Serialize the docker command args."""
        return [
            "--size",
            f"{self.size}M",
            "--code",
            self.code,
            "--host",
            self.host,
            "--uuid",
            self.app_id,
            "--application",
            self.application,
            "--timeout",
            int(self.timeout),
            "--self-signed",
            int(self.self_signed),
        ]

    def load(cmd: List[str], port: Dict[str, List[Dict[str, str]]]):
        """Load the the docker configuration from the command."""
        dataMap: Dict[str, Any] = {}
        for key, value in zip(cmd[::2], cmd[1::2]):
            dataMap[key[2:]] = value

        return DockerConfig(
            size=int(dataMap["size"][:-1]),
            host=dataMap["host"],
            app_id=dataMap["uuid"],
            timeout=int(dataMap["timeout"]),
            self_signed=int(dataMap["self-signed"]),
            code=dataMap["code"],
            application=dataMap["application"],
            port=int(port["443/tcp"][0]["HostPort"]),
        )
