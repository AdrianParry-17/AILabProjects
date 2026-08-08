"""Generic helper functions with no project dependencies.

These are pure/stdlib utilities used by build scripts, the delivery builder, and
metrics. Nothing layer-specific lives here.
"""

from __future__ import annotations

import hashlib
import math

from shared.constants import EARTH_RADIUS_M
from shared.types import LatLon


def haversine_m(a: LatLon, b: LatLon) -> float:
    """Great-circle distance in metres between two (lat, lon) points."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(value))


def stable_fraction(value: str) -> float:
    """Deterministic pseudo-random float in [0, 1) from a string (SHA-256).

    Used by the synthetic overlay layer so congestion/risk are reproducible across
    runs (DATASET_SPEC.md § 6.3).
    """
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / (2**64 - 1)
