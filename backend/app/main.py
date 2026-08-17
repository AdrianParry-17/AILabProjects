"""FastAPI entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .engine import RoutingEngine
from .errors import RoutingError
from .loader import DatasetLoadError, load_dataset
from .schemas import (
    CompareRequest,
    CompareResponse,
    GraphResponse,
    HealthResponse,
    MetadataResponse,
    MultiRouteRequest,
    MultiRouteResponse,
    ScenarioName,
    SearchRequest,
    SearchResponse,
    TrafficOverlayResponse,
)

logger = logging.getLogger(__name__)


def create_app(dataset_path: str | Path | None = None) -> FastAPI:
    settings = Settings.from_environment(dataset_path)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            metadata, graph = load_dataset(settings.dataset_path)
        except DatasetLoadError:
            logger.exception("Could not load routing dataset: %s", settings.dataset_path)
            raise
        application.state.routing_engine = RoutingEngine(metadata, graph)
        logger.info(
            "Loaded dataset %s (%d nodes, %d directed edges)",
            metadata.id,
            len(graph.nodes),
            len(graph.edges),
        )
        yield

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Educational classical-search API for courier and multi-stop delivery routes in "
            "central Ho Chi Minh City. The snapshot and scenario overlays are not live navigation data."
        ),
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @application.exception_handler(RoutingError)
    async def handle_routing_error(_: Request, exc: RoutingError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": jsonable_encoder(exc.details),
                }
            },
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    def engine_from_request(request: Request) -> RoutingEngine:
        engine: RoutingEngine | None = getattr(request.app.state, "routing_engine", None)
        if engine is None:
            raise RoutingError(
                "service_unavailable",
                "Routing dataset is not loaded",
                status_code=503,
            )
        return engine

    @application.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "api": settings.api_prefix,
        }

    @application.get(
        f"{settings.api_prefix}/health",
        response_model=HealthResponse,
        tags=["system"],
    )
    def health(engine: RoutingEngine = Depends(engine_from_request)) -> dict[str, Any]:  # noqa: B008
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
            "dataset_id": engine.dataset.id,
            "dataset_version": engine.dataset.version,
            "node_count": len(engine.graph.nodes),
            "directed_edge_count": len(engine.graph.edges),
        }

    @application.get(
        f"{settings.api_prefix}/metadata",
        response_model=MetadataResponse,
        tags=["metadata"],
    )
    def metadata(engine: RoutingEngine = Depends(engine_from_request)) -> dict[str, Any]:  # noqa: B008
        return engine.metadata_payload()

    @application.get(
        f"{settings.api_prefix}/graph",
        response_model=GraphResponse,
        tags=["graph"],
    )
    def graph(
        scenario: Annotated[ScenarioName, Query(description="Deterministic traffic overlay")] = ScenarioName.NORMAL,
        include_geojson: Annotated[
            bool,
            Query(description="Include a duplicate GeoJSON FeatureCollection for GIS clients"),
        ] = False,
        compact: Annotated[
            bool,
            Query(description="Return only attributes required by the interactive map"),
        ] = False,
        engine: RoutingEngine = Depends(engine_from_request),  # noqa: B008
    ) -> dict[str, Any]:
        return engine.graph_payload(
            scenario.value,
            include_geojson=include_geojson,
            compact=compact,
        )

    @application.get(
        f"{settings.api_prefix}/traffic",
        response_model=TrafficOverlayResponse,
        tags=["graph"],
    )
    def traffic(
        scenario: Annotated[ScenarioName, Query(description="Deterministic traffic overlay")],
        engine: RoutingEngine = Depends(engine_from_request),  # noqa: B008
    ) -> dict[str, Any]:
        return engine.traffic_payload(scenario.value)

    @application.post(
        f"{settings.api_prefix}/search",
        response_model=SearchResponse,
        tags=["routing"],
    )
    def search(
        payload: SearchRequest,
        engine: RoutingEngine = Depends(engine_from_request),  # noqa: B008
    ) -> dict[str, Any]:
        return engine.search(
            start_id=payload.start_id,
            goal_id=payload.goal_id,
            algorithm=payload.algorithm.value,
            heuristic=payload.heuristic.value,
            scenario=payload.scenario.value,
            weights=payload.cost_weights.to_domain(),
            include_trace=payload.include_trace,
            max_trace_events=payload.max_trace_events,
            max_expansions=payload.max_expansions,
            include_alternative=payload.include_alternative,
        )

    @application.post(
        f"{settings.api_prefix}/compare",
        response_model=CompareResponse,
        tags=["routing"],
    )
    def compare(
        payload: CompareRequest,
        engine: RoutingEngine = Depends(engine_from_request),  # noqa: B008
    ) -> dict[str, Any]:
        return engine.compare(
            start_id=payload.start_id,
            goal_id=payload.goal_id,
            algorithms=[algorithm.value for algorithm in payload.algorithms],
            heuristic=payload.heuristic.value,
            scenario=payload.scenario.value,
            weights=payload.cost_weights.to_domain(),
            include_trace=payload.include_trace,
            max_trace_events=payload.max_trace_events,
            max_expansions=payload.max_expansions,
        )

    @application.post(
        f"{settings.api_prefix}/multi-route",
        response_model=MultiRouteResponse,
        tags=["routing"],
    )
    def multi_route(
        payload: MultiRouteRequest,
        engine: RoutingEngine = Depends(engine_from_request),  # noqa: B008
    ) -> dict[str, Any]:
        return engine.multi_route(
            start_id=payload.start_id,
            stop_ids=payload.stop_ids,
            method=payload.method.value,
            return_to_start=payload.return_to_start,
            scenario=payload.scenario.value,
            weights=payload.cost_weights.to_domain(),
            seed=payload.seed,
            max_iterations=payload.max_iterations,
            max_expansions=payload.max_expansions,
        )

    return application


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
