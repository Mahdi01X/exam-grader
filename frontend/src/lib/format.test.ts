import { describe, expect, it } from "vitest";
import { confidenceLabel, formatPoints } from "./format";

describe("formatPoints", () => {
  it("formats two decimals", () => {
    expect(formatPoints(2.5, 4)).toBe("2.50 / 4.00");
  });
  it("rounds halves to even", () => {
    expect(formatPoints(0, 10)).toBe("0.00 / 10.00");
  });
});

describe("confidenceLabel", () => {
  it("high confidence is green", () => {
    expect(confidenceLabel(0.9).label).toBe("Élevée");
  });
  it("borderline mid", () => {
    expect(confidenceLabel(0.65).label).toBe("Moyenne");
  });
  it("low triggers danger", () => {
    expect(confidenceLabel(0.4).label).toBe("Basse");
  });
});
