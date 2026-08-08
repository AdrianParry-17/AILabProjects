import { useId, useMemo, useState } from "react";

import styles from "./index.module.css";

/** One selectable node option (id + display name). */
export interface NodeOption {
  id: string;
  name: string;
}

interface NodePickerProps {
  label: string;
  value: string | null;
  options: readonly NodeOption[];
  disabled?: boolean;
  onChange: (id: string | null) => void;
}

/**
 * NodePicker (§0.2 `NodeSelector` / D.10): an accessible combobox that filters
 * the node list by name or id and reports a selection (or a clear). Controlled —
 * the parent decides what happens via `onChange`.
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

  const selected = value ? options.find((o) => o.id === value) ?? null : null;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (o) => o.name.toLowerCase().includes(q) || o.id.toLowerCase().includes(q),
    );
  }, [options, query]);

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
      if (open && filtered[highlight]) choose(filtered[highlight]);
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
          placeholder="Choose a node…"
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
          <button type="button" className={styles.clear} aria-label={`Clear ${label}`} onMouseDown={(e) => e.preventDefault()} onClick={clear}>
            ×
          </button>
        ) : null}
      </div>
      {open && filtered.length > 0 ? (
        <ul id={listId} className={styles.menu} role="listbox" aria-label={label}>
          {filtered.map((option, i) => (
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
              {option.name}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}