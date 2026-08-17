from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml


class MissingCredentialError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceConfig:
    name: str
    base_url: str
    license: str
    requires_account: bool


class MeteoFranceClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://portail-api.meteofrance.fr"):
        self.api_key = api_key or os.getenv("METEOFRANCE_API_KEY")
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise MissingCredentialError("METEOFRANCE_API_KEY est requis pour ingerer des donnees reelles")

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = httpx.get(f"{self.base_url}/{path.lstrip('/')}", params=params, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()


class LocalRealDataStore:
    def __init__(self, root: str | Path = "data/raw"):
        self.root = Path(root)

    def require_file(self, relative_path: str) -> Path:
        path = self.root / relative_path
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier reel manquant: {path}. Importer la source officielle avant de lancer le pipeline."
            )
        return path


def load_sources(path: str | Path = "config/sources.yaml") -> list[SourceConfig]:
    content = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [SourceConfig(**item) for item in content["sources"]]
