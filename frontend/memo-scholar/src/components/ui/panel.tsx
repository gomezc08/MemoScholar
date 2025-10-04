import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, X, RotateCcw, Youtube, FileText, Cpu } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { mockItems } from "@/lib/mock";
import type { Item, PanelKind } from "@/types";
import { acceptOrReject, updateLikeStatus } from "@/lib/api";
import { generateSubmissionIndividualPanel } from "@/lib/api";
import { formatNumber, formatDuration } from "@/lib/dataTransformers";

export function Panel({ 
  kind, 
  topic = "", 
  objective = "", 
  guidelines = "",
  items: externalItems,
  onItemFeedback,
  user
}: { 
  kind: PanelKind; 
  topic?: string; 
  objective?: string; 
  guidelines?: string;
  items?: Item[];
  onItemFeedback?: (item: Item, feedback: 'accept' | 'reject') => void;
  user?: { user_id?: number } | null;
}) {
  const [instructions, setInstructions] = useState("");
  const [items, setItems] = useState<Item[]>(() => externalItems || (kind === "model" ? mockItems(kind) : []));
  const [isRegenerating, setIsRegenerating] = useState(false);

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
    if (!user?.user_id) {
      alert('Please sign in to generate content');
      return;
    }
    
    setIsRegenerating(true);
    try{
      console.log("Calling generateSubmissionIndividualPanel on the following data:", { panel_name: label, topic: topic, objective: objective, guidelines: guidelines, user_special_instructions: instructions, user_id: user.user_id });
      const result = await generateSubmissionIndividualPanel(topic, objective, guidelines, instructions, label, user.user_id);
      console.log("Submission generated:", result);
      console.log("YouTube array:", result.youtube);
      console.log("Papers array:", result.papers); 
      
      // Handle the API response format - backend returns different arrays based on panel type
      if (result.success) {
        if (result.youtube && Array.isArray(result.youtube)) {
          // Convert YouTube videos to panel items with numeric IDs
          const youtubeItems = result.youtube.map((video: any, index: number) => ({
            id: Date.now() + index, // Generate unique numeric ID
            title: video.video_title,
            meta: {
              channel: "YouTube", // We could extract channel from video data if needed
              duration: video.video_duration,
              views: parseInt(video.video_views) || 0, // Convert to number
              likes: parseInt(video.video_likes) || 0, // Convert to number
              video_url: video.video_url
            },
            feedback: undefined as "accept" | "reject" | undefined
          }));
          
          console.log("Created YouTube items:", youtubeItems);
          setItems(youtubeItems);
        } else if (result.papers && Array.isArray(result.papers)) {
          // Convert papers to panel items with numeric IDs
          const paperItems = result.papers.map((paper: any, index: number) => ({
            id: Date.now() + index + 1000, // Generate unique numeric ID (offset to avoid conflicts)
            title: paper.title,
            meta: {
              venue: "ArXiv", // ArXiv is the source
              year: new Date(paper.published).getFullYear(),
              authors: paper.authors ? paper.authors.join(', ') : 'Unknown',
              link: paper.link,
              pdf_link: paper.pdf_link,
              summary: paper.summary
            },
            feedback: undefined as "accept" | "reject" | undefined
          }));
          
          console.log("Created paper items:", paperItems);
          setItems(paperItems);
        }
      }
    } 
    catch (e) {
      console.error("Error generating submission:", e); 
    } finally {
      setIsRegenerating(false);
    }
  }

  const acceptOrRejectPanelItem = async (id: number, label: "accept" | "reject") => {
    const item = items.find(it => it.id === id);
    if (!item) return;

    // Check if we have the required database information
    if (!item.database_id || !item.target_type || !item.project_id) {
      console.error("Missing database information for item:", item);
      console.error("Available properties:", Object.keys(item));
      alert("This item is missing database information. Please regenerate the content to fix this issue.");
      return;
    }

    // Update UI state immediately for visual feedback
    setItems(prev => prev.map(it => it.id === id ? { ...it, feedback: label } : it));
    
    try{
      // Check if this item already has a like record (for updates)
      if (item.liked_disliked_id) {
        // Update existing like/dislike record
        const payload = {
          liked_disliked_id: item.liked_disliked_id
        };
        
        console.log("Calling updateLikeStatus API with payload:", payload);
        const result = await updateLikeStatus(payload);
        console.log("Like updated:", result);
        
        // Update the item with the new like ID if returned
        if (result.liked_disliked_id) {
          setItems(prev => prev.map(it => 
            it.id === id ? { ...it, liked_disliked_id: result.liked_disliked_id } : it
          ));
        }
      } else {
        // Create new like/dislike record
        const payload = {
          project_id: item.project_id,
          target_type: item.target_type,
          target_id: item.database_id,
          isLiked: label === "accept"
        };
        
        console.log("Calling acceptOrReject API with payload:", payload);
        const result = await acceptOrReject(payload);
        console.log("Submission accepted or rejected:", result);
        
        // Update the item with the new like ID
        if (result.like_id) {
          const updatedItem = { ...item, liked_disliked_id: result.like_id, feedback: label };
          setItems(prev => prev.map(it => 
            it.id === id ? updatedItem : it
          ));
          
          // Call the parent callback with the updated item (now has liked_disliked_id)
          if (onItemFeedback) {
            onItemFeedback(updatedItem, label);
          }
        }
      }
      
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
    <Card className="relative bg-zinc-900/60 p-10 shadow-xl shadow-black border-zinc-800/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg text-white">
            {icon}
            {label}
          </CardTitle>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={regenerate} 
            disabled={isRegenerating || !user?.user_id}
            className={isRegenerating ? "bg-pink-500 hover:bg-pink-600 border-pink-500" : ""}
          >
            <RotateCcw className={`h-4 w-4 mr-1 ${isRegenerating ? 'animate-spin' : ''}`} /> 
            {isRegenerating ? 'Generating...' : !user?.user_id ? 'Sign in to generate' : 'Regenerate'}
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
            <div className="text-center text-zinc-400 py-8">
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
                    <div className="font-medium leading-tight cursor-pointer hover:underline text-blue-400 hover:text-blue-300">{it.title}</div>
                    <div className="text-xs text-zinc-400">
                      <span>{it.meta.channel} • {formatDuration(it.meta.duration || null)} • {formatNumber(it.meta.views || 0)} views • {formatNumber(it.meta.likes || 0)} likes</span>
                    </div>
                  </a>
                ) : kind === "paper" && it.meta.link ? (
                  <a 
                    href={it.meta.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block hover:opacity-80 transition-opacity"
                  >
                    <div className="font-medium leading-tight cursor-pointer hover:underline text-blue-400 hover:text-blue-300">{it.title}</div>
                    <div className="text-xs text-zinc-400">
                      <span>{it.meta.venue} • {it.meta.year} • {it.meta.authors}</span>
                    </div>
                    {it.meta.summary && (
                      <div className="text-xs text-zinc-400 mt-1 line-clamp-2">
                        {it.meta.summary}
                      </div>
                    )}
                  </a>
                ) : (
                  <div>
                    <div className="font-medium leading-tight text-white">{it.title}</div>
                    <div className="text-xs text-zinc-400">
                      {kind === "paper" && <span>{it.meta.venue} • {it.meta.year}</span>}
                      {kind === "model" && <span>{it.meta.framework} • min VRAM {it.meta.vram}</span>}
                    </div>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button size="icon" variant="ghost" onClick={() => acceptOrRejectPanelItem(it.id, "reject")} aria-label="Reject" className="h-12 w-12 text-red-500 hover:bg-zinc-700 hover:text-red-400 rounded-full">
                  <X className="h-10 w-10" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => acceptOrRejectPanelItem(it.id, "accept")} aria-label="Accept" className="h-12 w-12 text-green-500 hover:bg-zinc-700 hover:text-green-400 rounded-full">
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
