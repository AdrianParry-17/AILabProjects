import { Activity, Bike, CloudRain, Database, Radio, ShieldCheck } from "lucide-react";
import { memo, type ReactNode } from "react";

interface Props {
  online: boolean;
  scenarioName: string;
  children: ReactNode;
}

export const AppHeader = memo(function AppHeader({ online, scenarioName }: Pick<Props, "online" | "scenarioName">) {
  return (
    <header className="app-header">
      <div className="brand-lockup">
        <div className="brand-mark"><Bike size={24} strokeWidth={2.2} /></div>
        <div>
          <div className="eyebrow">HCMC URBAN DELIVERY • AI SEARCH LAB</div>
          <h1>HCMC Delivery Intelligence</h1>
        </div>
      </div>
      <div className="header-signals">
        <div className="signal-chip"><CloudRain size={15} /> {scenarioName}</div>
        <div className="signal-chip"><Database size={15} /> OSM snapshot</div>
        <div className={`signal-chip ${online ? "is-live" : "is-offline"}`}>
          {online ? <Radio size={15} /> : <Activity size={15} />}
          {online ? "Engine online" : "Backend offline"}
        </div>
        <div className="safety-chip"><ShieldCheck size={16} /> offline teaching graph</div>
      </div>
    </header>
  );
});

export function AppShell({ online, scenarioName, children }: Props) {
  return (
    <div className="app-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />
      <AppHeader online={online} scenarioName={scenarioName} />
      {children}
      <footer className="app-footer">
        <span>© OpenStreetMap contributors • ODbL</span>
        <span>Travel time, traffic and risk are educational estimates—not live navigation guidance.</span>
      </footer>
    </div>
  );
}
