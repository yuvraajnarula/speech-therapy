import type { HTMLAttributes } from "react";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "success" | "warning" | "destructive" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  style,
  ...props
}) => {
  const getStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      display: "inline-flex",
      alignItems: "center",
      borderRadius: "9999px",
      padding: "0.2rem 0.65rem",
      fontSize: "0.75rem",
      fontWeight: 500,
      lineHeight: 1,
      transition: "all 0.15s ease",
      letterSpacing: "0.02em",
      fontFamily: "var(--font-mono)",
    };

    switch (variant) {
      case "success":
        return {
          ...base,
          backgroundColor: "var(--success-bg)",
          color: "var(--success-text)",
          border: "1px solid var(--success-border)",
        };
      case "warning":
        return {
          ...base,
          backgroundColor: "var(--warn-bg)",
          color: "var(--warn-text)",
          border: "1px solid var(--warn-border)",
        };
      case "destructive":
        return {
          ...base,
          backgroundColor: "var(--danger-bg)",
          color: "var(--danger-text)",
          border: "1px solid var(--danger-border)",
        };
      case "secondary":
        return {
          ...base,
          backgroundColor: "var(--surface-overlay)",
          color: "var(--text-secondary)",
          border: "1px solid var(--border-subdued)",
        };
      case "outline":
        return {
          ...base,
          backgroundColor: "transparent",
          color: "var(--text-secondary)",
          border: "1px solid var(--border-standard)",
        };
      case "default":
      default:
        return {
          ...base,
          backgroundColor: "var(--bg-elevated)",
          color: "var(--text-secondary)",
          border: "1px solid var(--border-standard)",
        };
    }
  };

  return (
    <span style={{ ...getStyles(), ...style }} {...props}>
      {children}
    </span>
  );
};
