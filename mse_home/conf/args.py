"""mse_home.conf.args module."""

from pathlib import Path
from typing import Any, Dict

import toml
from pydantic import BaseModel


class ApplicationArguments(BaseModel):
    """Definition of an enclave args used to verify the app."""

    host: str
    expiration_date: int
    size: int
    app_id: str
    application: str

    @staticmethod
    def load(path: Path):
        """Load the args from a toml file."""
        with open(path, encoding="utf8") as f:
            dataMap = toml.load(f)

            return ApplicationArguments(**dataMap)

    def save(self, path: Path) -> None:
        """Save the args into a toml file."""
        with open(path, "w", encoding="utf8") as f:
            dataMap: Dict[str, Any] = {
                "host": self.host,
                "expiration_date": self.expiration_date,
                "size": self.size,
                "app_id": self.app_id,
                "application": self.application,
            }

            toml.dump(dataMap, f)
