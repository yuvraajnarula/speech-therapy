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
        backgroundColor: "var(--surface-overlay)",
        padding: "3px",
        borderRadius: "var(--radius-control, 8px)",
        border: "1px solid var(--border-standard)",
        boxShadow: "var(--shadow-paper)",
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
              color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
              backgroundColor: isActive ? "var(--bg-elevated)" : "transparent",
              border: isActive ? "1px solid var(--border-strong)" : "1px solid transparent",
              borderRadius: "6px",
              cursor: "pointer",
              boxShadow: isActive ? "var(--shadow-paper)" : "none",
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
                  fontFamily: "var(--font-mono)",
                  backgroundColor: isActive ? "var(--border-strong)" : "var(--surface-overlay)",
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: 600,
                  border: "1px solid var(--border-standard)",
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
