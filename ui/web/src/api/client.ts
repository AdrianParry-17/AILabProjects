/**
 * Public client API (IMPLEMENTATION_PLAN.md §E.2). Components import ONLY from
 * this module. The transport is chosen once from `VITE_API_MODE`:
 * - "mock" (default): serves §11 fixtures, no backend required.
 * - "http": talks to the GUI service.
 * Switching modes requires zero component changes.
 */

import { FetchClient } from "./fetch/client";
import { MockClient } from "./mock/client";
import type { Transport } from "./transport";

let transport: Transport | null = null;

function mode(): "mock" | "http" {
  const value = import.meta.env.VITE_API_MODE ?? "mock";
  return value === "http" ? "http" : "mock";
}

/** Return the (lazily-created) transport selected by VITE_API_MODE. */
export function getTransport(): Transport {
  if (transport === null) {
    transport = mode() === "http" ? new FetchClient() : new MockClient();
  }
  return transport;
}

export const client: Transport = {
  getGraph: () => getTransport().getGraph(),
  getHealth: () => getTransport().getHealth(),
  search: (algorithm, start, goal, enableLogging) =>
    getTransport().search(algorithm, start, goal, enableLogging),
  listAlgorithms: () => getTransport().listAlgorithms(),
  getHistory: () => getTransport().getHistory(),
  getVersion: () => getTransport().getVersion(),
};

export { ApiError, parseErrorEnvelope, toApiError } from "./transport";
export type { Transport } from "./transport";
export type {
  AlgorithmSummary,
  AlgorithmsResponse,
  DeliveryEdge,
  DeliveryNode,
  ErrorEnvelope,
  GraphGeojson,
  GraphResponse,
  HealthResponse,
  HistoryResponse,
  HistoryRun,
  RouteFeature,
  SearchMetrics,
  SearchResponse,
  SearchResult,
  SearchStep,
  VersionResponse,
} from "./types";
