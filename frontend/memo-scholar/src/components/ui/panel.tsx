import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, X, RotateCcw, Youtube, FileText, Cpu } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { mockItems } from "@/lib/mock";
import type { Item, PanelKind } from "@/types";
import { acceptOrReject } from "@/lib/api";
import { generateSubmissionIndividualPanel } from "@/lib/api";

export function Panel({ 
  kind, 
  accent = "muted", 
  topic = "", 
  objective = "", 
  guidelines = "",
  items: externalItems,
  onItemFeedback
}: { 
  kind: PanelKind; 
  accent?: string; 
  topic?: string; 
  objective?: string; 
  guidelines?: string;
  items?: Item[];
  onItemFeedback?: (item: Item, feedback: 'accept' | 'reject') => void;
}) {
  const [instructions, setInstructions] = useState("");
  const [items, setItems] = useState<Item[]>(() => externalItems || mockItems(kind));

  // Update items when externalItems change
  useEffect(() => {
    if (externalItems) {
      setItems(externalItems);
    }
  }, [externalItems]);

  const icon =
    kind === "youtube" ? <Youtube className="h-4 w-4" /> :
    kind === "paper"   ? <FileText className="h-4 w-4" /> :
                         <Cpu className="h-4 w-4" />;

  const label = kind === "youtube" ? "YouTube" : kind === "paper" ? "Papers" : "Models";

  const regenerate = async () => {
    try{
      console.log("Calling generateSubmissionIndividualPanel on the following data:", { panel_name: label, topic: topic, objective: objective, guidelines: guidelines, user_special_instructions: instructions });
      const result = await generateSubmissionIndividualPanel({ panel_name: label, topic: topic, objective: objective, guidelines: guidelines, user_special_instructions: instructions });
      console.log("Submission generated:", result); 
      
      // Update items with the API response
      if (result && result.items) {
        setItems(result.items);
      }
    } 
    catch (e) {
      console.error("Error generating submission:", e); 
    }
  }

  const acceptOrRejectPanelItem = async (id: string, label: "accept" | "reject") => {
    const item = items.find(it => it.id === id);
    if (!item) return;

    // Update UI state immediately for visual feedback
    setItems(prev => prev.map(it => it.id === id ? { ...it, feedback: label } : it));
    
    // Call the parent callback to manage liked/disliked items
    if (onItemFeedback) {
      onItemFeedback(item, label);
    }
    
    try{
      console.log("Calling acceptOrReject API on the following data:", { panel_name: label, panel_name_content_id: id });
      const result = await acceptOrReject({ panel_name: label, panel_name_content_id: id });
      console.log("Submission accepted or rejected:", result); 
      
      // Remove item after successful API call with delay for dissolve effect
      setTimeout(() => setItems(prev => prev.filter(it => it.id !== id)), 800);
    } 
    catch (e) {
      console.error("Error accepting or rejecting:", e);
      // Revert the feedback state on error
      setItems(prev => prev.map(it => it.id === id ? { ...it, feedback: undefined } : it));
    }
  }

  return (
    <Card className={`relative border-${accent}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            {icon}
            {label}
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
          {items.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No items yet. Click "Regenerate" to generate content for this panel.
            </div>
          ) : (
            items.map((it) => (
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
              <div className="space-y-1 flex-1">
                {kind === "youtube" && it.meta.video_url ? (
                  <a 
                    href={it.meta.video_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block hover:opacity-80 transition-opacity"
                  >
                    <div className="font-medium leading-tight cursor-pointer hover:underline">{it.title}</div>
                    <div className="text-xs text-muted-foreground">
                      <span>{it.meta.channel} • {it.meta.duration} • {it.meta.views} views • {it.meta.likes} likes</span>
                    </div>
                  </a>
                ) : (
                  <div>
                    <div className="font-medium leading-tight">{it.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {kind === "paper" && <span>{it.meta.venue} • {it.meta.year}</span>}
                      {kind === "model" && <span>{it.meta.framework} • min VRAM {it.meta.vram}</span>}
                    </div>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button size="icon" variant="ghost" onClick={() => acceptOrRejectPanelItem(it.id, "reject")} aria-label="Reject" className="h-12 w-12 text-red-500 hover:text-red-700">
                  <X className="h-10 w-10" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => acceptOrRejectPanelItem(it.id, "accept")} aria-label="Accept" className="h-12 w-12 text-green-500 hover:text-green-700">
                  <Check className="h-10 w-10" />
                </Button>
              </div>
            </motion.div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
