import type { ButtonHTMLAttributes } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "default",
  size = "default",
  style,
  disabled,
  ...props
}) => {
  const getStyles = (): React.CSSProperties => {
    let base: React.CSSProperties = {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      borderRadius: "var(--radius-control, 8px)",
      fontSize: "0.875rem",
      fontWeight: 500,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      transition: "background-color 0.15s, border-color 0.12s, transform 0.05s",
      textDecoration: "none",
      border: "1px solid transparent",
    };

    // Size
    switch (size) {
      case "sm":
        base = { ...base, padding: "0.35rem 0.65rem", fontSize: "0.8rem" };
        break;
      case "lg":
        base = { ...base, padding: "0.65rem 1.25rem", fontSize: "1rem" };
        break;
      case "icon":
        base = { ...base, padding: "0.45rem", width: "2rem", height: "2rem" };
        break;
      case "default":
      default:
        base = { ...base, padding: "0.5rem 0.95rem" };
        break;
    }

    // Variant
    switch (variant) {
      case "secondary":
        return {
          ...base,
          backgroundColor: "var(--surface-overlay)",
          color: "var(--text-primary)",
          border: "1px solid var(--border-standard)",
          boxShadow: "var(--shadow-paper)",
        };
      case "outline":
        return {
          ...base,
          backgroundColor: "transparent",
          color: "var(--text-primary)",
          border: "1px solid var(--border-strong)",
        };
      case "destructive":
        return {
          ...base,
          backgroundColor: "var(--danger-bg)",
          color: "var(--danger-text)",
          border: "1px solid var(--danger-border)",
        };
      case "ghost":
        return {
          ...base,
          backgroundColor: "transparent",
          color: "var(--text-secondary)",
        };
      case "link":
        return {
          ...base,
          backgroundColor: "transparent",
          color: "var(--accent-primary)",
          textDecoration: "underline",
        };
      case "default":
      default:
        return {
          ...base,
          backgroundColor: "var(--accent-primary)",
          color: "#F9F6F0",
          border: "1px solid var(--accent-primary)",
          boxShadow: "var(--shadow-paper)",
        };
    }
  };

  return (
    <button style={{ ...getStyles(), ...style }} disabled={disabled} {...props}>
      {children}
    </button>
  );
};
