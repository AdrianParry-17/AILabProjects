"""Build the Delivery Graph (application layer) from the road graph.

Two-layer architecture:
* Road Graph (data/processed/graph.json): all OSM intersections/roads, backend-only,
  used to compute shortest paths.
* Delivery Graph (data/exports/delivery_graph.json): only meaningful POIs, the layer
  that search algorithms / UI / animation / reports operate on.

Example:
    python scripts/build_delivery_graph.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from delivery.builder import main

if __name__ == "__main__":
    main()
