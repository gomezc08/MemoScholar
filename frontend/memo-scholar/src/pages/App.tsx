import { useState } from "react";
import { Download, Save } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Panel } from "@/components/ui/panel";
import { HeaderBar } from "@/components/ui/header_bar";
import { useTheme } from "@/hooks/useTheme";
import { saveProject } from "@/lib/api";

export default function App() {
  const [topic, setTopic] = useState("");
  const [objective, setObjective] = useState("");
  const [constraints, setConstraints] = useState("");
  const { isDark, toggle } = useTheme();

  const onSavePDF = () => window.print();
  const onRun = async () => {
    try { await saveProject({ topic, objective, constraints }); console.log("Project saved"); }
    catch (e) { console.error(e); }
  };

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? "dark bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <HeaderBar isDark={isDark} onToggle={toggle} />

      <main className="flex-1 w-full px-4 py-6 space-y-6">
        <Card className="shadow-sm">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="text-lg">Project Details</CardTitle>
            <Button onClick={onRun} variant="default">
              <Save className="h-4 w-4 mr-1" /> Run
            </Button>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Topic</label>
              <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g., Graph Neural Networks for Recommendation" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Primary Objective</label>
              <Input value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="e.g., build a GNN-based re-ranker" />
            </div>
            <div className="sm:col-span-2 space-y-2">
              <label className="text-sm font-medium">Constraints / Notes</label>
              <Textarea value={constraints} onChange={(e) => setConstraints(e.target.value)} placeholder="e.g., prefer 2024–2025 content; no videos > 20 min; CVPR/NeurIPS venues; Apache-2.0 models" />
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-col min-[600px]:flex-row gap-4">
          <div className="flex-1"><Panel kind="youtube" accent="muted" /></div>
          <div className="flex-1"><Panel kind="paper" accent="muted" /></div>
          <div className="flex-1"><Panel kind="model" accent="muted" /></div>
        </div>
      </main>

      <Button onClick={onSavePDF} className="fixed bottom-5 right-5 shadow-lg" size="lg">
        <Download className="h-4 w-4 mr-2" /> Save as PDF
      </Button>
    </div>
  );
}
