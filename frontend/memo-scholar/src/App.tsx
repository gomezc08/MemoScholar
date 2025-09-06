import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, X, Play, RotateCcw, Download, Youtube, FileText, Cpu, Sun, Moon, Save } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";

// ---- Types ----
interface Item {
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

// ---- Mock helpers ----
const mockItems = (kind: "youtube" | "paper" | "model"): Item[] =>
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

function Panel({ kind, accent }: { kind: "youtube" | "paper" | "model"; accent: string }) {
  const [instructions, setInstructions] = useState("");
  const [items, setItems] = useState(() => mockItems(kind));

  const icon = kind === "youtube" ? <Youtube className="h-4 w-4" /> : kind === "paper" ? <FileText className="h-4 w-4" /> : <Cpu className="h-4 w-4" />;
  const label = kind === "youtube" ? "YouTube" : kind === "paper" ? "Papers" : "Models";

  function regenerate() {
    setItems(prev => [...prev].sort(() => Math.random() - 0.5));
  }

  async function handleFeedback(id: string, label: "accept" | "reject") {
    // Animate and remove after delay
    setItems(prev => prev.map(it => it.id === id ? { ...it, feedback: label } : it));
    try {
      await fetch(`/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, kind, label }),
      });
      console.log(`${label === "accept" ? "accepted" : "rejected"} ${id}`);
    } catch (err) {
      console.error("Feedback failed", err);
    }
    setTimeout(() => {
      setItems(prev => prev.filter(it => it.id !== id));
    }, 800);
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
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={regenerate}>
              <RotateCcw className="h-4 w-4 mr-1" /> Regenerate
            </Button>
            <Button size="sm">
              <Play className="h-4 w-4 mr-1" /> Run
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea
          value={instructions}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInstructions(e.target.value)}
          placeholder={`Per-panel instructions (e.g., ${
            kind === "youtube"
              ? "no videos > 20 min, prefer NeurIPS/ICLR channels"
              : kind === "paper"
              ? "only 2024-2025, prefer surveys and CVPR/NeurIPS"
              : "license: apache-2.0, VRAM ≤ 12GB, Transformers"
          })`}
          className="min-h-[72px]"
        />
        <Separator />
        <div className="grid grid-cols-1 gap-3">
          {items.map((it) => (
            <motion.div
              key={it.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0, backgroundColor: it.feedback === "accept" ? "#bbf7d0" : it.feedback === "reject" ? "#fecaca" : undefined }}
              exit={{ opacity: 0 }}
              className="flex items-start justify-between rounded-xl border p-3 transition-colors"
            >
              <div className="space-y-1">
                <div className="font-medium leading-tight">{it.title}</div>
                <div className="text-xs text-muted-foreground">
                  {kind === "youtube" && (
                    <span>{it.meta.channel} • {it.meta.duration}</span>
                  )}
                  {kind === "paper" && (
                    <span>{it.meta.venue} • {it.meta.year}</span>
                  )}
                  {kind === "model" && (
                    <span>{it.meta.framework} • min VRAM {it.meta.vram}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="icon" variant="ghost" onClick={() => handleFeedback(it.id, "reject")} aria-label="Reject">
                  <X className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => handleFeedback(it.id, "accept")} aria-label="Accept">
                  <Check className="h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function App() {
  const [topic, setTopic] = useState("");
  const [objective, setObjective] = useState("");
  const [constraints, setConstraints] = useState("");
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (isDark) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [isDark]);

  const onSavePDF = () => {
    window.print();
  };

  const onSaveProject = async () => {
    const payload = { topic, objective, constraints };
    try {
      await fetch("/api/project/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      console.log("Project saved", payload);
    } catch (err) {
      console.error("Save failed", err);
    }
  };

  return (
    <div className={`min-h-screen ${isDark ? "dark bg-gray-900 text-white" : "bg-background text-foreground"}`}>
      {/* Header */}
      <header className="sticky top-0 z-20 bg-background/80 backdrop-blur border-b">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <div className="grid grid-cols-3 items-center">
            <div />
            <h1 className="text-center text-2xl sm:text-3xl font-semibold tracking-tight">MemoScholar</h1>
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="ghost"
                size="icon"
                aria-label="Toggle theme"
                onClick={() => setIsDark(d => !d)}
                title={isDark ? "Switch to light" : "Switch to dark"}
              >
                {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
              <Button
                size="sm"
                className="bg-black text-white hover:bg-black/90"
                onClick={onSaveProject}
              >
                <Save className="h-4 w-4 mr-2" /> Save Project
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-6xl px-4 py-6 space-y-6">
        <Card className="shadow-sm">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="text-lg">Project Details</CardTitle>
            <Button onClick={onSaveProject} variant="default">
              <Save className="h-4 w-4 mr-1" /> Save Project
            </Button>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Topic</label>
              <Input value={topic} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTopic(e.target.value)} placeholder="e.g., Graph Neural Networks for Recommendation" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Primary Objective</label>
              <Input value={objective} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setObjective(e.target.value)} placeholder="e.g., build a GNN-based re-ranker" />
            </div>
            <div className="sm:col-span-2 space-y-2">
              <label className="text-sm font-medium">Constraints / Notes</label>
              <Textarea value={constraints} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setConstraints(e.target.value)} placeholder="e.g., prefer 2024–2025 content; no videos > 20 min; CVPR/NeurIPS venues; Apache-2.0 models" />
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Panel kind="youtube" accent="muted" />
          <Panel kind="paper" accent="muted" />
          <Panel kind="model" accent="muted" />
        </div>
      </main>

      <Button onClick={onSavePDF} className="fixed bottom-5 right-5 shadow-lg" size="lg">
        <Download className="h-4 w-4 mr-2" /> Save as PDF
      </Button>
    </div>
  );
}
