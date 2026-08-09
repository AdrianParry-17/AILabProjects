import { useStore } from "../../state/store";
import styles from "./index.module.css";

/**
 * Header (UI_TASK_BREAKDOWN §7 T14, COMPONENT_POLISH_SPEC §3, LAYOUT_SPEC §5,
 * UI_POLISH_SPEC §5). 64 px high, white surface, bottom border only. Left:
 * app logo + title. Right: backend connection status (probed once at boot
 * via the existing `client.getHealth` transport — see store.loadBackendInfo),
 * API version (existing `client.getVersion` transport), and a read-only
 * renderer indicator pill.
 *
 * Renderer-control ownership (UI_TASK_BREAKDOWN T14, locked): the pill is a
 * read-only indicator — it is NOT a control. The only interactive renderer
 * control is the segmented `RendererToggle` in `GraphPane` (T08). Clicking
 * the pill is intentionally a no-op; focusable disabled so keyboard users
 * discover the indicator without acting on it.
 */
export function Header(): JSX.Element {
  const backendOk = useStore((s) => s.backendOk);
  const version = useStore((s) => s.version);
  const renderer = useStore((s) => s.renderer);

  const backendText = backendOk == null ? "Checking…" : backendOk ? "Backend connected" : "Backend offline";
  const rendererText = renderer === "map" ? "Map view" : "Graph view";

  // T22: version lifecycle. While backendOk is unresolved we render a
  // placeholder skeleton; once backendOk is known but version never arrived
  // (the version probe failed), surface an inline indicator with no retry —
  // retry is reserved for the exhaustive list of retry-bearing errors.
  const versionSkeleton = backendOk == null;
  const versionError = backendOk === false && version == null;

  return (
    <header className={styles.header} role="banner">
      <div className={styles.brand}>
        <span className={styles.logo} aria-hidden="true">
          {/* Decorative logo glyph (LAYOUT_SPEC §5: app logo + title left). */}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 12h4l3-7 4 14 3-7h4" />
          </svg>
        </span>
        <span className={styles.title}>HCMC Delivery AI Search</span>
      </div>
      <div className={styles.right}>
        <span
          className={styles.status}
          data-state={backendOk == null ? "pending" : backendOk ? "ok" : "down"}
          aria-live="polite"
        >
          <span className={styles.statusDot} aria-hidden="true" />
          {backendText}
        </span>
        {version ? (
          <span className={styles.version} aria-label={`API version ${version}`}>
            v{version}
          </span>
        ) : versionSkeleton ? (
          <span className={`${styles.version} ${styles.versionSkeleton}`} aria-label="Loading API version" aria-busy="true" />
        ) : versionError ? (
          <span className={`${styles.version} ${styles.versionError}`} role="status" data-testid="version-error" aria-label="API version unavailable">
            v—
          </span>
        ) : null}
        <span
          className={styles.pill}
          aria-label={`Active renderer: ${rendererText}`}
          data-renderer={renderer}
        >
          {rendererText}
        </span>
      </div>
    </header>
  );
}
