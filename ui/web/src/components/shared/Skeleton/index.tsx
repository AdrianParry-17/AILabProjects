import styles from "./index.module.css";

interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
}

/** Shimmer placeholder (COMPONENT_POLISH_SPEC §22); fixed dimensions, no layout shift. */
export function Skeleton({ width, height, className }: SkeletonProps): JSX.Element {
  return (
    <span
      className={[styles.skeleton, className].filter(Boolean).join(" ")}
      style={width || height ? { width, height } : undefined}
      aria-hidden="true"
    />
  );
}