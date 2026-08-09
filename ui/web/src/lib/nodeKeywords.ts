import type { DeliveryNode } from "../api/types";

/** Build the searchable keyword blob (street, POI, etc.) from a
 *  DeliveryNode's free-form attributes without inventing a new contract.
 *  Both top-level string values and string[] array values (e.g. `road_names`)
 *  are flattened into the search text, joined with the node kind so kind still
 *  matches (e.g. typing "supermarket" finds delivery_supermarket nodes).
 *  Falls back to a blob containing just the kind for nodes that have no
 *  extra metadata. */
export function nodeKeywords(node: {
  kind: DeliveryNode["kind"];
  attributes?: DeliveryNode["attributes"];
}): string {
  const parts: string[] = [];
  if (node.attributes) {
    for (const value of Object.values(node.attributes)) {
      if (typeof value === "string") {
        const trimmed = value.trim();
        if (trimmed) parts.push(trimmed);
      } else if (Array.isArray(value)) {
        for (const item of value) {
          if (typeof item === "string" && item.trim()) parts.push(item.trim());
        }
      }
    }
  }
  parts.push(node.kind);
  return parts.join(" ");
}
