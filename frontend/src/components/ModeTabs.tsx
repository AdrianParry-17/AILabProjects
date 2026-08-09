import { memo } from "react";
import { BookOpen, GitCompareArrows, MapPinned, Route } from "lucide-react";
import type { PlannerMode } from "../types";

const tabs: { id: PlannerMode; label: string; icon: typeof Route }[] = [
  { id: "route", label: "Tìm tuyến", icon: Route },
  { id: "multi", label: "Nhiều điểm", icon: MapPinned },
  { id: "compare", label: "So sánh", icon: GitCompareArrows },
  { id: "learn", label: "Thuật toán", icon: BookOpen },
];

export const ModeTabs = memo(function ModeTabs({ value, onChange }: { value: PlannerMode; onChange: (value: PlannerMode) => void }) {
  return (
    <nav className="mode-tabs" aria-label="Chế độ phòng lab">
      {tabs.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          className={value === id ? "active" : ""}
          onClick={() => onChange(id)}
        >
          <Icon size={16} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
});
