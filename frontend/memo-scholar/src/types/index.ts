export type PanelKind = "youtube" | "paper" | "model";

export interface Item {
  id: string;
  title: string;
  meta: {
    channel?: string;
    duration?: string;
    venue?: string;
    year?: number;
    framework?: string;
    vram?: string;
  };
  feedback?: "accept" | "reject";
}
