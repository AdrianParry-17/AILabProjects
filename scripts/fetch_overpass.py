"""Fetch an Overpass snapshot for the HCMC teaching graph and save it as raw JSON.

Usage:
    python scripts/fetch_overpass.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.paths import RAW_OSM_PATH

MIRRORS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def fetch(query: str, timeout: int = 120) -> dict:
    last_error: Exception | None = None
    for mirror in MIRRORS:
        try:
            request = urllib.request.Request(
                mirror,
                data=query.encode("utf-8"),
                headers={"User-Agent": "hcmc-delivery-lab/1.0 (student project)"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if "elements" not in payload:
                raise ValueError(
                    f"Unexpected Overpass payload from {mirror}: {list(payload)[:5]}"
                )
            print(f"Fetched from {mirror}: {len(payload['elements'])} elements")
            return payload
        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc
            print(f"Mirror failed ({mirror}): {exc}")
            time.sleep(2)
    raise RuntimeError(f"All Overpass mirrors failed. Last error: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        type=Path,
        default=Path(__file__).with_name("overpass_hcmc.ql"),
        help="Path to the .ql Overpass query",
    )
    parser.add_argument(
        "--output", type=Path, default=RAW_OSM_PATH, help="Output raw JSON path"
    )
    args = parser.parse_args()

    query = args.query.read_text(encoding="utf-8")
    payload = fetch(query)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
