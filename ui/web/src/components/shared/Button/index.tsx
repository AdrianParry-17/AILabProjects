import styles from "./index.module.css";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "small" | "medium" | "large";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

/** Action button (COMPONENT_POLISH_SPEC §17); consumes only design tokens. */
export function Button({
  variant = "primary",
  size = "medium",
  loading = false,
  disabled,
  children,
  className,
  type = "button",
  ...rest
}: ButtonProps): JSX.Element {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      className={[styles.button, styles[variant], styles[size], className].filter(Boolean).join(" ")}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <span className={styles.spinner} aria-hidden="true" /> : null}
      <span className={styles.label}>{children}</span>
    </button>
  );
}