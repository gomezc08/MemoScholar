import { useState } from "react";
import { motion } from "framer-motion";
import { Check, X, RotateCcw, Youtube, FileText, Cpu } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { mockItems } from "@/lib/mock";
import { postFeedback } from "@/lib/api";
import type { Item, PanelKind } from "@/types";

export function Panel({ kind, accent = "muted" }: { kind: PanelKind; accent?: string }) {
  const [instructions, setInstructions] = useState("");
  const [items, setItems] = useState<Item[]>(() => mockItems(kind));

  const icon =
    kind === "youtube" ? <Youtube className="h-4 w-4" /> :
    kind === "paper"   ? <FileText className="h-4 w-4" /> :
                         <Cpu className="h-4 w-4" />;

  const label = kind === "youtube" ? "YouTube" : kind === "paper" ? "Papers" : "Models";

  function regenerate() {
    setItems(prev => [...prev].sort(() => Math.random() - 0.5));
  }

  async function handleFeedback(id: string, label: "accept" | "reject") {
    setItems(prev => prev.map(it => it.id === id ? { ...it, feedback: label } : it));
    try {
      await postFeedback({ id, kind, label });
      console.log(`${label === "accept" ? "accepted" : "rejected"} ${id}`);
    } catch (err) {
      console.error(err);
    }
    setTimeout(() => setItems(prev => prev.filter(it => it.id !== id)), 800);
  }

  return (
    <Card className={`relative border-${accent}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            {icon}
            {label}
            <Badge variant="secondary" className="ml-2">Panel</Badge>
          </CardTitle>
          <Button size="sm" variant="outline" onClick={regenerate}>
            <RotateCcw className="h-4 w-4 mr-1" /> Regenerate
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder={`Per-panel instructions...`}
          className="min-h-[72px]"
        />
        <Separator />
        <div className="grid grid-cols-1 gap-3">
          {items.map((it) => (
            <motion.div
              key={it.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{
                opacity: 1,
                y: 0,
                backgroundColor:
                  it.feedback === "accept" ? "#bbf7d0" :
                  it.feedback === "reject" ? "#fecaca" : undefined,
              }}
              exit={{ opacity: 0 }}
              className="flex items-start justify-between rounded-xl border p-3 transition-colors"
            >
              <div className="space-y-1">
                <div className="font-medium leading-tight">{it.title}</div>
                <div className="text-xs text-muted-foreground">
                  {kind === "youtube" && <span>{it.meta.channel} • {it.meta.duration}</span>}
                  {kind === "paper" && <span>{it.meta.venue} • {it.meta.year}</span>}
                  {kind === "model" && <span>{it.meta.framework} • min VRAM {it.meta.vram}</span>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="icon" variant="ghost" onClick={() => handleFeedback(it.id, "reject")} aria-label="Reject" className="h-12 w-12 text-red-500 hover:text-red-700">
                  <X className="h-10 w-10" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => handleFeedback(it.id, "accept")} aria-label="Accept" className="h-12 w-12 text-green-500 hover:text-green-700">
                  <Check className="h-10 w-10" />
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
