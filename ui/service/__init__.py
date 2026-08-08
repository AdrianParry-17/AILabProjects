"""GUI-owned Python JSON service (the thin backend).

Serves the React frontend over HTTP (GUI_ROADMAP.md § 3.2, § 4): loads the delivery +
road graphs, runs searches via ``run_algorithm`` with mock fallback, and serializes
results per docs/MAP_CONTRACT.md. Owned by the UI-facing service owner.
"""

from __future__ import annotations

from . import errors as errors
from . import graphs as graphs
from . import history as history
from . import main as main
from . import routing as routing
from . import serialization as serialization
