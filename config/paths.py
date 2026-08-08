"""Filesystem layout.

Resolved relative to this package so the project is location-independent and each
loader can open its dataset without guessing (CONVENTION.md § 11).
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

RAW_OSM_PATH = RAW_DIR / "hcmc_overpass.json"
ROAD_GRAPH_PATH = PROCESSED_DIR / "graph.json"
DELIVERY_GRAPH_PATH = EXPORTS_DIR / "delivery_graph.json"
