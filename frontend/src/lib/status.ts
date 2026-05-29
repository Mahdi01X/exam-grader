import type { Tone } from "../components/ui";

type Meta = { label: string; tone: Tone };

export const examStatusMeta: Record<string, Meta> = {
  draft: { label: "Brouillon", tone: "neutral" },
  rubric_pending: { label: "Barème à valider", tone: "warn" },
  rubric_ready: { label: "Prêt à corriger", tone: "brand" },
  grading: { label: "Correction en cours", tone: "brand" },
  closed: { label: "Clôturé", tone: "ok" },
};

export const copyStatusMeta: Record<string, Meta> = {
  uploaded: { label: "Déposée", tone: "neutral" },
  extracted: { label: "Extraite", tone: "neutral" },
  graded: { label: "Notée", tone: "brand" },
  reviewed: { label: "Révisée", tone: "ok" },
  failed: { label: "Échec", tone: "danger" },
};

export function examStatus(s: string): Meta {
  return examStatusMeta[s] ?? { label: s, tone: "neutral" };
}

export function copyStatus(s: string): Meta {
  return copyStatusMeta[s] ?? { label: s, tone: "neutral" };
}
