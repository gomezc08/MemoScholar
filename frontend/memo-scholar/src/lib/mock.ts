import type { Item, PanelKind } from "@/types";

export const mockItems = (kind: PanelKind): Item[] =>
  Array.from({ length: 4 }).map((_, i) => ({
    id: `${kind}_${i + 1}`,
    title:
      kind === "youtube"
        ? `YouTube Talk ${i + 1}`
        : kind === "paper"
        ? `Paper Title ${i + 1}`
        : `Model Option ${i + 1}`,
    meta:
      kind === "youtube"
        ? { channel: "Conf Channel", duration: `${10 + i * 3} min` }
        : kind === "paper"
        ? { venue: "arXiv 2025", year: 2025 }
        : { framework: i % 2 ? "Transformers" : "llama.cpp", vram: `${8 + i * 2} GB` },
  }));