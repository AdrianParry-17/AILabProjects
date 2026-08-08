import { useEffect, useState } from "react";
import L from "leaflet";

import type { Bounds } from "../../lib/coords";

/**
 * "Leaflet is not available in jsdom" guard: browser-only APIs (window,
 * navigator, document.createRange…) used by Leaflet are absent in the test
 * environment, so the map must never be initialised there (T11: jsdom-safe
 * tests). The container element is still rendered, and the overlay/render
 * pipeline stays unit-testable through the leaflet-free helpers.
 */
const IS_JSDOM =
  typeof navigator !== "undefined" && /jsdom/.test(navigator.userAgent ?? "");

export interface MapInstance {
  map: L.Map;
  tileLayer: L.TileLayer;
  /** Current camera (center + zoom). */
  getView: () => { center: L.LatLng; zoom: number };
}

/** Persistent camera across renderer switches (module-level, keyed per bbox
 *  signature) — the map is destroyed when the renderer switches, but the
 *  camera is restored "where the graph fits" (MAP_RENDERING_SPEC §4, T10). */
const cameraCache = new Map<string, { center: L.LatLng; zoom: number }>();

export function bboxSignature(bounds: Bounds): string {
  return [bounds.minLon, bounds.minLat, bounds.maxLon, bounds.maxLat]
    .map((v) => v.toFixed(5))
    .join(",");
}

/**
 * Leaflet lifecycle hook (T11): creates the map once per mounted container,
 * adds the OSM tile layer, clamps zoom to [10, 18], fits the graph bounds with
 * 40 px padding, and cleans up all listeners/layers on unmount.
 *
 * The hook is inert in jsdom (tests stay green); the container is rendered
 * regardless. `cameraCache` restores the previous camera across renderer
 * switches when the graph still fits (MAP_RENDERING_SPEC §4).
 */
export function useLeaflet(
  containerRef: React.RefObject<HTMLDivElement | null>,
  bounds: Bounds | null,
): {
  ready: boolean;
  view: MapInstance | null;
  error: string | null;
} {
  const [view, setView] = useState<MapInstance | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (IS_JSDOM || !container || !bounds || typeof L === "undefined") {
      setView(null);
      return;
    }

    let map: L.Map | null = null;
    let tileLayer: L.TileLayer | null = null;
    let disposed = false;

    try {
      map = L.map(container, {
        zoomControl: false,
        attributionControl: true,
        keyboard: true,
        doubleClickZoom: true,
        scrollWheelZoom: true,
        dragging: true,
        touchZoom: true,
        boxZoom: true,
        minZoom: 10,
        maxZoom: 18,
      });

      tileLayer = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        },
      );
      tileLayer.addTo(map);

      const signature = bboxSignature(bounds);
      const cached = cameraCache.get(signature);
      if (cached) {
        map.setView(cached.center, cached.zoom);
      } else {
        map.fitBounds(
          L.latLngBounds(
            [bounds.minLat, bounds.minLon],
            [bounds.maxLat, bounds.maxLon],
          ),
          { padding: [40, 40], maxZoom: 18 },
        );
      }

      const instance: MapInstance = {
        map,
        tileLayer,
        getView: () => ({ center: map!.getCenter(), zoom: map!.getZoom() }),
      };
      const onMoveEnd = (): void => {
        const v = instance.getView();
        const center = L.latLng(v.center.lat, v.center.lng);
        cameraCache.set(signature, { center, zoom: v.zoom });
      };
      map.on("moveend zoomend", onMoveEnd);

      if (!disposed) setView(instance);

      return () => {
        disposed = true;
        if (map) map.off();
        if (map) map.remove();
        map = null;
        tileLayer = null;
      };
    } catch (err) {
      if (!disposed) {
        setError(err instanceof Error ? err.message : "Leaflet failed to initialise.");
        setView(null);
      }
      return () => {
        disposed = true;
        if (map) map.off();
        if (map) map.remove();
        map = null;
        tileLayer = null;
      };
    }
  }, [containerRef, bounds]);

  return { ready: view !== null, view, error };
}