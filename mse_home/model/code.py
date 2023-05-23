"""mse_home.model.code module."""

from pathlib import Path
from typing import Any, Dict, List

import toml
from pydantic import BaseModel


class CodeConfig(BaseModel):
    """Definition of a code configuration."""

    name: str
    python_application: str
    healthcheck_endpoint: str
    tests_cmd: str
    tests_requirements: List[str]

    @staticmethod
    def load(path: Path):
        """Load the args from a toml file."""
        with open(path, encoding="utf8") as f:
            dataMap = toml.load(f)

            return CodeConfig(**dataMap)

    def save(self, path: Path) -> None:
        """Save the code configuration into a toml file."""
        with open(path, "w", encoding="utf8") as f:
            dataMap: Dict[str, Any] = {
                "name": self.name,
                "python_application": self.python_application,
                "healthcheck_endpoint": self.healthcheck_endpoint,
                "tests_cmd": self.tests_cmd,
                "tests_requirements": self.tests_requirements,
            }

            toml.dump(dataMap, f)

    @property
    def python_module(self):
        """Get the python module from python_application."""
        split_str = self.python_application.split(":")
        if len(split_str) != 2:
            raise Exception(
                "`python_application` is malformed. Expected format: `module:variable`"
            )
        return split_str[0]

    @property
    def python_variable(self):
        """Get the python variable from python_application."""
        split_str = self.python_application.split(":")
        if len(split_str) != 2:
            raise Exception(
                "`python_application` is malformed. Expected format: `module:variable`"
            )
        return split_str[1]
