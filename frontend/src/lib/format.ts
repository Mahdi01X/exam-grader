export function formatPoints(value: number, max: number): string {
  return `${value.toFixed(2)} / ${max.toFixed(2)}`;
}

export function confidenceLabel(c: number): { label: string; color: string } {
  if (c >= 0.8) return { label: "Élevée", color: "text-ok" };
  if (c >= 0.6) return { label: "Moyenne", color: "text-warn" };
  return { label: "Basse", color: "text-danger" };
}
