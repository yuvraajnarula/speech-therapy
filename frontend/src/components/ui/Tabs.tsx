import React from "react";

export interface TabItem {
  id: string;
  label: string;
  icon?: string;
  badge?: string;
}

interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ items, activeId, onChange }) => {
  return (
    <div
      role="tablist"
      style={{
        display: "inline-flex",
        backgroundColor: "#f1f5f9",
        padding: "3px",
        borderRadius: "8px",
        border: "1px solid #e2e8f0",
      }}
    >
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.45rem 1rem",
              fontSize: "0.85rem",
              fontWeight: isActive ? 600 : 500,
              color: isActive ? "#0f172a" : "#64748b",
              backgroundColor: isActive ? "#ffffff" : "transparent",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              boxShadow: isActive ? "0 1px 2px rgba(0,0,0,0.06)" : "none",
              transition: "all 0.15s ease",
            }}
          >
            {tab.icon && <span>{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge && (
              <span
                style={{
                  fontSize: "0.7rem",
                  padding: "0.1rem 0.4rem",
                  borderRadius: "9999px",
                  backgroundColor: isActive ? "#eff6ff" : "#e2e8f0",
                  color: isActive ? "#2563eb" : "#475569",
                  fontWeight: 600,
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
