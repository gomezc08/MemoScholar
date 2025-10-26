import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  onItemsUpdate,
  user,
  project_id,
  query_id
}: { 
  kind: PanelKind; 
  topic?: string; 
  objective?: string; 
  guidelines?: string;
  items?: Item[];
  onItemFeedback?: (item: Item, feedback: 'accept' | 'reject') => void;
  onItemsUpdate?: (items: Item[]) => void;
  user?: { user_id?: number } | null;
  project_id?: number;
  query_id?: number;
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
    
    if (!project_id || !query_id) {
      alert('Project ID and Query ID are required for individual panel generation');
      return;
    }
    
    setIsRegenerating(true);
    try{
      console.log("Calling generateSubmissionIndividualPanel on the following data:", { panel_name: label, topic: topic, objective: objective, guidelines: guidelines, user_special_instructions: instructions, user_id: user.user_id, project_id, query_id });
      const result = await generateSubmissionIndividualPanel(topic, objective, guidelines, instructions, label, user.user_id, project_id, query_id);
      console.log("Submission generated:", result);
      console.log("YouTube array:", result.youtube);
      console.log("Papers array:", result.papers); 
      
      // Handle the API response format - backend returns different arrays based on panel type
      if (result.success) {
        if (label === "YouTube" && result.youtube && Array.isArray(result.youtube) && result.youtube.length > 0) {
          // Convert YouTube videos to panel items with numeric IDs
          const youtubeItems = result.youtube.map((video: any, index: number) => {
            return {
              id: Date.now() + index, // Generate unique numeric ID
              title: video.video_title,
              database_id: video.rec_id || video.youtube_id, // Handle both rec_id and youtube_id
              target_type: "youtube" as const,
              project_id: project_id,
              meta: {
                channel: "YouTube", // We could extract channel from video data if needed
                duration: video.video_duration,
                views: parseInt(video.video_views) || 0, // Convert to number
                likes: parseInt(video.video_likes) || 0, // Convert to number
                video_url: video.video_url,
                score: video.score,
                calculated_score: video.calculated_score,
                rank_position: video.rank_position
              },
              feedback: undefined as "accept" | "reject" | undefined
            };
          });
          setItems(youtubeItems);
          // Notify parent component about the new items
          if (onItemsUpdate) {
            onItemsUpdate(youtubeItems);
          }
        } else if (label === "Papers" && result.papers && Array.isArray(result.papers) && result.papers.length > 0) {
          // Convert papers to panel items with numeric IDs
          const paperItems = result.papers.map((paper: any, index: number) => ({
            id: Date.now() + index + 1000, // Generate unique numeric ID (offset to avoid conflicts)
            title: paper.title,
            database_id: paper.paper_id, // Add database ID for like/dislike functionality
            target_type: "paper" as const,
            project_id: project_id,
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
          // Notify parent component about the new items
          if (onItemsUpdate) {
            onItemsUpdate(paperItems);
          }
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
    if (!item) {
      console.error("Item not found with id:", id);
      return;
    }

    // Check if we have the required database information
    if (!item.database_id || !item.target_type || !item.project_id) {
      console.error("Missing database information for item:", item);
      console.error("Available properties:", Object.keys(item));
      alert("This item is missing database information. Please regenerate the content to fix this issue.");
      return;
    }

    // Update UI state immediately for visual feedback with fade effect
    setItems(prev => prev.map(it => it.id === id ? { ...it, feedback: label } : it));
    
    // Wait for the color animation to be visible before making API call
    setTimeout(async () => {
      try {
        let result;
        let updatedItem = { ...item, feedback: label };

        // Check if this item already has a like record (for updates)
        if (item.liked_disliked_id) {
          // Update existing like/dislike record
          const payload = {
            liked_disliked_id: item.liked_disliked_id
          };
          
          console.log("Calling updateLikeStatus API with payload:", payload);
          result = await updateLikeStatus(payload);
          console.log("Like updated:", result);
          
          // Check if update was successful
          if (!result.success) {
            throw new Error(result.error || "Failed to update like/dislike status");
          }
          
          // Update the item with the liked_disliked_id (should remain the same)
          updatedItem.liked_disliked_id = item.liked_disliked_id;
          
        } else {
          // Create new like/dislike record
          if (!item.project_id || !item.target_type || !item.database_id) {
            throw new Error("Missing required fields for creating like/dislike record");
          }
          
          const payload = {
            project_id: item.project_id,
            target_type: item.target_type,
            target_id: item.database_id,
            isLiked: label === "accept"
          };
          
          console.log("Calling acceptOrReject API with payload:", payload);
          result = await acceptOrReject(payload);
          console.log("Submission accepted or rejected:", result);
          
          // Check if creation was successful
          if (!result.success) {
            throw new Error(result.error || "Failed to create like/dislike record");
          }
          
          // Update the item with the new like ID
          if (result.like_id) {
            updatedItem.liked_disliked_id = result.like_id;
          } else {
            throw new Error("No like_id returned from server");
          }
        }
        
        // Update the item in state with all the correct information
        setItems(prev => prev.map(it => it.id === id ? updatedItem : it));
        
        // Call the parent callback with the updated item
        if (onItemFeedback) {
          onItemFeedback(updatedItem, label);
        }
        
        // Don't remove from local state - let the parent component handle filtering
        // The parent will filter out items that are in the alreadyProcessedKeys set
        // This ensures proper synchronization between panels and management panel
        
      } catch (error) {
        console.error("Error accepting or rejecting:", error);
        // Revert the feedback state on error
        setItems(prev => prev.map(it => 
          it.id === id ? { ...it, feedback: undefined } : it
        ));
        
        // Show user-friendly error message
        const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
        alert(`Failed to ${label} item: ${errorMessage}`);
      }
    }, 300); // Wait 300ms for color animation to be visible
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
            <AnimatePresence mode="popLayout">
              {items.map((it) => (
            <motion.div
              key={`panel-${kind}-${it.id}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{
                opacity: 1,
                backgroundColor:
                  it.feedback === "accept" ? "#10b981" : // Brighter Green
                  it.feedback === "reject" ? "#dc2626" : // Brighter Red
                  undefined,
              }}
              transition={{
                duration: it.feedback ? 0.3 : 0.3,
                ease: "easeInOut"
              }}
              exit={{ 
                opacity: 0,
                transition: { duration: 0.7, ease: "easeInOut" }
              }}
              className="flex items-start justify-between rounded-xl border p-3 transition-all duration-300"
            >
              <div className="space-y-1 flex-1">
                {kind === "youtube" && it.meta.video_url ? (
                  <a 
                    href={it.meta.video_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block hover:opacity-80 transition-opacity"
                  >
                    <div className="font-medium leading-tight cursor-pointer hover:underline text-blue-400 hover:text-blue-300 transition-colors">{it.title}</div>
                    <div className="text-xs text-zinc-400">
                      <span>{it.meta.channel} • {formatDuration(it.meta.duration || null)} • {formatNumber(it.meta.views || 0)} views • {formatNumber(it.meta.likes || 0)} likes</span>
                      {(it.meta.calculated_score !== undefined || it.meta.score !== undefined) && (
                        <div className="mt-1 text-xs text-white font-medium">
                          Score: {((it.meta.calculated_score || it.meta.score || 0) * 100).toFixed(2)}% • Rank: #{it.meta.rank_position || 'N/A'}
                        </div>
                      )}
                    </div>
                  </a>
                ) : kind === "paper" && it.meta.link ? (
                  <a 
                    href={it.meta.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block hover:opacity-80 transition-opacity"
                  >
                    <div className="font-medium leading-tight cursor-pointer hover:underline text-blue-400 hover:text-blue-300 transition-colors">{it.title}</div>
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
            ))}
            </AnimatePresence>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
