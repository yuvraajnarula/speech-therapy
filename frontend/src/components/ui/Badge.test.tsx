import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("applies default variant styles", () => {
    const { container } = render(<Badge>Default</Badge>);
    const badge = container.querySelector("span")!;
    expect(badge.getAttribute("style")).toContain("var(--bg-elevated)");
  });

  it("applies success variant styles", () => {
    const { container } = render(<Badge variant="success">Success</Badge>);
    const badge = container.querySelector("span")!;
    expect(badge.getAttribute("style")).toContain("var(--success-bg)");
  });

  it("applies warning variant styles", () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    const badge = container.querySelector("span")!;
    expect(badge.getAttribute("style")).toContain("var(--warn-bg)");
  });

  it("applies destructive variant styles", () => {
    const { container } = render(<Badge variant="destructive">Error</Badge>);
    const badge = container.querySelector("span")!;
    expect(badge.getAttribute("style")).toContain("var(--danger-bg)");
  });
});
