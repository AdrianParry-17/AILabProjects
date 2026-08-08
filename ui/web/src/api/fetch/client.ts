/**
 * Real HTTP transport. Talks to the GUI service (`GET /api/graph`,
 * `GET /api/health`, `POST /api/search`, `GET /api/algorithms`,
 * `GET /api/history`, `GET /api/version`) and maps failures to the §7
 * `ErrorEnvelope`. JSON request/response bodies use snake_case (§11).
 */

import { toApiError, type Transport } from "../transport";
import type {
  AlgorithmsResponse,
  GraphResponse,
  HealthResponse,
  HistoryResponse,
  SearchResponse,
  VersionResponse,
} from "../types";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api";

function baseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;
}

export class FetchClient implements Transport {
  async getGraph(): Promise<GraphResponse> {
    return this.request<GraphResponse>("/graph");
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health");
  }

  async search(
    algorithm: string,
    start: string,
    goal: string,
    enableLogging = true,
  ): Promise<SearchResponse> {
    return this.request<SearchResponse>("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ algorithm, start, goal, enable_logging: enableLogging }),
    });
  }

  async listAlgorithms(): Promise<AlgorithmsResponse> {
    return this.request<AlgorithmsResponse>("/algorithms");
  }

  async getHistory(): Promise<HistoryResponse> {
    return this.request<HistoryResponse>("/history");
  }

  async getVersion(): Promise<VersionResponse> {
    return this.request<VersionResponse>("/version");
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const headers = new Headers({ Accept: "application/json" });
    if (init?.headers) {
      new Headers(init.headers).forEach((value, key) => headers.set(key, value));
    }
    const response = await fetch(`${baseUrl()}${path}`, { ...init, headers });
    if (!response.ok) {
      throw await toApiError(response);
    }
    return (await response.json()) as T;
  }
}