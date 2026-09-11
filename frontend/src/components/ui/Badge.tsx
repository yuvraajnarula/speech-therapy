import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
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
      fontWeight: 600,
      lineHeight: 1,
      transition: "all 0.15s ease",
      letterSpacing: "0.02em",
    };

    switch (variant) {
      case "success":
        return { ...base, backgroundColor: "#ecfdf5", color: "#065f46", border: "1px solid #a7f3d0" };
      case "warning":
        return { ...base, backgroundColor: "#fffbeb", color: "#92400e", border: "1px solid #fde68a" };
      case "destructive":
        return { ...base, backgroundColor: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca" };
      case "secondary":
        return { ...base, backgroundColor: "#f1f5f9", color: "#334155", border: "1px solid #e2e8f0" };
      case "outline":
        return { ...base, backgroundColor: "transparent", color: "#475569", border: "1px solid #cbd5e1" };
      case "default":
      default:
        return { ...base, backgroundColor: "#0f172a", color: "#ffffff", border: "1px solid #0f172a" };
    }
  };

  return (
    <span style={{ ...getStyles(), ...style }} {...props}>
      {children}
    </span>
  );
};
