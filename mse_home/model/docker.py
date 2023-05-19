"""mse_home.model.docker_cmd module."""

from typing import Any, Dict, List

from pydantic import BaseModel


class DockerConfig(BaseModel):
    """Definition of a running docker configuration."""

    size: int
    host: str
    app_id: str
    ratls: int
    code: str
    application: str
    port: int
    plaincode: bool

    def serialize(self) -> List[str]:
        """Serialize the docker command args."""
        args = [
            "--size",
            f"{self.size}M",
            "--code",
            self.code,
            "--host",
            self.host,
            "--id",
            self.app_id,
            "--application",
            self.application,
            "--ratls",
            str(self.ratls),
        ]

        if self.plaincode:
            args.append("--plaincode")

        return args

    @staticmethod
    def load(cmd: List[str], port: Dict[str, List[Dict[str, str]]]):
        """Load the the docker configuration from the command."""
        dataMap: Dict[str, Any] = {}

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
            host=dataMap["host"],
            app_id=dataMap["id"],
            ratls=int(dataMap["ratls"]),
            code=dataMap["code"],
            application=dataMap["application"],
            port=int(port["443/tcp"][0]["HostPort"]),
            plaincode=dataMap.get("plaincode", False),
        )
