import { useId } from "react";

import styles from "./index.module.css";

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  invalid?: boolean;
  errorText?: string;
}

/** Text input (COMPONENT_POLISH_SPEC §18); accessible by default. */
export function TextInput({
  label,
  invalid = false,
  errorText,
  id,
  className,
  ...rest
}: TextInputProps): JSX.Element {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = errorText ? `${inputId}-error` : undefined;

  return (
    <div className={styles.wrap}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <input
        id={inputId}
        className={[styles.input, invalid ? styles.invalid : null, className].filter(Boolean).join(" ")}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        {...rest}
      />
      {errorText ? (
        <span id={describedBy} className={styles.error} role="alert">
          {errorText}
        </span>
      ) : null}
    </div>
  );
}