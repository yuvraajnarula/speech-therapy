import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
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
      borderRadius: "6px",
      fontSize: "0.875rem",
      fontWeight: 500,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      transition: "background-color 0.15s, border-color 0.15s",
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
        return { ...base, backgroundColor: "#f1f5f9", color: "#0f172a", border: "1px solid #e2e8f0" };
      case "outline":
        return { ...base, backgroundColor: "transparent", color: "#334155", border: "1px solid #cbd5e1" };
      case "destructive":
        return { ...base, backgroundColor: "#ef4444", color: "#ffffff" };
      case "ghost":
        return { ...base, backgroundColor: "transparent", color: "#475569" };
      case "link":
        return { ...base, backgroundColor: "transparent", color: "#2563eb", textDecoration: "underline" };
      case "default":
      default:
        return { ...base, backgroundColor: "#0f172a", color: "#ffffff" };
    }
  };

  return (
    <button style={{ ...getStyles(), ...style }} disabled={disabled} {...props}>
      {children}
    </button>
  );
};
