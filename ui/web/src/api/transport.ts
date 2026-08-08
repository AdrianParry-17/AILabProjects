/**
 * Transport abstraction (IMPLEMENTATION_PLAN.md §E.1/E.2).
 *
 * `client.ts` is the only public API for components. It instantiates one
 * transport from `VITE_API_MODE` (mock|http) so switching modes never touches
 * component code. Both transports map failures to the same `ErrorEnvelope`
 * shape, giving the UI a single error path.
 */

import type {
  AlgorithmsResponse,
  ErrorEnvelope,
  GraphResponse,
  HealthResponse,
  HistoryResponse,
  SearchResponse,
  VersionResponse,
} from "./types";

/** A §7 error raised by any transport when a request fails. */
export class ApiError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown> | undefined;

  constructor(code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
  }
}

/** Normalize a JSON body into a typed ErrorEnvelope (or throw if malformed). */
export function parseErrorEnvelope(body: unknown): ErrorEnvelope | null {
  if (typeof body !== "object" || body === null) return null;
  const candidate = body as { error?: unknown };
  const error = candidate.error;
  if (typeof error !== "object" || error === null) return null;
  const envelope = error as { code?: unknown; message?: unknown; details?: unknown };
  if (typeof envelope.code !== "string" || typeof envelope.message !== "string") {
    return null;
  }
  return {
    error: {
      code: envelope.code,
      message: envelope.message,
      details:
        typeof envelope.details === "object" && envelope.details !== null
          ? (envelope.details as Record<string, unknown>)
          : undefined,
    },
  };
}

/** Converts a failed HTTP response into a typed ApiError. */
export async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  const envelope = parseErrorEnvelope(body);
  if (envelope) {
    return new ApiError(envelope.error.code, envelope.error.message, envelope.error.details);
  }
  return new ApiError("HTTP_ERROR", `Request failed with status ${response.status}`);
}

export interface Transport {
  getGraph(): Promise<GraphResponse>;
  getHealth(): Promise<HealthResponse>;
  search(
    algorithm: string,
    start: string,
    goal: string,
    enableLogging?: boolean,
  ): Promise<SearchResponse>;
  listAlgorithms(): Promise<AlgorithmsResponse>;
  getHistory(): Promise<HistoryResponse>;
  getVersion(): Promise<VersionResponse>;
}