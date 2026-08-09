import { useId, useMemo, useRef, useState } from "react";

import type { AlgorithmSummary } from "../../api/types";
import { Badge } from "../shared/Badge";
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
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path d="M9 3h6v4l4 5a2 2 0 0 1-2 3H7a2 2 0 0 1-2-3l4-5V3Z" strokeLinejoin="round" />
      <path d="M7 21h10" strokeLinecap="round" />
    </svg>
  );
}

/** Real provider glyph — decorative. */
function RealIcon(): JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <circle cx="12" cy="12" r="8" />
      <path d="m8 12 3 3 5-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * AlgorithmSelector (UI_TASK_BREAKDOWN §7 T17, COMPONENT_POLISH_SPEC §6): a
 * catalog-driven combobox. Mock providers are tagged from catalog metadata
 * only — the component never branches on names. The dropdown includes a
 * search input that filters the catalog by label (case-insensitive).
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
  const [query, setQuery] = useState("");
  const triggerRef = useRef<HTMLButtonElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const selected = catalog.find((a) => a.id === value) ?? null;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return catalog;
    return catalog.filter((a) => a.label.toLowerCase().includes(q));
  }, [catalog, query]);

  function closeDropdown(returnFocus: boolean): void {
    setOpen(false);
    setQuery("");
    if (returnFocus) triggerRef.current?.focus();
  }

  function select(id: string, returnFocus: boolean): void {
    onChange(id);
    setOpen(false);
    setQuery("");
    if (returnFocus) triggerRef.current?.focus();
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLButtonElement | HTMLInputElement>): void {
    if (disabled) return;
    const count = Math.max(filtered.length, 1);
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
      if (open && filtered[highlight]) {
        // Selecting via Enter from the search input must return focus to
        // the trigger — the input unmounts on close and focus would
        // otherwise fall to <body> (same rule as Escape/mouse selection).
        const returnFocus = searchRef.current?.matches(":focus") ?? false;
        select(filtered[highlight].id, returnFocus);
      } else setOpen(true);
    } else if (e.key === "Escape") {
      e.preventDefault();
      // Restore focus to the trigger when closing from the search input —
      // the input itself unmounts on close and focus would otherwise land on
      // <body>, dropping the user out of the combobox (COMPONENT_POLISH §24).
      const returnFocus = searchRef.current?.matches(":focus") ?? false;
      closeDropdown(returnFocus);
    }
  }

  return (
    <div className={styles.wrap}>
      <span className={styles.label}>Algorithm</span>
      <button
        type="button"
        ref={triggerRef}
        className={styles.trigger}
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listId}
        aria-activedescendant={
          open && filtered[highlight] ? `algo-option-${filtered[highlight].id}` : undefined
        }
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKeyDown}
      >
        <span className={styles.triggerText}>{selected ? selected.label : "Choose Algorithm…"}</span>
        <svg
          className={styles.chevron}
          width="16"
          height="16"
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
        <div className={styles.menu} role="presentation">
          <input
            ref={searchRef}
            type="text"
            className={styles.search}
            placeholder="Search algorithms…"
            autoComplete="off"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setHighlight(0);
            }}
            aria-label="Filter algorithm list"
            onKeyDown={(e) => {
              if (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === "Escape") {
                onKeyDown(e);
              }
            }}
          />
          <ul id={listId} className={styles.list} role="listbox" aria-label="Algorithm list">
            {filtered.length === 0 ? (
              <li className={styles.empty} role="status">
                No matching algorithms.
              </li>
            ) : (
              filtered.map((algo, i) => (
                <li
                  key={algo.id}
                  id={`algo-option-${algo.id}`}
                  role="option"
                  aria-selected={algo.id === value}
                  className={`${styles.item}${i === highlight ? ` ${styles.highlight}` : ""}`}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    // mouseDown on the option was likely initiated from the
                    // search input → return focus to the trigger so keyboard
                    // users land back on the combobox trigger after pick.
                    const returnFocus = searchRef.current?.matches(":focus") ?? false;
                    select(algo.id, returnFocus);
                  }}
                  onMouseEnter={() => setHighlight(i)}
                >
                  <span className={styles.itemIcon}>{algo.mock ? <SimIcon /> : <RealIcon />}</span>
                  <span className={styles.itemLabel}>{algo.label}</span>
                  {algo.mock ? (
                    <Badge variant="warning">Mock</Badge>
                  ) : null}
                </li>
              ))
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
