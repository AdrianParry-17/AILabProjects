"""Application service that composes graph, search, explanation and API payloads."""

from __future__ import annotations

import math
from dataclasses import asdict
from time import perf_counter
from typing import Any
from uuid import uuid4

from .algorithms import (
    ALGORITHM_METADATA,
    SearchOptions,
    SearchResult,
    algorithm_metadata,
    run_algorithm,
)
from .costs import CostCalculator, CostWeights
from .domain import DatasetMetadata, RoadGraph
from .errors import RoutingError
from .heuristics import HeuristicRegistry
from .multi_stop import MULTI_METHODS, multi_method_metadata, optimize_stop_order
from .traffic import SCENARIOS, TrafficModel


class RoutingEngine:
    def __init__(self, metadata: DatasetMetadata, graph: RoadGraph) -> None:
        self.dataset = metadata
        self.graph = graph
        self.traffic = TrafficModel()
        self.heuristics = HeuristicRegistry()

    def _ensure_node(self, node_id: str, role: str) -> None:
        if node_id not in self.graph.nodes:
            raise RoutingError(
                "unknown_node",
                f"Unknown {role} node {node_id!r}",
                details={"role": role, "node_id": node_id, "available_nodes": list(self.graph.nodes)},
            )

    def _calculator(self, scenario: str, weights: CostWeights) -> CostCalculator:
        try:
            return CostCalculator(self.graph, self.traffic, scenario, weights)
        except ValueError as exc:
            raise RoutingError("invalid_scenario", str(exc)) from exc

    def metadata_payload(self) -> dict[str, Any]:
        return {
            "api": {
                "name": "HCMC Delivery Route Lab API",
                "version": "2.0.0",
                "contract_version": "2026-08-09",
            },
            "dataset": asdict(self.dataset),
            "graph": self._graph_summary(),
            "algorithms": algorithm_metadata(),
            "heuristics": self.heuristics.metadata(),
            "scenarios": TrafficModel.scenario_metadata(),
            "multi_route_methods": multi_method_metadata(),
            "defaults": {
                "algorithm": "astar",
                "heuristic": "travel_time",
                "scenario": "normal",
                "cost_weights": CostWeights().as_dict(),
                "multi_route_method": "nearest_neighbor",
            },
            "trace_schema": {
                "version": "1.0",
                "events": [
                    "start", "iteration", "expand", "discover", "relax", "prune", "finish"
                ],
                "directions": ["forward", "backward"],
                "fields": [
                    "step", "event", "node_id", "parent_id", "edge_id", "direction",
                    "frontier_size", "explored_count", "g_cost", "h_cost", "f_cost",
                    "depth", "message",
                ],
            },
        }

    def _graph_summary(self) -> dict[str, Any]:
        latitudes = [node.lat for node in self.graph.nodes.values()]
        longitudes = [node.lon for node in self.graph.nodes.values()]
        return {
            "node_count": len(self.graph.nodes),
            "directed_edge_count": len(self.graph.edges),
            "distance_lower_bound_scale": round(self.graph.distance_lower_bound_scale, 9),
            "max_speed_kph": self.graph.max_speed_kph,
            "bounding_box": {
                "south": min(latitudes),
                "west": min(longitudes),
                "north": max(latitudes),
                "east": max(longitudes),
            },
        }

    def graph_payload(
        self,
        scenario: str,
        *,
        include_geojson: bool = False,
        compact: bool = False,
    ) -> dict[str, Any]:
        try:
            TrafficModel.validate_scenario(scenario)
        except ValueError as exc:
            raise RoutingError("invalid_scenario", str(exc)) from exc
        compact_node_keys = {
            "delivery_destination", "delivery_category", "routing_component",
            "district", "address", "osm_type", "osm_id",
        }
        nodes = []
        for node in self.graph.nodes.values():
            node_attributes = dict(node.attributes)
            if compact:
                node_attributes = {
                    key: value for key, value in node_attributes.items() if key in compact_node_keys
                }
            nodes.append(
                {
                    "id": node.id,
                    "name": node.name,
                    "kind": node.kind,
                    "lat": node.lat,
                    "lon": node.lon,
                    "attributes": node_attributes,
                }
            )
        edges: list[dict[str, Any]] = []
        graph_features: list[dict[str, Any]] = []
        for edge in self.graph.edges.values():
            status = self.traffic.status(edge, scenario)
            geometry = self.graph.edge_coordinates(edge.id)
            public_attributes = {
                key: value for key, value in edge.attributes.items() if key != "geometry"
            }
            if compact:
                compact_edge_keys = {
                    "source_direction", "base_congestion", "bridge", "flood_prone",
                    "incident_prone", "close_during_incident", "synthetic_access_connector",
                }
                public_attributes = {
                    key: value for key, value in public_attributes.items() if key in compact_edge_keys
                }
            source_direction = str(edge.attributes.get("source_direction", "directed"))
            if source_direction not in {"one-way", "two-way"}:
                source_direction = "directed"
            edges.append(
                {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "distance_m": edge.distance_m,
                "speed_kph": edge.speed_kph,
                "road_name": edge.road_name,
                "road_class": edge.road_class,
                "risk": edge.risk,
                "traversable": edge.traversable,
                "direction": source_direction,
                # Geometry has a dedicated field below. Omitting it here avoids
                # making the browser parse a second identical coordinate array.
                "attributes": public_attributes,
                "geometry": geometry,
                "traffic": status.as_dict(),
            }
            )
            if include_geojson:
                graph_features.append(
                {
                    "type": "Feature",
                    "id": edge.id,
                    "properties": {
                        "edge_id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "road_name": edge.road_name,
                        "road_class": edge.road_class,
                        "distance_m": edge.distance_m,
                        "scenario": scenario,
                        "congestion": status.congestion,
                        "closed": status.closed,
                        "multiplier": status.multiplier,
                    },
                    "geometry": {"type": "LineString", "coordinates": geometry},
                }
                )
        return {
            "dataset": asdict(self.dataset),
            "summary": self._graph_summary(),
            "scenario": asdict(SCENARIOS[scenario]),
            "nodes": nodes,
            "directed_edges": edges,
            "graph_geojson": {"type": "FeatureCollection", "features": graph_features},
        }

    def traffic_payload(self, scenario: str) -> dict[str, Any]:
        """Return only mutable scenario fields, without repeating graph topology."""

        try:
            TrafficModel.validate_scenario(scenario)
        except ValueError as exc:
            raise RoutingError("invalid_scenario", str(exc)) from exc
        return {
            "scenario": asdict(SCENARIOS[scenario]),
            "edges": [
                {
                    "edge_id": status.edge_id,
                    "multiplier": status.multiplier,
                    "effective_speed_kph": status.effective_speed_kph,
                    "travel_time_s": status.travel_time_s,
                    "congestion": status.congestion,
                    "closed": status.closed,
                }
                for edge in self.graph.edges.values()
                for status in [self.traffic.status(edge, scenario)]
            ],
        }

    def search(
        self,
        *,
        start_id: str,
        goal_id: str,
        algorithm: str,
        heuristic: str,
        scenario: str,
        weights: CostWeights,
        include_trace: bool,
        max_trace_events: int,
        max_expansions: int,
        include_alternative: bool,
    ) -> dict[str, Any]:
        self._ensure_node(start_id, "start")
        self._ensure_node(goal_id, "goal")
        calculator = self._calculator(scenario, weights)
        try:
            result = run_algorithm(
                self.graph,
                calculator,
                self.heuristics,
                algorithm,
                heuristic,
                start_id,
                goal_id,
                SearchOptions(
                    include_trace=include_trace,
                    max_trace_events=max_trace_events,
                    max_expansions=max_expansions,
                ),
            )
        except ValueError as exc:
            raise RoutingError("invalid_search_configuration", str(exc)) from exc

        alternative = None
        if include_alternative and result.found and result.edge_ids:
            alternative = self._alternative_route(
                result, calculator, start_id, goal_id, max_expansions
            )
        return self._search_payload(result, calculator, alternative)

    def _search_payload(
        self,
        result: SearchResult,
        calculator: CostCalculator,
        alternative: dict[str, Any] | None,
    ) -> dict[str, Any]:
        algorithm_info = asdict(ALGORITHM_METADATA[result.algorithm])
        heuristic_info = asdict(self.heuristics.get_metadata(result.heuristic))
        heuristic_info["used"] = ALGORITHM_METADATA[result.algorithm].heuristic_required
        breakdown = calculator.aggregate(result.edge_ids)
        metrics = dict(result.metrics)
        metrics.update(
            {
                "distance_m": breakdown["distance_m"],
                "free_flow_time_s": breakdown["free_flow_time_s"],
                "travel_time_s": breakdown["travel_time_s"],
                "traffic_delay_s": breakdown["traffic_delay_s"],
                "risk_exposure": breakdown["risk_exposure"],
            }
        )
        return {
            "request_id": str(uuid4()),
            "status": result.status,
            "found": result.found,
            "start_id": result.start_id,
            "goal_id": result.goal_id,
            "algorithm": algorithm_info,
            "heuristic": heuristic_info,
            "scenario": asdict(SCENARIOS[calculator.scenario]),
            "path": result.path,
            "edge_ids": result.edge_ids,
            "route_geojson": self.graph.route_geojson(result.path, result.edge_ids),
            "metrics": metrics,
            "trace": {
                "schema_version": "1.0",
                "event_count": len(result.trace_events),
                "truncated": result.trace_truncated,
                "events": result.trace_events,
            },
            "explanation": self._explain(result, calculator),
            "alternative": alternative,
            "cost_breakdown": breakdown,
        }

    def _explain(self, result: SearchResult, calculator: CostCalculator) -> dict[str, Any]:
        algorithm = ALGORITHM_METADATA[result.algorithm]
        heuristic = self.heuristics.get_metadata(result.heuristic)
        warnings: list[str] = []
        if algorithm.heuristic_required and not heuristic.admissible:
            warnings.append(heuristic.warning or "The selected heuristic can overestimate.")
        if result.algorithm in {"bfs", "dfs", "greedy_best_first"}:
            warnings.append("This algorithm does not guarantee the lowest weighted route cost.")
        if result.trace_truncated:
            warnings.append("Trace events were truncated at the requested limit.")
        if self.dataset.disclaimer:
            warnings.append(self.dataset.disclaimer)
        if result.found:
            summary = (
                f"{algorithm.label} found a {len(result.edge_ids)}-edge route with "
                f"weighted cost {result.total_cost:.6f}."
            )
        else:
            summary = (
                "Search stopped at the expansion limit before finding a route."
                if result.status == "limit_reached"
                else "No traversable route exists for the selected traffic scenario."
            )
        optimality = algorithm.optimality
        if algorithm.heuristic_required and not heuristic.admissible:
            optimality += " The selected heuristic removes the optimality guarantee."
        return {
            "summary": summary,
            "optimality": optimality,
            "heuristic_note": (
                f"{heuristic.label}: {heuristic.description}"
                if algorithm.heuristic_required
                else f"{algorithm.label} does not use the selected heuristic."
            ),
            "traffic_note": SCENARIOS[calculator.scenario].description,
            "cost_model": (
                "total = w_distance·kilometres + w_time·minutes + "
                "w_delay·delay-minutes + w_risk·(risk×kilometres); weights are normalized"
            ),
            "warnings": warnings,
        }

    def _alternative_route(
        self,
        primary: SearchResult,
        calculator: CostCalculator,
        start_id: str,
        goal_id: str,
        max_expansions: int,
    ) -> dict[str, Any] | None:
        best: SearchResult | None = None
        blocked_for_best: str | None = None
        # Removing each primary edge is a compact deterministic alternative-route
        # strategy. It is intentionally bounded by the primary path length.
        for blocked_edge in dict.fromkeys(primary.edge_ids):
            candidate = run_algorithm(
                self.graph,
                calculator,
                self.heuristics,
                "dijkstra",
                "zero",
                start_id,
                goal_id,
                SearchOptions(
                    include_trace=False,
                    max_trace_events=0,
                    max_expansions=max_expansions,
                    blocked_edge_ids=frozenset({blocked_edge}),
                ),
            )
            if not candidate.found or candidate.edge_ids == primary.edge_ids:
                continue
            if best is None or (candidate.total_cost or math.inf) < (best.total_cost or math.inf):
                best = candidate
                blocked_for_best = blocked_edge
        if best is None:
            return None
        breakdown = calculator.aggregate(best.edge_ids)
        primary_cost = primary.total_cost or 0.0
        difference = (
            ((best.total_cost or 0.0) - primary_cost) / primary_cost * 100
            if primary_cost > 0
            else None
        )
        return {
            "algorithm": "dijkstra",
            "reason": f"Best route found while excluding primary edge {blocked_for_best}.",
            "path": best.path,
            "edge_ids": best.edge_ids,
            "route_geojson": self.graph.route_geojson(best.path, best.edge_ids),
            "difference_percent": round(difference, 6) if difference is not None else None,
            "metrics": best.metrics,
            "cost_breakdown": breakdown,
        }

    def compare(
        self,
        *,
        start_id: str,
        goal_id: str,
        algorithms: list[str],
        heuristic: str,
        scenario: str,
        weights: CostWeights,
        include_trace: bool,
        max_trace_events: int,
        max_expansions: int,
    ) -> dict[str, Any]:
        if len(set(algorithms)) != len(algorithms):
            raise RoutingError("duplicate_algorithms", "Comparison algorithms must be unique")
        runs = [
            self.search(
                start_id=start_id,
                goal_id=goal_id,
                algorithm=algorithm,
                heuristic=heuristic,
                scenario=scenario,
                weights=weights,
                include_trace=include_trace,
                max_trace_events=max_trace_events,
                max_expansions=max_expansions,
                include_alternative=False,
            )
            for algorithm in algorithms
        ]
        ranked = sorted(
            runs,
            key=lambda run: (
                not run["found"],
                run["metrics"]["path_cost"] if run["metrics"]["path_cost"] is not None else math.inf,
                run["metrics"]["expanded_nodes"],
                run["algorithm"]["id"],
            ),
        )
        ranking = [
            {
                "rank": index + 1,
                "algorithm": run["algorithm"]["id"],
                "found": run["found"],
                "path_cost": run["metrics"]["path_cost"],
                "expanded_nodes": run["metrics"]["expanded_nodes"],
                "runtime_ms": run["metrics"]["runtime_ms"],
            }
            for index, run in enumerate(ranked)
        ]
        path_groups: dict[tuple[str, ...], list[str]] = {}
        for run in runs:
            if run["found"]:
                path_groups.setdefault(tuple(run["edge_ids"]), []).append(run["algorithm"]["id"])
        return {
            "request_id": str(uuid4()),
            "start_id": start_id,
            "goal_id": goal_id,
            "scenario": asdict(SCENARIOS[scenario]),
            "runs": runs,
            "ranking": ranking,
            "best_algorithm": ranking[0]["algorithm"] if ranking and ranking[0]["found"] else None,
            "agreement": {
                "all_found": all(run["found"] for run in runs),
                "same_path": len(path_groups) == 1 and bool(path_groups),
                "unique_path_count": len(path_groups),
                "path_groups": [
                    {"edge_ids": list(path), "algorithms": names}
                    for path, names in path_groups.items()
                ],
            },
        }

    def multi_route(
        self,
        *,
        start_id: str,
        stop_ids: list[str],
        method: str,
        return_to_start: bool,
        scenario: str,
        weights: CostWeights,
        seed: int,
        max_iterations: int,
        max_expansions: int,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        self._ensure_node(start_id, "start")
        if start_id in stop_ids:
            raise RoutingError("duplicate_start", "stop_ids must not contain start_id")
        if len(set(stop_ids)) != len(stop_ids):
            raise RoutingError("duplicate_stops", "stop_ids must be unique")
        for index, stop_id in enumerate(stop_ids):
            self._ensure_node(stop_id, f"stop[{index}]")
        if method not in MULTI_METHODS:
            raise RoutingError("invalid_multi_route_method", f"Unknown multi-route method {method!r}")
        if method == "held_karp" and len(stop_ids) > 10:
            raise RoutingError("too_many_stops", "Held-Karp accepts at most 10 stops")

        calculator = self._calculator(scenario, weights)
        locations = [start_id, *stop_ids]
        pair_results: dict[tuple[str, str], SearchResult] = {}
        matrix: dict[tuple[str, str], float] = {}
        total_pair_expansions = 0
        for source in locations:
            for target in locations:
                if source == target:
                    matrix[(source, target)] = 0.0
                    continue
                result = run_algorithm(
                    self.graph,
                    calculator,
                    self.heuristics,
                    "dijkstra",
                    "zero",
                    source,
                    target,
                    SearchOptions(
                        include_trace=False,
                        max_trace_events=0,
                        max_expansions=max_expansions,
                    ),
                )
                pair_results[(source, target)] = result
                matrix[(source, target)] = result.total_cost if result.found else math.inf
                total_pair_expansions += result.metrics["expanded_nodes"]

        try:
            optimized = optimize_stop_order(
                method,
                start_id,
                stop_ids,
                matrix,
                return_to_start,
                seed=seed,
                max_iterations=max_iterations,
            )
        except ValueError as exc:
            raise RoutingError("multi_route_failed", str(exc)) from exc
        if not math.isfinite(optimized.total_cost):
            unreachable = [
                {"source": source, "target": target}
                for (source, target), value in matrix.items()
                if source != target and not math.isfinite(value)
            ]
            raise RoutingError(
                "multi_route_unreachable",
                "No route can visit every requested stop in the selected scenario",
                details={"unreachable_pairs": unreachable},
            )

        visit_sequence = [start_id, *optimized.order]
        if return_to_start:
            visit_sequence.append(start_id)
        combined_path: list[str] = []
        combined_edges: list[str] = []
        segments: list[dict[str, Any]] = []
        for source, target in zip(visit_sequence, visit_sequence[1:]):
            result = pair_results[(source, target)]
            breakdown = calculator.aggregate(result.edge_ids)
            if not combined_path:
                combined_path.extend(result.path)
            else:
                combined_path.extend(result.path[1:])
            combined_edges.extend(result.edge_ids)
            segments.append(
                {
                    "from_id": source,
                    "to_id": target,
                    "path": result.path,
                    "edge_ids": result.edge_ids,
                    "route_geojson": self.graph.route_geojson(result.path, result.edge_ids),
                    "cost_breakdown": breakdown,
                }
            )

        breakdown = calculator.aggregate(combined_edges)
        elapsed_ms = (perf_counter() - started_at) * 1000
        method_info = asdict(MULTI_METHODS[method])
        return {
            "request_id": str(uuid4()),
            "status": "found",
            "method": method_info,
            "scenario": asdict(SCENARIOS[scenario]),
            "start_id": start_id,
            "requested_stop_ids": stop_ids,
            "stop_order": optimized.order,
            "return_to_start": return_to_start,
            "visit_sequence": visit_sequence,
            "path": combined_path,
            "edge_ids": combined_edges,
            "route_geojson": self.graph.route_geojson(combined_path, combined_edges),
            "segments": segments,
            "metrics": {
                "runtime_ms": round(elapsed_ms, 6),
                "pairwise_searches": len(pair_results),
                "pairwise_expanded_nodes": total_pair_expansions,
                "optimizer_iterations": optimized.iterations,
                "optimizer_improvements": optimized.improvements,
                "stop_count": len(stop_ids),
                "hop_count": len(combined_edges),
                "path_cost": breakdown["total_cost"],
                "distance_m": breakdown["distance_m"],
                "travel_time_s": breakdown["travel_time_s"],
                "traffic_delay_s": breakdown["traffic_delay_s"],
            },
            "cost_breakdown": breakdown,
            "explanation": {
                "summary": (
                    f"{method_info['label']} ordered {len(stop_ids)} stops and produced "
                    f"a {len(combined_edges)}-edge route."
                ),
                "optimality": (
                    "Exact for the pairwise weighted-cost matrix."
                    if optimized.exact
                    else "Approximate stop ordering; pairwise segments are exact Dijkstra paths."
                ),
                "heuristic_note": "Pairwise paths use Dijkstra and do not use a heuristic.",
                "traffic_note": SCENARIOS[scenario].description,
                "cost_model": (
                    "Stop ordering minimizes the sum of pairwise weighted route costs under the selected scenario."
                ),
                "warnings": [self.dataset.disclaimer] if self.dataset.disclaimer else [],
            },
        }
