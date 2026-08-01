from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_PATH = BACKEND_DIR / "data" / "hcmc_delivery_osm_snapshot.json"
TEACHING_DATASET_PATH = BACKEND_DIR / "data" / "delivery_teaching_fixture.json"
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "HCMC Delivery Route Lab API"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v1"
    dataset_path: Path = DEFAULT_DATASET_PATH
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS

    @classmethod
    def from_environment(cls, dataset_path: str | Path | None = None) -> "Settings":
        raw_path = dataset_path or os.getenv("ROUTING_DATASET_PATH") or DEFAULT_DATASET_PATH
        raw_origins = os.getenv("CORS_ORIGINS")
        origins = (
            tuple(item.strip() for item in raw_origins.split(",") if item.strip())
            if raw_origins
            else DEFAULT_CORS_ORIGINS
        )
        return cls(dataset_path=Path(raw_path).expanduser().resolve(), cors_origins=origins)
