import { useId, useState } from "react";

import type { AlgorithmSummary } from "../../api/types";
import styles from "./index.module.css";

interface AlgorithmSelectorProps {
  catalog: readonly AlgorithmSummary[];
  value: string | null;
  disabled?: boolean;
  onChange: (id: string) => void;
}

/** Sim (mock) provider glyph — decorative. */
function SimIcon(): JSX.Element {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path d="M9 3h6v4l4 5a2 2 0 0 1-2 3H7a2 2 0 0 1-2-3l4-5V3Z" strokeLinejoin="round" />
      <path d="M7 21h10" strokeLinecap="round" />
    </svg>
  );
}

/** Real provider glyph — decorative. */
function RealIcon(): JSX.Element {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <circle cx="12" cy="12" r="8" />
      <path d="m8 12 3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * AlgorithmSelector (§2.3 / D.4): a catalog-driven combobox. Mock providers are
 * tagged from catalog metadata only — the component never branches on names.
 */
export function AlgorithmSelector({
  catalog,
  value,
  disabled = false,
  onChange,
}: AlgorithmSelectorProps): JSX.Element {
  const listId = `${useId()}-list`;
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);

  const selected = catalog.find((a) => a.id === value) ?? null;

  function select(id: string): void {
    onChange(id);
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLButtonElement>): void {
    if (disabled) return;
    const count = Math.max(catalog.length, 1);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setHighlight((h) => (h + 1) % count);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setOpen(true);
      setHighlight((h) => (h - 1 + count) % count);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (open && catalog[highlight]) select(catalog[highlight].id);
      else setOpen(true);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    }
  }

  return (
    <div className={styles.wrap}>
      <span className={styles.label}>Algorithm</span>
      <button
        type="button"
        className={styles.trigger}
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listId}
        aria-activedescendant={
          open && catalog[highlight] ? `algo-option-${catalog[highlight].id}` : undefined
        }
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKeyDown}
      >
        <span className={styles.triggerText}>{selected ? selected.label : "Choose Algorithm…"}</span>
        <svg
          className={styles.chevron}
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open ? (
        <ul id={listId} className={styles.menu} role="listbox" aria-label="Algorithm list">
          {catalog.map((algo, i) => (
            <li
              key={algo.id}
              id={`algo-option-${algo.id}`}
              role="option"
              aria-selected={algo.id === value}
              className={`${styles.item}${i === highlight ? ` ${styles.highlight}` : ""}`}
              onMouseDown={(e) => {
                e.preventDefault();
                select(algo.id);
              }}
              onMouseEnter={() => setHighlight(i)}
            >
              <span className={styles.itemIcon}>{algo.mock ? <SimIcon /> : <RealIcon />}</span>
              <span className={styles.itemLabel}>{algo.label}</span>
              {algo.mock ? (
                <span className={styles.mockTag} aria-hidden="true">
                  (mock)
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}