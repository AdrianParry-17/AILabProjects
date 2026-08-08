import { useEffect } from "react";

import { Header } from "./components/Header";
import { GraphPane } from "./components/GraphPane";
import { InfoPanel } from "./components/InfoPanel";
import { Sidebar } from "./components/Sidebar";
import { StepTimeline } from "./components/StepTimeline";
import { useStore } from "./state/store";
import styles from "./styles/shell.module.css";

/**
 * App shell (UI_IMPLEMENTATION_PLAN.md §7 T04, LAYOUT_SPEC §3). Five-region
 * layout: fixed header, 3-column body (left sidebar | GraphPane | right panel),
 * docked bottom timeline. Boots the store once; downstream panels own their
 * own state subscriptions. No store / API / SearchResult changes here.
 */
function App(): JSX.Element {
  const loadGraph = useStore((s) => s.loadGraph);
  const loadHistory = useStore((s) => s.loadHistory);
  const loadCatalog = useStore((s) => s.loadCatalog);
  const loadBackendInfo = useStore((s) => s.loadBackendInfo);

  useEffect(() => {
    void loadGraph();
    void loadHistory();
    void loadCatalog();
    void loadBackendInfo();
  }, [loadGraph, loadHistory, loadCatalog, loadBackendInfo]);

  return (
    <div className={styles.shell}>
      <Header />
      <div className={styles.body}>
        <Sidebar />
        <main className={styles.main} role="main">
          <GraphPane />
        </main>
        <aside className={styles.rightPanel} aria-label="Information" data-testid="right-panel-slot">
          <InfoPanel />
        </aside>
      </div>
      <footer className={styles.dock} aria-label="Playback timeline" data-testid="timeline-dock">
        <StepTimeline />
      </footer>
      <div className={styles.narrowNotice} role="status" aria-label="Best viewed at 768 pixels or wider">
        Best viewed at &ge; 768 px
      </div>
    </div>
  );
}

export default App;