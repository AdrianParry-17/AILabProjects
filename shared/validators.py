"""Generic, dependency-free validation helpers.

Layer-specific graph invariants stay with their owner (e.g. strong connectivity in
`delivery/loader.py`); only reusable, shape-agnostic checks live here.
"""

from __future__ import annotations

from collections.abc import Iterable

from shared.exceptions import InvalidGraphError


def ensure_schema_version(declared: object, expected: str, *, what: str) -> None:
    """Raise `InvalidGraphError` when `declared != expected` (label = `what`)."""
    if declared != expected:
        raise InvalidGraphError(
            f"{what} schema_version {declared!r} != expected {expected!r}"
        )


def ensure_unique(values: Iterable[object], *, what: str) -> None:
    """Raise `InvalidGraphError` listing any duplicated `values`."""
    seen: set[object] = set()
    duplicates: set[object] = set()
    for item in values:
        if item == "":
            continue
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    if duplicates:
        raise InvalidGraphError(f"Duplicate {what}: {sorted(duplicates, key=str)}")
