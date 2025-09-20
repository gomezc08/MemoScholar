export type PanelKind = "youtube" | "paper" | "model";

export interface Item {
  id: string;
  title: string;
  meta: {
    channel?: string;
    duration?: string;
    views?: string;
    likes?: string;
    video_url?: string;
    venue?: string;
    year?: number;
    framework?: string;
    vram?: string;
    authors?: string;
    link?: string;
    pdf_link?: string;
    summary?: string;
  };
  feedback?: "accept" | "reject";
}
