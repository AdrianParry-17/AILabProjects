"""shared/validators unit tests."""

from __future__ import annotations

import pytest

from shared.exceptions import InvalidGraphError
from shared.validators import ensure_schema_version, ensure_unique


def test_ensure_schema_version_ok() -> None:
    ensure_schema_version("1.0", "1.0", what="graph")


def test_ensure_schema_version_mismatch_raises() -> None:
    with pytest.raises(InvalidGraphError):
        ensure_schema_version("2.0", "1.0", what="graph")


def test_ensure_unique_ok_with_empty_strings() -> None:
    ensure_unique(["a", "b", "", "", "c"], what="node id")


def test_ensure_unique_reports_sorted_duplicates() -> None:
    with pytest.raises(InvalidGraphError) as exc:
        ensure_unique(["b", "a", "b", "c", "a"], what="node id")
    assert "['a', 'b']" in str(exc.value)
    assert "node id" in str(exc.value)