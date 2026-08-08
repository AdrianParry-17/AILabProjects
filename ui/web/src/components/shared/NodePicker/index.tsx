import { useEffect, useId, useMemo, useRef, useState } from "react";

import styles from "./index.module.css";

/** One selectable node option. The optional `keywords` field carries extra
 *  searchable text (street, POI type) sourced from the node attributes —
 *  the picker filters across all of these (T18, COMPONENT_POLISH_SPEC §7). */
export interface NodeOption {
  id: string;
  name: string;
  keywords?: string;
}

/** Subsequence fuzzy match: every char of `q` appears in `target` in order.
 *  Case-insensitive. Returns true when q is empty so callers can treat
 *  blank input as "no filter applied". */
function fuzzyMatch(q: string, target: string): boolean {
  if (!q) return true;
  const needle = q.toLowerCase();
  const hay = target.toLowerCase();
  let i = 0;
  for (let j = 0; j < hay.length && i < needle.length; j++) {
    if (hay[j] === needle[i]) i++;
  }
  return i === needle.length;
}

const MAX_RESULTS = 8;
const MAX_RECENT = 4;

interface NodePickerProps {
  label: string;
  value: string | null;
  options: readonly NodeOption[];
  disabled?: boolean;
  onChange: (id: string | null) => void;
}

/**
 * NodePicker (UI_TASK_BREAKDOWN §7 T18, COMPONENT_POLISH_SPEC §7): accessible
 * combobox that filters by id, name, and optional keywords (street / POI
 * metadata) using both substring and subsequence matching. Recent selections
 * are kept in component-local memory only (session-scoped, no persistence).
 * Maximum 8 visible results per spec.
 */
export function NodePicker({
  label,
  value,
  options,
  disabled = false,
  onChange,
}: NodePickerProps): JSX.Element {
  const baseId = useId();
  const inputId = `${baseId}-input`;
  const listId = `${baseId}-list`;
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const [recents, setRecents] = useState<string[]>([]);
  const lastValueRef = useRef<string | null>(value);

  // Push a freshly-picked id into the session-scoped recents (most-recent-first,
  // capped at MAX_RECENT). The ref guards against the effect firing on first
  // mount with the initial value — only "real" user selections are tracked.
  useEffect(() => {
    if (value == null || value === lastValueRef.current) {
      lastValueRef.current = value;
      return;
    }
    lastValueRef.current = value;
    setRecents((prev) => {
      const next = [value, ...prev.filter((id) => id !== value)];
      return next.slice(0, MAX_RECENT);
    });
  }, [value]);

  const selected = value ? options.find((o) => o.id === value) ?? null : null;

  const filtered = useMemo(() => {
    const q = query.trim();
    if (!q) return options.slice(0, MAX_RESULTS);
    const hits = options.filter((o) => {
      const blob = `${o.name}\n${o.id}\n${o.keywords ?? ""}`;
      return blob.toLowerCase().includes(q.toLowerCase()) || fuzzyMatch(q, blob);
    });
    return hits.slice(0, MAX_RESULTS);
  }, [options, query]);

  const recentOptions = useMemo(() => {
    if (query.trim()) return [];
    const seen = new Set<string>();
    const out: NodeOption[] = [];
    for (const id of recents) {
      if (seen.has(id)) continue;
      const opt = options.find((o) => o.id === id);
      if (opt) {
        out.push(opt);
        seen.add(id);
      }
      if (out.length >= MAX_RECENT) break;
    }
    return out;
  }, [recents, options, query]);

  const inputValue = open || query ? query : (selected?.name ?? "");

  function choose(option: NodeOption): void {
    onChange(option.id);
    setOpen(false);
    setQuery("");
    setHighlight(-1);
  }

  function clear(): void {
    onChange(null);
    setOpen(false);
    setQuery("");
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>): void {
    if (disabled) return;
    const pool = filtered;
    const count = Math.max(pool.length, 1);
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
      if (open && pool[highlight]) choose(pool[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setHighlight(-1);
    }
  }

  return (
    <div className={styles.wrap}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <div className={styles.inputRow}>
        <input
          id={inputId}
          className={styles.input}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-autocomplete="list"
          aria-controls={listId}
          aria-activedescendant={
            open && filtered[highlight] ? `node-option-${filtered[highlight].id}` : undefined
          }
          value={inputValue}
          placeholder="Choose a location…"
          autoComplete="off"
          disabled={disabled}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
            setHighlight(-1);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
        />
        {selected ? (
          <button
            type="button"
            className={styles.clear}
            aria-label={`Clear ${label}`}
            onMouseDown={(e) => e.preventDefault()}
            onClick={clear}
          >
            ×
          </button>
        ) : null}
      </div>
      {open ? (
        <div className={styles.menu}>
          {recentOptions.length > 0 ? (
            <div className={styles.recentGroup}>
              <span className={styles.recentLabel}>Recent</span>
              <ul className={styles.recentList} aria-label={`${label} recent selections`}>
                {recentOptions.map((option) => (
                  <li key={`recent-${option.id}`}>
                    <button
                      type="button"
                      className={styles.recentItem}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        choose(option);
                      }}
                    >
                      {option.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <ul id={listId} className={styles.list} role="listbox" aria-label={label}>
            {filtered.length === 0 ? (
              <li className={styles.empty} role="status">
                No matching locations.
              </li>
            ) : (
              filtered.map((option, i) => (
                <li
                  key={option.id}
                  id={`node-option-${option.id}`}
                  role="option"
                  aria-selected={option.id === value}
                  className={`${styles.item}${i === highlight ? ` ${styles.highlight}` : ""}`}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    choose(option);
                  }}
                  onMouseEnter={() => setHighlight(i)}
                >
                  <span className={styles.itemPrimary}>{option.name}</span>
                  {option.keywords ? (
                    <span className={styles.itemSecondary}>{option.keywords}</span>
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
