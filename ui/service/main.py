"""FastAPI application + routes for the GUI service.

Exposes `GET /api/health`, `GET /api/graph`, `GET /api/algorithms` and
`GET /api/version` (GUI_ROADMAP.md § 11/§ 12) and, since Task-012,
`POST /api/search` (§ 11): it validates inputs, runs the requested algorithm
with a timeout, records the run, and returns the § 11
``{run, result, metrics, route}`` body. Errors follow § 7.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from config.settings import SCHEMA_VERSION
from shared.exceptions import InvalidGraphError
from shared.logger import get_logger

from . import backends, errors, graphs, history, routing, serialization

__all__ = ["create_app", "main"]

logger = get_logger(__name__)

router = APIRouter(prefix="/api")

DEFAULT_FRONTEND_ORIGIN = "http://localhost:5173"

# Service identity for the § 12 version gate (GUI_ROADMAP.md § 11 `GET /version`).
SERVICE_NAME = "hcmc-ai-ui-service"
API_VERSION = "1.0"

# Shared catalog reused by `GET /algorithms` (GUI_ROADMAP.md § 11).
_CATALOG = backends.AlgorithmCatalog()

# Search runs longer than this (ms) are aborted as `504 SEARCH_TIMEOUT` (§ 7/§ 11).
SEARCH_TIMEOUT_MS = 5000

# Failures to produce the payload that mean "the graph is not available"
# (GUI_ROADMAP.md § 7): a missing file, unparseable JSON, a schema-version or
# invariant violation, or a Pydantic validation error. Everything else is an
# unexpected internal failure and stays `500 INTERNAL`.
GRAPH_LOAD_EXCEPTIONS = (
    FileNotFoundError,
    InvalidGraphError,
    json.JSONDecodeError,
    ValidationError,
)


class _SearchRequest(BaseModel):
    """The § 11 `POST /search` request body.

    `enable_logging` defaults to `True` so every normal interactive search
    records `SearchStep`s for the animation + replay pipeline; callers that do
    not need steps opt out explicitly.
    """

    algorithm: str
    start: str
    goal: str
    enable_logging: bool = True


def _frontend_origin() -> str:
    """Return the CORS origin configured for the frontend.

    Reads `GUI_FRONTEND_ORIGIN` (single origin) and falls back to the local Vite
    dev origin; overridable later by production config without code changes.
    """
    return os.getenv("GUI_FRONTEND_ORIGIN", DEFAULT_FRONTEND_ORIGIN)


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe (GUI_ROADMAP.md § 11)."""
    return {"status": "ok"}


@router.get("/graph", response_model=None)
def get_graph() -> dict[str, Any] | JSONResponse:
    """Serve the delivery graph payload (GUI_ROADMAP.md § 11).

    Returns:
        The cached `graph` / `bbox` / `metadata` payload; `503 GRAPH_NOT_FOUND`
        when the graph files are missing or failed to load; `500 INTERNAL` on any
        other (unexpected) failure (§ 7).
    """
    try:
        return graphs.get_graph_payload()
    except GRAPH_LOAD_EXCEPTIONS as exc:
        logger.warning("graph payload unavailable: %s", exc)
        return errors.graph_not_found()
    except Exception as exc:  # noqa: BLE001 - surface unexpected failures as INTERNAL
        logger.error("unexpected graph payload failure: %s", exc)
        return errors.internal_error()


@router.get("/algorithms", response_model=None)
def get_algorithms() -> JSONResponse:
    """Serve the algorithm catalog (GUI_ROADMAP.md § 11 `GET /algorithms`)."""
    return JSONResponse(status_code=200, content={"algorithms": _CATALOG.all()})


@router.get("/version", response_model=None)
def get_version() -> JSONResponse:
    """Serve the schema/client version gate (GUI_ROADMAP.md § 11/§ 12)."""
    return JSONResponse(
        status_code=200,
        content={
            "service": SERVICE_NAME,
            "version": SCHEMA_VERSION,
            "api_version": API_VERSION,
        },
    )


# Persistent worker pool for search runs. Module-level (not created per request)
# so a timed-out search can outlive the request thread: the handler returns
# `504` immediately while the worker finishes in the background.
_SEARCH_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def _run_search_with_timeout(
    algorithm: str,
    start: str,
    goal: str,
    enable_logging: bool,
) -> tuple[Any, str]:
    """Run `routing.run` in a worker and fail with `504` when it overruns.

    `routing.run` is CPU-bound; the executor keeps the event loop free and the
    `result(timeout=...)` call lets the service honor `SEARCH_TIMEOUT_MS`. On
    timeout the handler returns immediately without waiting for (or cancelling)
    the worker — the running search is simply abandoned after the deadline.
    """
    future = _SEARCH_EXECUTOR.submit(
        backends.run_search, algorithm, start, goal, enable_logging=enable_logging
    )
    try:
        return future.result(timeout=SEARCH_TIMEOUT_MS / 1000.0)
    except TimeoutError as exc:
        raise errors.SearchTimeoutError(
            "The search did not finish in time. Try a smaller graph or a different algorithm."
        ) from exc


def _handle_search(payload: _SearchRequest) -> JSONResponse:
    """Validate, run and record a search; return the § 11 response body."""
    delivery = graphs.get_delivery_graph()
    node_ids = {node.id for node in delivery.nodes}
    if payload.start not in node_ids or payload.goal not in node_ids:
        raise errors.InvalidInputError(
            "Unknown node id; `start` and `goal` must be delivery graph node ids."
        )

    try:
        result, source = _run_search_with_timeout(
            payload.algorithm,
            payload.start,
            payload.goal,
            payload.enable_logging,
        )
    except errors.SearchError:
        raise
    except NotImplementedError as exc:
        # Only reachable for a NotImplementedError escaping outside the backend
        # (registered placeholders are caught in backends.run and fall back to
        # the mock, § 10). Safety net: surface as `ALGORITHM_UNAVAILABLE` (§ 7).
        raise errors.AlgorithmUnavailableError(
            "The requested algorithm is not available for this graph."
        ) from exc
    except KeyError as exc:
        # A registered algorithm crashed with an internal KeyError. This is a
        # real bug, not a registry miss (backends handles misses before running);
        # never mask it with a mock (GUI_ROADMAP § 10) — surface as SEARCH_FAILED.
        raise errors.SearchFailedError(
            "The search failed for the given inputs."
        ) from exc
    except Exception as exc:  # never leak stack traces to the wire
        raise errors.SearchFailedError(
            "The search failed for the given inputs."
        ) from exc

    recorded = history.record(
        algorithm=payload.algorithm,
        start=payload.start,
        goal=payload.goal,
        source=source,
        result=result,
    )
    return JSONResponse(
        status_code=200,
        content=_search_response(recorded, result, source),
    )


def _search_response(
    recorded: history.RecordedRun,
    result: Any,
    source: str,
) -> dict[str, Any]:
    """Build the § 11 `POST /search` success body."""
    return {
        "run": {
            "id": recorded.id,
            "algorithm": recorded.algorithm,
            "source": source,
        },
        "result": serialization.search_result_to_contract(result),
        "metrics": serialization.metrics_from_result(result),
        "route": routing.expand_path(
            result.path,
            graphs.get_road_graph(),
            graphs.get_delivery_graph(),
        ),
    }


@router.post("/search", response_model=None)
def create_search(payload: _SearchRequest) -> JSONResponse:
    """Serve a search request (GUI_ROADMAP.md § 11)."""
    try:
        return _handle_search(payload)
    except errors.SearchError as exc:
        return errors.error_response(exc.status_code, exc.to_envelope())


@router.get("/history", response_model=None)
def get_history() -> JSONResponse:
    """Serve the recent run summaries (GUI_ROADMAP.md § 11 `GET /history`)."""
    return JSONResponse(status_code=200, content={"runs": history.list_runs()})


@router.get("/history/{run_id}", response_model=None)
def get_history_by_id(run_id: str) -> JSONResponse:
    """Serve a single recorded run, incl. its steps for replay (§ 11).

    Returns `404 NOT_FOUND` (§ 7) when the run id is unknown.
    """
    run = history.get_run(run_id)
    if run is None:
        envelope = errors.ErrorEnvelope(
            code="NOT_FOUND",
            message=f"No recorded run with id {run_id!r}.",
            details={"id": run_id},
        )
        return errors.error_response(404, envelope)
    return JSONResponse(
        status_code=200,
        content={
            "run": {
                "id": run.id,
                "algorithm": run.algorithm,
                "start": run.start,
                "goal": run.goal,
                "source": run.source,
                "created_at": run.created_at,
                "hops": run.hops,
            },
            "result": serialization.search_result_to_contract(run.result),
        },
    )


def create_app() -> FastAPI:
    """Build the service application with the `/api` router."""
    app = FastAPI(title="HCMC Delivery AI Search - UI service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[_frontend_origin()],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def _on_validation_error(request: Request, exc: RequestValidationError):
        return errors.error_response(
            400,
            errors.InvalidInputError("The request body does not match the § 11 search schema.").to_envelope(),
        )

    return app


def main() -> None:
    """Run the service with uvicorn (dev entry point)."""
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()