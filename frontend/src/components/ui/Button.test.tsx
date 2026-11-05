import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Button } from "./Button";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("applies default variant styles", () => {
    const { container } = render(<Button>Default</Button>);
    const button = container.querySelector("button")!;
    expect(button.getAttribute("style")).toContain("var(--accent-primary)");
  });

  it("applies destructive variant styles", () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    const button = container.querySelector("button")!;
    expect(button.getAttribute("style")).toContain("var(--danger-bg)");
  });

  it("applies secondary variant styles", () => {
    const { container } = render(<Button variant="secondary">Secondary</Button>);
    const button = container.querySelector("button")!;
    expect(button.getAttribute("style")).toContain("var(--border-standard)");
  });

  it("applies sm size styles", () => {
    const { container } = render(<Button size="sm">Small</Button>);
    const button = container.querySelector("button")!;
    expect(button).toHaveStyle("font-size: 0.8rem");
  });

  it("applies lg size styles", () => {
    const { container } = render(<Button size="lg">Large</Button>);
    const button = container.querySelector("button")!;
    expect(button).toHaveStyle("font-size: 1rem");
  });

  it("is disabled when disabled prop is set", () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole("button", { name: "Disabled" });
    expect(button).toBeDisabled();
  });

  it("passes onClick handler", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Clickable</Button>);
    const button = screen.getByRole("button", { name: "Clickable" });
    button.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
