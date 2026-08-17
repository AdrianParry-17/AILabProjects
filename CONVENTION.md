# CONVENTION.md

**HCMC Delivery AI Search - Development Convention**

Version: 3.0

Status: **Enforced** (for code style, typing, error handling, tests, and tooling).

This document is the single coding standard for the Python packages (`shared`, `config`,
`core`, `data`, `delivery`, `algorithms`, `visualization`, `scripts`, `tests`, `backend`)
and applies to every contributor. This file covers **how code is written**; the backend
API surface and the React frontend live in `backend/` and `frontend/` respectively.

---

# 1. General Principles

* Modular, small, single-responsibility modules.
* Reuse existing helpers before writing new ones.
* Strictly typed but **pragmatically**: typing protects the API surface, it is not an
  ideology. Follow § 4.
* Readable > clever. Vietnamese display names, English code.
* No `streamlit`, no Python UI framework. React is the frontend.
* Errors are explicit; nothing is silently swallowed.

---

# 2. Project Layout & Imports

The summary:

* `shared` owns generic protocols/helpers. `config` owns single-source values.
  `core` owns the search framework (`SearchResult`, registry). `data` owns the road models
  + dataset. `delivery` owns the POI graph + road shortest paths. `algorithms` owns
  search. `visualization` owns map serialization. `scripts` owns the pipeline.
  `backend` owns the FastAPI routing API. `frontend` owns the React app.
* Imports flow downward only. `data` never imports
  `delivery`/`algorithms`; `config`/`core` never import domain packages.
* Import order in every file: standard library, third-party, then local modules. Group
  with blank lines, exactly as:

```python
import math
from collections import deque

from pydantic import BaseModel

from data.models import GraphData
```

* No wildcard imports. Prefer importing the module, or explicit names.

---

# 3. Naming

| Kind | Convention | Example |
|------|-----------|---------|
| Package/dir | `snake_case` | `algorithms/` |
| Python file | `snake_case.py` | `path_metrics.py` |
| Class | `PascalCase` | `SearchResult` |
| Function/method | `snake_case` | `load_graph()` |
| Variable | `snake_case` | `current_node` |
| Constant | `UPPER_SNAKE` | `DEFAULT_WEIGHTS` |
| Private member | leading `_` | `_edge_by_pair` |
| Type variable | `PascalCase` | `TNode` |

Identifiers are English. **Displayed** strings (node names, explanations) are Vietnamese
and stored in the dataset, never in variable names.

---

# 4. Typing Rules (practical)

These replace the older absolute rules; they are enforceable by `mypy` without becoming
dogmatic.

1. **Annotate public signatures.** Every public function has typed parameters and a return
   type. Private helpers should be annotated too when non-trivial.
2. **Prefer precise over loose types.**
   * Use `list[str]`, `dict[str, float]`, `tuple[int, str]` instead of bare `list`/`dict`.
   * Prefer `dataclass`/Pydantic `BaseModel` over ad-hoc `dict[str, Any]` for multi-field
     state (matches § 7).
   * `Any` is allowed where the value is genuinely heterogeneous by contract (e.g. OSM tag
     dicts, JSON passthrough). Do NOT use `Any` to dodge typing on your own shapes.
3. **`Optional[T]` only when `None` is a real possibility.** If a value is always
   provided, don't annotate it `Optional`.
4. **`Final` for module constants** (aids mypy and readers).
5. **`Literal` / `Enum`.** Use an `Enum` when a set of values is domain logic
   (e.g. traffic condition, algorithm name). Use `Literal["one-way","two-way"]` for a
   small closed set of plain strings. Do **not** force an Enum where a plain string with a
   documented contract is clearer (dataset `kind`, `road_class`).
6. **`isinstance` is fine** when narrowing a genuinely mixed payload at a boundary (e.g.
   validating OSM element types). It is a *tool*, not a smell. Just keep payloads typed
   once they cross into typed model land.
7. **No `object`** as a general-purpose type; use `Any` (typed `object` only where you
   actually want to require `__str__`/etc.).
8. **JSON-shaped payloads** use Pydantic models (or `TypedDict` for read-only
   serialization). Prefer Pydantic so validation and `model_dump()` come free.

---

# 5. Documentation Style

Every module has a header docstring explaining its responsibility. Every public function
docstring covers **purpose**; add **Args / Returns / Raises** sections when not obvious.

```python
def load_graph(path: Path | None = None) -> GraphData:
    """Load the road graph.

    Args:
        path: Optional override; defaults to the packaged data/processed/graph.json.

    Returns:
        The validated GraphData model.

    Raises:
        ValueError: if the file is missing or malformed.
    """
```

Use English for code docs; only user-facing strings (explanations, UI labels) are
Vietnamese.

---

# 6. Exceptions

## 6.1 Hierarchy

The exception hierarchy is defined once in `shared/exceptions.py` (base `AILabError` +
per-layer roots `ConfigError`, `DataError`, `SearchError`). Import from there; do not
redefine a root in your layer. Reuse stdlib exceptions where fitting (`ValueError`,
`KeyError`, `FileNotFoundError`); add a domain subclass only when a caller needs to catch
a whole family:

```python
from shared.exceptions import InvalidGraphError, SearchError, UnreachableNodeError
```

(For reference, the hierarchy is `AILabError` → `ConfigError` / `DataError` →
`InvalidGraphError`, and `SearchError` → `UnreachableNodeError`.)

## 6.2 Rules

* Raise **project-specific** exceptions for domain failures; `ValueError`/`TypeError`
  for invalid arguments.
* Never `except Exception: pass` or swallow errors silently.
* Never re-raise a bare `raise` after handling without a reason; wrap with context when
  it helps (`raise InvalidGraphError("...") from exc`).
* Algorithms validate inputs first (missing node, disconnected target) and return a
  *failure* `SearchResult` rather than raising, per `ALGORITHM_SPEC.md`; genuine bugs
  (bad shapes, missing edges on a found path) raise.

---

# 7. Data Structures & State

* Prefer Pydantic `BaseModel` for anything serialized to JSON (dataset, search results).
* Prefer `@dataclass(frozen=True)` for immutable value objects (e.g. `CostWeights`).
* Prefer `@dataclass(slots=True)` for hot mutable objects (e.g. internal search state).
* **No mutable default arguments** — use `field(default_factory=...)`.
* No monkey-patching objects; no ad-hoc attribute assignment (`node.temp = True`).
* No `global` and no static mutable class attributes.

```python
@dataclass(frozen=True, slots=True)
class CostWeights:
    distance: float = 0.3
    time: float = 0.4
    congestion: float = 0.2
    risk: float = 0.1
```

---

# 8. Logging

* Use `logging`, the stdlib. Each package/module gets its own logger:
  `logger = logging.getLogger(__name__)`.
* Log at the right level: `debug` for search internals, `info` for pipeline milestones,
  `warning` for recoverable issues, `error` for failures.
* Never `print()` in library code. `print` is acceptable only in `scripts/*` entry points
  (CLI output), not in `data`, `delivery`, or `algorithms`.
* Sensitive data (API keys) never logged.

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("expanding node %s", current)   # f-strings NOT required here
```

---

# 9. Testing

* Tests live under the top-level `tests/` package, one subpackage per owner
  (`tests/algorithms/`, `tests/core/`, `tests/data/`, `tests/delivery/`,
  `tests/visualization/`), named `test_<module>.py` (e.g. `tests/algorithms/test_bfs.py`).
* Tests are run with `pytest` (from the repository root: `python -m pytest`).
* Every important module includes: happy path, edge cases, invalid input, and (where
  applicable) a by-hand/analytical trace.
* Tests are deterministic: no sleeps, no network, no nondeterminism. Fixtures are
  hand-built or load versioned data files.
* Name tests as `test_<behaviour>` and assert behaviour, not implementation.

See `ALGORITHM_SPEC.md § 9` for algorithm-specific test obligations.

---

# 10. Performance

* Keep worst-case bounds in mind for the target graphs: the road graph is ~1.1k nodes /
  ~2.3k directed edges; the delivery graph is ~31 POIs.
* Sub-100-node searches must finish well under 50 ms. Prefer O(1) lookups:
  `build_edge_lookup()` (a `(start, end) -> Edge` map) over linear scans inside loops.
* Precompute indices once (e.g. `RoadGraph` builds `_out`/`_edge_by_pair` at
  construction), not per query.
* Cache repeated computations; avoid re-traversing the graph.
* Profile before optimizing; correctness and clarity first.

---

# 11. Versioning

* Code versioning = Git tags (`v1.0.0`, …). Semantic versioning: MAJOR for breaking
  schema/API changes, MINOR for additive features, PATCH for fixes.
* Dataset versioning = `metadata.version` + `generated_at` inside each
  `data/processed/*.json` / `data/exports/*.json`; bump on any schema change.
* Breaking schema changes require updating `config/settings.py::SCHEMA_VERSION`, the
  JSON generators, all consumers, and this doc set together in one PR.

---

# 12. JSON Naming (summary)

* snake_case field names, identical to the Pydantic fields.
* No field renaming between Python, JSON, or the React client.
* Coordinates: WGS84 decimal degrees; geometry arrays use `[lon, lat]` in the dataset and
  `[lat, lon]` in UI-facing payloads if the UI demands — keep the chosen convention
  documented in the backend schemas (`backend/app/schemas.py`).

---

# 13. Static Analysis & Quality Gates

Commands (run from the repository root):

```bash
python -m pytest                      # tests must pass
ruff check .                          # lints
python -m mypy data delivery algorithms core config shared visualization tests  # typing
```

Recommended `mypy` config (add to `pyproject.toml` when one exists):

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
```

Rules:

* Any `ruff` error or `mypy` error on *new/changed* code rejects the PR.
* Fixes may use `# type: ignore[code]` with a comment when justified; never blanket
  ignores.
* Keep `black`-compatible formatting (or run `ruff format`) so diffs stay clean.

---

# 14. Git Convention

* Branch names: `feature/<name>`, `fix/<name>`, `refactor/<name>`, `docs/<name>`.
* Commit message format (Conventional Commits):

```text
feat: implement ucs
fix: resolve bfs frontier ordering
docs: sync dataset spec with two-layer graph
refactor: move path metrics to shared helper
test: add delivery graph connectivity test
```

* Only commit what the task needs; never commit secrets, large dumps, or build artifacts
  beyond the agreed data files.

---

# 15. Code Review Checklist

- [ ] Follows the naming (§ 3), typing (§ 4), and doc (§ 5) rules.
- [ ] Imports respect the architecture dependency flow (§ 2).
- [ ] Uses shared helpers instead of duplicating logic.
- [ ] Raises project-specific exceptions; nothing swallowed.
- [ ] Tests added for the new behaviour; existing tests still pass.
- [ ] `ruff`, `mypy`, `pytest` all green on changed code.
- [ ] No `print()` in library code, no `streamlit` import.
- [ ] JSON field names unchanged unless `data/models.py` + the backend schemas updated in
      the same PR.

# UI Language Convention

All application interface text must be written in English.

This includes:

- Buttons
- Labels
- Menus
- Dialogs
- Placeholders
- Tooltips
- Status messages
- Error messages
- Notifications
- Accessibility labels

Exceptions:

Real-world geographic data must preserve its original language.

Examples:

✓ "Choose Algorithm"

✓ "Run Search"

✓ "Destination"

✓ "Đường Nguyễn Huệ"

✓ "Đại học Khoa học Tự nhiên"

Never translate dataset values.