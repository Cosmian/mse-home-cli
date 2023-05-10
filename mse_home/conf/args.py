from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel
import toml


class ApplicationArguments(BaseModel):
    host: str
    port: int
    expiration_date: int
    size: int
    app_id: str

    @staticmethod
    def load(path: Path):
        with open(path, encoding="utf8") as f:
            dataMap = toml.load(f)

            return ApplicationArguments(**dataMap)

    def save(self, path: Path) -> None:
        with open(path, "w", encoding="utf8") as f:
            dataMap: Dict[str, Any] = {
                "host": self.host,
                "port": self.port,
                "expiration_date": self.expiration_date,
                "size": self.size,
                "app_id": self.app_id,
            }

            toml.dump(dataMap, f)
