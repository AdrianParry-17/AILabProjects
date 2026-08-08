import type { DeliveryNode } from "../../api/types";
import { kindLabel } from "../../lib/format";
import { Tooltip } from "../shared/Tooltip";
import styles from "./NodeListFallback.module.css";

interface NodeListFallbackProps {
  nodes: readonly DeliveryNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

/**
 * Keyboard-reachable accessibility fallback list of nodes (§A.11, §C.5). The
 * canvas is `role="img"`; this `<ul>` is the alternative text representation
 * so every node is reachable without a pointer. Each row carries the shared
 * Tooltip (T13) — name, id, type, coordinates — so graph mode has the same
 * tooltip semantics as map mode.
 */
export function NodeListFallback({ nodes, selectedId, onSelect }: NodeListFallbackProps): JSX.Element {
  return (
    <details className={styles.details}>
      <summary className={styles.summary}>List of delivery points</summary>
      <ul className={styles.list}>
        {nodes.map((node) => (
          <li key={node.id}>
            <Tooltip
              title={node.name}
              lines={[
                { label: "ID", value: node.id },
                { label: "Type", value: kindLabel(node.kind) },
                {
                  label: "Coords",
                  value: `${node.latitude.toFixed(4)}, ${node.longitude.toFixed(4)}`,
                },
              ]}
            >
              <button
                type="button"
                className={styles.item}
                aria-pressed={node.id === selectedId}
                onClick={() => onSelect(node.id)}
              >
                {node.name} · {kindLabel(node.kind)}
                {node.id === selectedId ? " (selected)" : ""}
              </button>
            </Tooltip>
          </li>
        ))}
      </ul>
    </details>
  );
}