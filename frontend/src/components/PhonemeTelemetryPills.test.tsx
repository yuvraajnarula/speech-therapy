import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { PhonemeTelemetryPills } from "./PhonemeTelemetryPills";

afterEach(() => cleanup());

describe("PhonemeTelemetryPills", () => {
  const correctDiagnostic = {
    type: "diagnostic",
    target: "namaste",
    spoken: "namaste",
    target_phonemes: "N AH M AH S T EY",
    spoken_phonemes: "N AH M AH S T EY",
    is_correct: true,
    target_achieved: true,
    accuracy_score: 100,
    errors: [],
    clinical_feedback: "Perfect pronunciation!",
  } as const;

  const substitutionDiagnostic = {
    type: "diagnostic",
    target: "cat",
    spoken: "bat",
    target_phonemes: "K AE T",
    spoken_phonemes: "B AE T",
    is_correct: false,
    target_achieved: false,
    accuracy_score: 67,
    errors: [
      { type: "replace", target_slice: "K", spoken_slice: "B" },
    ],
    clinical_feedback: "Substitution: Replaced sound /K/ with /B/.",
  } as const;

  it("returns null when no diagnostic", () => {
    const { container } = render(<PhonemeTelemetryPills diagnostic={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders diagnostic header and score", () => {
    render(<PhonemeTelemetryPills diagnostic={correctDiagnostic} />);
    expect(screen.getByText("Phonemic Alignment & SODA Matrix")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText("Articulation Score")).toBeInTheDocument();
  });

  it("renders target achieved pill when correct with no errors", () => {
    const { getByText } = render(<PhonemeTelemetryPills diagnostic={correctDiagnostic} />);
    expect(
      getByText("Target Achieved: All target phonemes accurately articulated")
    ).toBeInTheDocument();
  });

  it("renders substitution error pill", () => {
    const { getByText } = render(<PhonemeTelemetryPills diagnostic={substitutionDiagnostic} />);
    expect(getByText("Substitution (S)")).toBeInTheDocument();
    expect(screen.getByText("K")).toBeInTheDocument();
  });

  it("renders clinical feedback", () => {
    const { getByText } = render(<PhonemeTelemetryPills diagnostic={substitutionDiagnostic} />);
    expect(getByText("Substitution: Replaced sound /K/ with /B/.")).toBeInTheDocument();
  });

  it("renders Badge for phoneme target slice", () => {
    const { getByText } = render(<PhonemeTelemetryPills diagnostic={substitutionDiagnostic} />);
    expect(getByText("K")).toBeInTheDocument();
  });

  it("renders substitution score color", () => {
    const { container } = render(<PhonemeTelemetryPills diagnostic={substitutionDiagnostic} />);
    const scoreEl = container.querySelector('div[style*="font-size: 1.4rem"]');
    expect(scoreEl).toBeInTheDocument();
  });
});
